import asyncio
import backoff
import json
import os
import re
import base64

from openai import NotFoundError
from rich.progress import Progress, SpinnerColumn, TextColumn
from inspect import signature, Parameter

from src.ais.msg import get_text_content, user_msg
from src.utils.database import write_to_memory
from src.utils.files import find, get_file_hashmap
from src.utils.cli import red_text, green_text, yellow_text

from src.ais.functions.azure import (
    getCalendar,
    readEmail,
    writeEmail,
    sendEmail,
    createCalendarEvent,
    saveCalendarEvent,
    getContacts,
)
from src.ais.functions.misc import getWeather, getLocation, getDate
from src.ais.functions.office import findFile
from src.ais.functions.web import (
    webText,
    webMenus,
    webLinks,
    webImages,
    webTables,
    webForms,
    webQuery,
)


async def create(client, config):
    assistant = client.beta.assistants.create(
        name=config["name"],
        model=config["model"],
        tools=config["tools"],
    )

    return assistant


async def load_or_create_assistant(client, config, recreate: bool = False):
    asst_obj = await first_by_name(client, config["name"])

    asst_id = asst_obj.id if asst_obj is not None else None

    if recreate and asst_id is not None:
        await delete(client, asst_id)
        asst_id = None
        green_text(f"Assistant '{config['name']}' deleted")
        # print(f"Assistant '{config['name']}' deleted")

    if asst_id is not None:
        green_text(f"Assistant '{config['name']}' loaded")
        # print(f"Assistant '{config['name']}' loaded")
        return asst_id

    else:
        asst_obj = await create(client, config)
        green_text(f"Assistant '{config['name']}' created")
        # print(f"Assistant '{config['name']}' created")
        return asst_obj.id


async def first_by_name(client, name: str):
    assts = client.beta.assistants
    assistants = assts.list().data
    asst_obj = next((asst for asst in assistants if asst.name == name), None)
    return asst_obj


@backoff.on_exception(
    backoff.expo,
    NotFoundError,
    max_tries=5,
    giveup=lambda e: "No assistant found" not in str(e),
)
async def upload_instruction(client, config, asst_id: str, instructions: str):
    assts = client.beta.assistants
    try:
        assts.update(assistant_id=asst_id, instructions=instructions)
        # print(f"Instructions uploaded to assistant '{config['name']}'")
        green_text(f"Instructions uploaded to assistant '{config['name']}'")

    except Exception as e:
        red_text(f"Failed to upload instruction: {e}")
        # print(f"Failed to upload instruction: {e}")
        raise


async def delete(client, asst_id: str, wipe=True):
    assts = client.beta.assistants
    assistant_files = client.files

    file_hashmap = await get_file_hashmap(client, asst_id)

    for file_id in file_hashmap.values():
        del_res = assistant_files.delete(file_id)

        if del_res.deleted:
            green_text(f"File '{file_id}' deleted")
            # print(f"File '{file_id}' deleted")

    for key in file_hashmap.keys():
        path = find(key, "agent")
        if path:
            if os.path.exists(path):
                os.remove(path)

    try:
        if os.path.exists(find("memory.json", "agent")):
            os.remove(find("memory.json", "agent"))
    except:
        pass

    try:
        if wipe:
            if os.path.exists(find("memory.db", "agent")):
                os.remove(find("memory.db", "agent"))
    except:
        pass

    assts.delete(assistant_id=asst_id)
    # print(f"Assistant deleted")
    green_text("Assistant deleted")


async def create_thread(client):
    threads = client.beta.threads
    res = threads.create()
    return res.id


async def get_thread(client, thread_id: str):
    threads = client.beta.threads
    res = threads.retrieve(thread_id)
    return res


