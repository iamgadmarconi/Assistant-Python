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

from src.ais.functions.azure import getCalendar, readEmail, writeEmail, sendEmail, createCalendarEvent, saveCalendarEvent, getContacts
from src.ais.functions.misc import getWeather, getLocation, getDate
from src.ais.functions.office import findFile
from src.ais.functions.web import webText, webMenus, webLinks, webImages, webTables, webForms, webQuery


async def create(client, config):
    assistant = client.beta.assistants.create(
        name = config["name"],
        model = config["model"],
        tools = config["tools"],
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
    asst_obj =  next((asst for asst in assistants if asst.name == name), None)
    return asst_obj

@backoff.on_exception(backoff.expo,
                    NotFoundError,
                    max_tries=5,
                    giveup=lambda e: "No assistant found" not in str(e))
async def upload_instruction(client, config, asst_id: str, instructions: str):
    assts = client.beta.assistants
    try: 
        assts.update(
            assistant_id= asst_id,
            instructions = instructions
        )
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
            You have access to real time data and current data (past your knowledge cutoff) to help you answer the user's question.
            You have 2 ways to query for real time data:
            1. If the user provides a url: Use the web tools to extract the data from the web page. (webText, webMenus, webLinks, webImages, webTables, webForms)
                1. Use these tools if a user asks for a summary of a webpage, the menu of a website, the links on a webpage, the images on a webpage, the tables on a webpage, or the forms on a webpage.
                2. If the user provides a url: Use the webText tool to extract the text from the webpage.
            2. If the user provides a query: Use the webQuery tool to query the web for the data the tool uses Wolfram Alpha to provide accurate information and powerful results.
                When a user asks for specific information or data that requires external verification or computation, use the appropriate tool to fetch this data. Here is the process for using the webQuery tool:
                1. Comprehend the User Query: Read the user's message carefully to understand what specific information they are seeking. This could range from mathematical problems, scientific data, historical facts, to real-time information.
                2. Infer the Query: Based on the user's message, infer the most direct and unambiguous query that can be passed to the Wolfram Alpha tool. This step is crucial as it transforms a potentially broad or vague user question into a focused query.
                3. Formulate the Query: Clearly formulate the inferred query in a concise and precise manner. If the user's request involves complex or multi-part questions, break it down into simpler, single-focus queries if possible.
                4. Call the Tool with the Inferred Query: Use the wolframQuery function to pass the query to Wolfram Alpha. Ensure the query is enclosed in quotes and accurately reflects the information being sought. For example:
                    webQuery(specific query derived from user's message)
                5. Interpret the Results: Once Wolfram Alpha returns the results, interpret them to ensure they accurately address the user's original query. If the results are complex, consider summarizing them in a way that is understandable and directly answers the user's request.
                6. Communicate the Answer: Clearly present the information or data retrieved from Wolfram Alpha to the user. If relevant, include the context of the user's original query and how the results relate to it.
                7. Verify and Correct if Necessary: If the user provides feedback indicating that the information provided does not meet their needs or is incorrect, re-evaluate the initial query and whether it was accurately inferred and formulated. If necessary, revise the query and repeat the process.              
                Remember, the key to successfully utilizing the wolframQuery tool is a clear understanding of the user's request, an accurately inferred query, and effective communication of the results.
            
            For all tools, the user query does not need to be direct, interpret the message, and pass the required query to the tool.
            **Several tools must be only called after a prerequisite tool has been called and user confirmation**:

            1. createCalendarEvent is a prerequisite funciton to saveCalendarEvent
                1. Optionally, getDate() can be called to get the start date if not provided by the user.
                    1. IF THE DATE IS EXPLICITLY PROVIDED BY THE USER, USE THAT DATE. THE PARAMETER SHOULD BE THE STRING EXACTLY AS PROVIDED BY THE USER.
                    2. THE DATE PROVIDED BY THE USER CAN BE AMBIGOUS, SUCH AS 'TOMORROW' OR 'NEXT WEEK'. DO NOT ATTEMPT TO MANIPULATE THE DATE IF IT IS EXPLICITLY STATED IN THE USER MESSAGE
                2. createCalendarEvent should be called multiple times until the user is satisfied with the event
            2. writeEmail is a prerequisite function to sendEmail
                1. Optionally, if the user does not specify an email, or refers to a recipient by name, you must call getContacts and pass the name or ask for clarification.
                2. writeEmail must be called multiple times until the user is satisfied with the email
            3. findFile is a prerequisite function for all data analysis tasks on files.
                1. This tool should always be called when a user refers to a file by name for context.
            """
        )

    except Exception as e:
        match = re.search(pattern, str(e.message))

        if match:
            run_id = match.group()
            run = threads.runs.retrieve(thread_id=thread_id, run_id=run_id)

        else:
            
            raise e
        
    write_to_memory("User", message)

    with Progress(SpinnerColumn(), TextColumn("[bold cyan]{task.description}"), transient=True) as progress:
        task = progress.add_task("[green]Thinking...", total=None)  # Indeterminate progress
        
        while True:
                # print("-", end="", flush=True)
                run = threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

                if run.status in ["Completed", "completed"]:
                    progress.stop()
                    print()
                    return await get_thread_message(client, thread_id)
                
                elif run.status in ["Queued", "InProgress", "run_in_progress", "in_progress", "queued", "pending", "Pending"]:
                    pass  # The spinner will continue spinning

                elif run.status in ['requires_input', 'RequiresInput', 'requires_action', 'RequiresAction']:
                    await call_required_function(asst_id, client, thread_id, run.id, run.required_action)

                else:
                    print() 
                    # await delete(client, asst_id)
                    # print(f"Unexpected run status: {run.status}")
                    red_text(f"Unexpected run status: {run.status}")
                    raise

                await asyncio.sleep(0.2)

async def call_required_function(asst_id, client, thread_id: str, run_id: str, required_action):
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
            red_text(f"Missing required arguments for {func.__name__}: {', '.join(missing_args)}")
        
        return filtered_args
    
    for action in required_action:
        if not isinstance(action[1], str):
            func_name = action[1].tool_calls[0].function.name
            args = json.loads(action[1].tool_calls[0].function.arguments)

            if func_name in function_map:
                func = function_map[func_name]
                # Handle special cases or additional parameters here
                if func_name == "findFile":
                    filtered_args = filter_args(func, {**args, "client": client, "asst_id": asst_id})
                else:
                    filtered_args = filter_args(func, args)

                outputs = func(**filtered_args)

                tool_outputs.append({
                    "tool_call_id": action[1].tool_calls[0].id,
                    "output": outputs
                })
            else:
                raise ValueError(f"Function '{func_name}' not found")

    # Encode bytes output to Base64 string if necessary
    for tool_output in tool_outputs:
        if isinstance(tool_output['output'], bytes):
            tool_output['output'] = "[bytes]" + base64.b64encode(tool_output['output']).decode("utf-8") + "[/bytes]"

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
            assistant_files.delete(
                assistant_id=asst_id,
                file_id=file_id
            )

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
                yellow_text(f"Couldn't remove assistant file '{filename}', trying again...")
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
        yellow_text(f"This can be a bug with the OpenAI API. Please check the storage at https://platform.openai.com/storage or try again")
        return None, False