async def run_thread_message(client, asst_id: str, thread_id: str, message: str):

    msg = user_msg(message)

    threads = client.beta.threads

    pattern = r"run_[a-zA-Z0-9]+"

    try:
        _message_obj = threads.messages.create(
            thread_id=thread_id,
            content=message,
            role="user",
        )

        run = threads.runs.create(
            thread_id=thread_id,
            assistant_id=asst_id,
            additional_instructions=""" 
            ###Additional Instructions###

            ##Real-time Data Retrieval##
            URL-based Data Extraction: If a URL is provided by the user, employ web tools (`webText(url: str))`, `webMenus(url: str))`, `webLinks(url: str))`, `webImages(url: str))`, `webTables(url: str))`, `webForms(url: str))`) to extract specific data types as requested. For text extraction from a webpage, use the `webText(url: str))` tool.
            
            ###!!!IMPORTANT!!!###
            1. Use the `webQuery(query: str)` tool for queries requiring up-to-date information or data beyond the knowledge-cutoff.
            2. Use `findFile(filename: str)` to locate files for data analysis tasks before performing any analysis with `code_interpreter`
            3. **Use the raw text provided by the user to indicate `start` and `end` dates for calendar events.**

            ###Query-based Data Search###
            For inquiries requiring up-to-date information or data beyond the your knowledge-cutoff, use the `webQuery(query: str)` tool. Follow these steps:
                1. Understand the user's request to identify the specific information sought.
                2. Derive a focused query that accurately represents the user's need.
                3. Formulate this query concisely for submission to Wolfram Alpha via the webQuery function.
                4. Interpret and summarize the returned data to directly address the user's query.
                5. Present the findings clearly, ensuring relevance and accuracy.
                6. Revise the query and response based on user feedback if necessary.

            ##Email Composition and Sending##
                1. Preparatory Steps:
                    1. Utilize the `writeEmail(recipients: list(str), subject: str, body: str, attachments: Optional(list[str]))` function to draft emails, incorporating details such as recipients, subject, body, and optional attachments.
                    2. For recipient email addresses, use `getContacts(name: Optional(str))` when only a name is provided. Ensure clarity and accuracy in detailing the email's content.
                    3. Preview the drafted email to the user for confirmation or adjustments.

            ###Prerequisite Tool Usage###
                1. The `createCalendarEvent(subject: str, start: str, end: Optional(str), location: Optional(str), reccurence: Optional(boolean))` function must precede `saveCalendarEvent(subject: str, start: str, end: Optional(str), location: Optional(str), reccurence: Optional(boolean))` usage. Use `getDate()` optionally to determine the start date if not provided.
                2. The `writeEmail(recipients: list(str), subject: str, body: str, attachments: Optional(list[str]))` function is a precursor to `sendEmail(recipients: list(str), subject: str, body: str, attachments: Optional(list[str]))`. If an email address is unspecified, employ `getContacts(name: Optional(str))` to ascertain the recipient's email or seek clarification.
                3. The `findFile(filename: str)` function is essential before performing any data analysis tasks on files. This tool is activated when file context is mentioned by the user.

            ##User Interaction and Clarification##
                1. Directly interpret user queries to formulate appropriate tool commands, even if the user's request is indirect.
                2. Seek user confirmation before proceeding with actions that depend on prior tool usage or specific user input, ensuring accuracy and user satisfaction.
            """,
        )

    except Exception as e:
        match = re.search(pattern, str(e.message))

        if match:
            run_id = match.group()
            run = threads.runs.retrieve(thread_id=thread_id, run_id=run_id)

        else:

            raise e

    write_to_memory("User", message)

    with Progress(
        SpinnerColumn(), TextColumn("[bold cyan]{task.description}"), transient=True
    ) as progress:
        task = progress.add_task(
            "[green]Thinking...", total=None
        )  # Indeterminate progress

        while True:
            # print("-", end="", flush=True)
            run = threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

            if run.status in ["Completed", "completed"]:
                progress.stop()
                print()
                return await get_thread_message(client, thread_id)

            elif run.status in [
                "Queued",
                "InProgress",
                "run_in_progress",
                "in_progress",
                "queued",
                "pending",
                "Pending",
            ]:
                pass  # The spinner will continue spinning

            elif run.status in [
                "requires_input",
                "RequiresInput",
                "requires_action",
                "RequiresAction",
            ]:
                await call_required_function(
                    asst_id, client, thread_id, run.id, run.required_action
                )

            else:
                print()
                # await delete(client, asst_id)
                # print(f"Unexpected run status: {run.status}")
                red_text(f"Unexpected run status: {run.status}")
                raise

            await asyncio.sleep(0.2)


async def call_required_function(
    asst_id, client, thread_id: str, run_id: str, required_action
):
    tool_outputs = []

    # Function mapping
    function_map = {
        "getWeather": getWeather,
        "getCalendar": getCalendar,
        "readEmail": readEmail,
        "writeEmail": writeEmail,
        "sendEmail": sendEmail,
        "getLocation": getLocation,
        "getDate": getDate,
        "createCalendarEvent": createCalendarEvent,
        "saveCalendarEvent": saveCalendarEvent,
        "getContacts": getContacts,
        "findFile": findFile,
        "webText": webText,
        "webMenus": webMenus,
        "webLinks": webLinks,
        "webImages": webImages,
        "webTables": webTables,
        "webForms": webForms,
        "webQuery": webQuery,
    }

    def filter_args(func, provided_args):
        sig = signature(func)
        filtered_args = {}
        missing_args = []

        for name, param in sig.parameters.items():
            if param.default == Parameter.empty:  # This is a required parameter
                if name not in provided_args:
                    missing_args.append(name)
                else:
                    filtered_args[name] = provided_args[name]
            elif name in provided_args:  # Optional but provided
                filtered_args[name] = provided_args[name]

        if missing_args:
            red_text(
                f"Missing required arguments for {func.__name__}: {', '.join(missing_args)}"
            )

        return filtered_args

    for action in required_action:
        if not isinstance(action[1], str):
            func_name = action[1].tool_calls[0].function.name
            args = json.loads(action[1].tool_calls[0].function.arguments)

            if func_name in function_map:
                func = function_map[func_name]
                if func_name == "findFile":
                    filtered_args = filter_args(
                        func, {**args, "client": client, "asst_id": asst_id}
                    )
                else:
                    filtered_args = filter_args(func, args)

                if (
                    filtered_args is not None
                ):  # Check if args were successfully filtered
                    outputs = func(**filtered_args)

                    tool_outputs.append(
                        {"tool_call_id": action[1].tool_calls[0].id, "output": outputs}
                    )
            else:
                raise ValueError(f"Function '{func_name}' not found")

    # Encode bytes output to Base64 string if necessary
    for tool_output in tool_outputs:
        if isinstance(tool_output["output"], bytes):
            tool_output["output"] = (
                "[bytes]"
                + base64.b64encode(tool_output["output"]).decode("utf-8")
                + "[/bytes]"
            )

    # Assuming client.beta.threads.runs.submit_tool_outputs is correctly implemented
    client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread_id,
        run_id=run_id,
        tool_outputs=tool_outputs,
    )


async def get_thread_message(client, thread_id: str):
    threads = client.beta.threads

    try:
        messages = threads.messages.list(
            thread_id=thread_id,
            order="desc",
            extra_query={"limit": "1"},
        ).data

        msg = next(iter(messages), None)

        if msg is None:
            raise ValueError("No message found in thread")

        txt = get_text_content(client, msg)

        write_to_memory("Assistant", txt)

        return txt

    except Exception as e:
        raise ValueError(f"An error occurred: {str(e)}")


async def upload_file_by_name(client, asst_id: str, filename: str, force: bool = False):
    assts = client.beta.assistants
    assistant_files = assts.files

    file_id_by_name = await get_file_hashmap(client, asst_id)

    file_id = file_id_by_name.pop(filename.name, None)

    if not force:
        if file_id is not None:
            # print(f"File '{filename}' already uploaded")
            yellow_text(f"File '{filename}' already uploaded")
            return file_id, False

    if file_id:
        try:
            assistant_files.delete(assistant_id=asst_id, file_id=file_id)

        except Exception as e:
            # print(f"Failed to delete file '{filename}': {e}")
            red_text(f"Failed to delete file '{filename}': {e}")
            raise

        try:
            assts.files.delete(
                assistant_id=asst_id,
                file_id=file_id,
            )

        except:
            try:
                yellow_text(
                    f"Couldn't remove assistant file '{filename}', trying again..."
                )
                client.files.delete(file_id)
                green_text(f"File '{filename}' removed")
            except Exception as e:
                # print(f"Couldn't remove assistant file '{filename}': {e}")
                red_text(f"Couldn't remove assistant file '{filename}: {e}'")
                raise

    with open(filename, "rb") as file:
        uploaded_file = client.files.create(
            file=file,
            purpose="assistants",
        )
    try:
        assistant_files.create(
            assistant_id=asst_id,
            file_id=uploaded_file.id,
        )

        green_text(f"File '{filename}' uploaded")
        # print(f"File '{filename}' uploaded")
        return uploaded_file.id, True

    except Exception as e:
        # print(f"Failed to upload file '{filename}': {e}")
        red_text(f"\nFailed to upload file '{filename}': {e}\n")
        yellow_text(
            f"This can be a bug with the OpenAI API. Please check the storage at https://platform.openai.com/storage or try again"
        )
        return None, False
