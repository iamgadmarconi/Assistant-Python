
 # ==== file path: agent\..\src\agent\agent.py ==== 

import os
import asyncio
import json
from aiofiles import open as aio_open
from pathlib import Path
from openai import OpenAI

from src.utils.files import load_from_toml, list_files, bundle_to_file, load_from_json, load_to_json, ensure_dir, db_to_json, find
from src.utils.cli import green_text, red_text, yellow_text
from src.ais.assistant import load_or_create_assistant, upload_instruction, upload_file_by_name, get_thread, create_thread, run_thread_message


class Assistant:

    def __init__(self, directory) -> None:
        self.dir = directory

    async def init_from_dir(self, recreate: bool = False):
        self.config = load_from_toml(f"{self.dir}/agent.toml")
        self.oac = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.asst_id = await load_or_create_assistant(self.oac, self.config, recreate)
        self.name = self.config["name"]

        db_to_json()

        try:
            await upload_file_by_name(self.oac, asst_id=self.asst_id, filename=Path(r"agent\.agent\persistance\memory.json"), force=True)
        except:
            # print("No previous memory")
            yellow_text("No previous memory")

        await self.upload_instructions()
        await self.upload_files(recreate)

        return self

    async def upload_instructions(self):
        file_path = os.path.join(self.dir, self.config["instructions_file"])
        if os.path.exists(file_path):
            async with aio_open(file_path, 'r') as file:
                inst_content = await file.read()
            await upload_instruction(self.oac, self.config, self.asst_id, inst_content)  
            return True
        else:
            return False
        
    async def upload_files(self, recreate: bool) -> int:
        num_uploaded = 0

        data_files_dir = self.data_files_dir()

        exclude_element = f"*{self.asst_id}*"
        
        for file in list_files(data_files_dir, ["*.rs", "*.md"], [exclude_element]):

            if ".agent" not in str(file):
                raise Exception(f"File '{file}' is not in data directory")

            os.remove(file)

        for bundle in self.config["file_bundles"]:
            # print(f"\n debug -- bundle: {bundle}\n")
            src_dir = Path(self.dir).joinpath(bundle['src_dir'])
            # print(f"\n debug -- src_dir: {src_dir}\n")
            if src_dir.is_dir():
                src_globs = bundle['src_globs']

                files = list_files(src_dir, src_globs, None)

                # print(f"\n debug -- files: {files}\n")

                if files:
                    

                    if bundle['bundle_name'] == "source-code":
                        bundle_file_name = f"{self.name}-{bundle['bundle_name']}-{self.asst_id}.{bundle['dst_ext']}"
                        bundle_file = self.data_files_dir().joinpath(bundle_file_name)
                        force_reupload = recreate or not bundle_file.exists()

                        # Assuming bundle_to_file bundles files into the specified bundle_file
                        bundle_to_file(files, bundle_file)
                        # print(f"\n debug -- bundle_file: {type(bundle_file)}\n")
                        _, uploaded = await upload_file_by_name(self.oac, self.asst_id, bundle_file, force_reupload)

                        if uploaded:
                            num_uploaded += 1
                    else:  
                        for file in files:
                            # print(f"\n debug -- type: {type(file)}\n")
                            # print(f"\n debug -- file: {file}\n")
                            # print(f"\n debug -- path str: {str(file.resolve())}\n")
                            if not str(file.name) == "conv.json":
                                _, uploaded = await upload_file_by_name(self.oac, self.asst_id, file.resolve(), False)
                                if uploaded:
                                    num_uploaded += 1

        return num_uploaded
    
    async def load_or_create_conv(self, recreate: bool):
        conv_file = Path(self.data_dir()).joinpath("conv.json")

        if recreate and conv_file.exists():
            os.remove(conv_file)  # Removes the file

        try:
            conv = load_from_json(conv_file)
            await get_thread(self.oac, conv['thread_id'])
            # print(f"Conversation loaded")  
            green_text(f"Conversation loaded")

        except (FileNotFoundError, json.JSONDecodeError):
            thread_id = await create_thread(self.oac)
            # print(f"Conversation created")  
            green_text(f"Conversation created")
            conv = {'thread_id': thread_id}
            load_to_json(conv_file, conv)

        return conv
    
    async def chat(self, conv, msg: str) -> str:
        res = await run_thread_message(self.oac, self.asst_id, conv["thread_id"], msg)
        return res
    
    def data_dir(self) -> Path:
        """Returns the path to the data directory, ensuring its existence."""
        data_dir = Path(self.dir + r"\.agent")
        ensure_dir(data_dir)
        return data_dir

    def data_files_dir(self) -> Path:
        """Returns the path to the data files directory within the data directory, ensuring its existence."""
        files_dir = self.data_dir().joinpath("files")
        ensure_dir(files_dir)
        return files_dir


 # ==== file path: agent\..\src\agent\__init__.py ==== 




 # ==== file path: agent\..\src\ais\assistant.py ==== 

import asyncio
import backoff
import json
import os
import re
import base64

from openai import NotFoundError
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.ais.msg import get_text_content, user_msg
from src.utils.database import write_to_memory
from src.utils.files import find, get_file_hashmap
from src.utils.cli import red_text, green_text, yellow_text

from src.ais.functions.azure import getCalendar, readEmail, writeEmail, sendEmail, writeCalendarEvent, createCalendarEvent, getContacts
from src.ais.functions.misc import getWeather, getLocation, getDate
from src.ais.functions.office import findFile
from src.ais.functions.web import webText, webMenus, webLinks, webImages, webTables, webForms


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

async def delete(client, asst_id: str, wipe=False):
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
                    await delete(client, asst_id)
                    # print(f"Unexpected run status: {run.status}")
                    red_text(f"Unexpected run status: {run.status}")
                    raise

                await asyncio.sleep(0.5)

async def call_required_function(asst_id, client, thread_id: str, run_id: str, required_action):
    tool_outputs = []

    for action in required_action:
        if not isinstance(action[1], str):
            
            func_name = action[1].tool_calls[0].function.name
            args = json.loads(action[1].tool_calls[0].function.arguments)
            
            if func_name == "getWeather":
                outputs = getWeather(
                    msg = args.get("msg", None)
                )
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )
            elif func_name == "getCalendar":
                outputs = getCalendar(
                    upto = args.get("upto", None)
                )
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )
            
            elif func_name == "readEmail":
                outputs = readEmail(
                )
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )

            elif func_name == "writeEmail":
                outputs = writeEmail(
                    recipients=args.get("recipients", None),
                    subject = args.get("subject", None),
                    body = args.get("body", None),
                    attachments = args.get("attachments", None)
                )
                
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )
            
            elif func_name == "sendEmail":
                outputs = sendEmail(
                    recipients=args.get("recipients", None),
                    subject = args.get("subject", None),
                    body = args.get("body", None),
                    attachments = args.get("attachments", None)
                )
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )

            elif func_name == "getLocation":
                outputs = getLocation()
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )
            
            elif func_name == "getDate":
                outputs = getDate()
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )

            elif func_name == "writeCalendarEvent":
                outputs = writeCalendarEvent(
                    subject = args.get("subject", None),
                    start = args.get("start", None),
                    end = args.get("end", None),
                    location = args.get("location", None),
                    body = args.get("body", None),
                    recurrence = args.get("recurrence", False)
                )
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )

            elif func_name == "createCalendarEvent":
                outputs = createCalendarEvent(
                    subject = args.get("subject", None),
                    start = args.get("start", None),
                    end = args.get("end", None),
                    location = args.get("location", None),
                    body = args.get("body", None),
                    recurrence = args.get("recurrence", False)
                )
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )

            elif func_name == "getContacts":
                outputs = getContacts(
                    name = args.get("name", None)
                )
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )
            
            # elif func_name == "csvQuery":
            #     outputs = csvQuery(
            #         path = args.get("path", None),
            #         query = args.get("query", None)
            #     )
            #     tool_outputs.append(
            #         {
            #             "tool_call_id": action[1].tool_calls[0].id,
            #             "output": outputs
            #         }
            #     )
                
            elif func_name == "findFile":
                outputs = findFile(
                    client = client,
                    asst_id = asst_id,
                    filename = args.get("filename", None),
                )
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )
            
            elif func_name == "webText":
                outputs = webText(
                    url = args.get("url", None)
                )
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )
            
            elif func_name == "webMenus":
                outputs = webMenus(
                    url = args.get("url", None)
                )
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )
            
            elif func_name == "webLinks":
                outputs = webLinks(
                    url = args.get("url", None)
                )
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )

            elif func_name == "webImages":
                outputs = webImages(
                    url = args.get("url", None)
                )
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )

            elif func_name == "webTables":
                outputs = webTables(
                    url = args.get("url", None)
                )
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )

            elif func_name == "webForms":
                outputs = webForms(
                    url = args.get("url", None)
                )
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )
                
            else:
                raise ValueError(f"Function '{func_name}' not found")
            
    # print(f"debug-- tool_outputs: {tool_outputs}\n\n")

    for tool_output in tool_outputs:
        if isinstance(tool_output['output'], bytes):
            tool_output['output'] = "[bytes]" + base64.b64encode(tool_output['output']).decode("utf-8") + "[/bytes]"

    # print(f"debug-- tool_outputs after encoding: {tool_outputs}\n\n")

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




 # ==== file path: agent\..\src\ais\msg.py ==== 

import re
import base64

from io import BytesIO
from PIL import Image


class CreateMessageRequest:
    def __init__(self, role, content, **kwargs):
        self.role = role
        self.content = content
        for key, value in kwargs.items():
            setattr(self, key, value)

class MessageContentText:
    def __init__(self, text):
        self.text = text

class MessageContentImageFile:
    pass

class MessageObject:
    def __init__(self, content):
        self.content = content

def user_msg(content):
    return CreateMessageRequest(
        role="user",
        content=str(content),  # Converts the content into a string
    )

def get_text_content(client, msg):
    if not msg.content:
        raise ValueError("No content found in message")

    msg_content = next(iter(msg.content), None)

    if msg_content is None:
        raise ValueError("No content found in message")
    
    if hasattr(msg_content, "image_file"):
        file_id = msg_content.image_file.file_id
        resp = client.files.with_raw_response.retrieve_content(file_id)
        if resp.status_code == 200:
            image_data = BytesIO(resp.content)
            img = Image.open(image_data)
            img.show()
    
    msg_file_ids = next(iter(msg.file_ids), None)

    if msg_file_ids:
        file_data = client.files.content(msg_file_ids)
        file_data_bytes = file_data.read()
        with open("files", "wb") as file:
            file.write(file_data_bytes)
            
    message_content = msg_content.text
    annotations = message_content.annotations
    citations = []
    for index, annotation in enumerate(annotations):
        # Replace the text with a footnote
        message_content.value = message_content.value.replace(annotation.text, f' [{index}]')

        # Gather citations based on annotation attributes
        if (file_citation := getattr(annotation, 'file_citation', None)):
            cited_file = client.files.retrieve(file_citation.file_id)
            citations.append(f'[{index}] {file_citation.quote} from {cited_file.filename}')
        elif (file_path := getattr(annotation, 'file_path', None)):
            cited_file = client.files.retrieve(file_path.file_id)
            citations.append(f'[{index}] Click <here> to download {cited_file.filename}')
            # Note: File download functionality not implemented above for brevity

    # Add footnotes to the end of the message before displaying to user
    message_content.value += '\n' + '\n'.join(citations)

    if isinstance(msg_content.text.value, str):
        txt = msg_content.text.value
        # print(f"\n\ndebug --Text content: {txt}\n\n")
        pattern = r'\[bytes](.*?)\[/bytes]'
        # Find all occurrences of the pattern
        decoded_bytes_list = []
        text_parts = re.split(pattern, txt)  # Split the string into parts

        # Iterate over the split parts, decoding where necessary
        for i, part in enumerate(text_parts):
            if i % 2 != 0:  # The pattern is expected to capture every second element
                # Decode and store the bytes
                decoded_bytes = base64.b64decode(part)
                decoded_bytes_list.append(decoded_bytes)
                # Replace the original encoded string with a placeholder or remove it
                text_parts[i] = ""  # Remove or replace with a placeholder as needed

        # Reassemble the textual content without the encoded bytes
        textual_content = "".join(text_parts)
        # print(f"\n\nDecoded bytes: {decoded_bytes_list}\n\n")
        for resp in decoded_bytes_list:
            image_data = BytesIO(resp)
            img = Image.open(image_data)
            img.show()

        if len(citations) > 0:
            textual_content += '\n' + '\n'.join(citations)

        return textual_content
    
    else:
        raise ValueError("Unsupported message content type")



 # ==== file path: agent\..\src\ais\__init__.py ==== 




 # ==== file path: agent\..\src\ais\functions\azure.py ==== 

import os
import dateparser

from typing import Optional
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
from O365 import Account, MSGraphProtocol
from O365.utils import Query

from src.utils.files import find
from src.utils.tools import get_context, html_to_text

SCOPES = ["basic", "message_all", "calendar_all", "address_book_all", "tasks_all"]


def O365Auth(scopes_helper: list[str] = SCOPES):
    protocol = MSGraphProtocol()
    credentials = (os.environ.get("CLIENT_ID"), os.environ.get("CLIENT_SECRET"))
    scopes_graph = protocol.get_scopes_for(scopes_helper)

    try:
        account = Account(credentials, protocol=protocol)

        if not account.is_authenticated:
            account.authenticate(scopes=scopes_graph)

        return account
    
    except:
        raise Exception("Failed to authenticate with O365")

def writeEmail(recipients: list, subject: str, body: str, attachments: Optional[list] = None):
    
    email_report = (
        f"To: {', '.join([recipient for recipient in recipients])}\n"
        f"Subject: {subject}\n"
        f"Body: {body}\n"
        f"Attachments: {', '.join([attachment for attachment in attachments]) if attachments else 'None'}"
    )

    return email_report


def sendEmail(recipients: list, subject: str, body: str, attachments: Optional[list] = None):
    try:
        account = O365Auth(SCOPES)
        m = account.new_message()
        m.to.add(recipients)
        m.subject = subject
        m.body = body
        m.body_type = "HTML"

        if attachments:

            for attachment_path in attachments:
                path = find(attachment_path, r'files/mail')
                m.attachments.add(path)
        
        m.send()
        
        return "Email sent successfully"
    
    except:
        return "Failed to send email"

def readEmail():
    
    account = O365Auth(SCOPES)

    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    messages = inbox.get_messages(limit=5)
    

    email_reports = []

    for message in messages:
        
        message_body = html_to_text(message.body)

        email_report = (f"From: {message.sender}\n"
                        f"Subject: {message.subject}\n"
                        f"Received: {message.received}\n"
                        f"Body: {message_body}\n")
        
        email_reports.append(email_report)

    email_reports = "\n".join(email_reports)

    return email_reports
    
def getCalendar(upto: Optional[str] = None):

    account = O365Auth(SCOPES)

    if upto is None:
        upto = datetime.now() + timedelta(days=7)
        
    else:
        time = get_context(upto, ["TIME", "DATE"])
        if time == "":
            time = "7 days"
            
        settings = {"PREFER_DATES_FROM": "future"}
        diff = dateparser.parse(time, settings=settings)

        if diff is not None:
            upto = diff

        else:
            upto = datetime.now() + timedelta(days=7)  # Default to 7 days from now if parsing fails

    schedule = account.schedule()
    calendar = schedule.get_default_calendar()

    q = calendar.new_query('start').greater_equal(datetime.now())
    q.chain('and').on_attribute('end').less_equal(upto)

    try:
        events = calendar.get_events(query=q, include_recurring=True)

    except:
        events = calendar.get_events(query=q, include_recurring=False)

    cal_reports = []

    for event in events:

        cal_report = (f"Event: {event.subject}\n"
                      f"Start: {event.start}\n"
                      f"End: {event.end}\n"
                      f"Location: {event.location}\n"
                      f"Description: {event.body}")
        
        cal_reports.append(cal_report)

    cal_reports = "\n".join(cal_reports)

    return cal_reports

def writeCalendarEvent(subject: str, start: str, end: Optional[str], location: Optional[str], body: Optional[str], recurrence: False):
    
    settings = {"PREFER_DATES_FROM": "future"}

    start_time = get_context(start, ["TIME", "DATE"])
    if start_time != "":
        start_time_str = dateparser.parse(start_time, settings=settings).strftime("%d/%m/%Y, %H:%M:%S")
    else:
        start_time_str = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

    if end:
        end_time = get_context(end, ["TIME", "DATE"])
        if end_time != "":
            end_time_str = dateparser.parse(end_time, settings=settings).strftime("%d/%m/%Y, %H:%M:%S")
        else:
            end_time_str = (datetime.now() + timedelta(hours=1)).strftime("%d/%m/%Y, %H:%M:%S")

    start_end_str = f"Start: {start_time_str}, End: {end_time_str}" if end else f"Start: {start_time_str}\n"
    location_str = f"Location: {location}" if location else ""
    recurrence_str = f"Recurrence: {recurrence}" if recurrence else ""

    # Simplified f-string
    calendar_report = (
        f"Subject: {subject}\n"
        f"Body: {body}\n"
        f"{start_end_str}"
        f"{location_str}"
        f"{recurrence_str}"
    )

    return calendar_report

def createCalendarEvent(subject: str, start: str, end: Optional[str], location: Optional[str], body: Optional[str], recurrence: False):
    account = O365Auth(SCOPES)
    schedule = account.schedule()
    calendar = schedule.get_default_calendar()
    event = calendar.new_event()

    start = dateparser.parse(start)

    if end:
        end = dateparser.parse(end)
    else:
        end = start + timedelta(hours=1)

    event.start = start
    event.end = end

    event.subject = subject

    if body:
        event.body = body

    if location:
        event.location = location

    # if recurrence:
    #     event.is_all_day = True
    #     event.recurrence = True

    event.save()

    return "Event created successfully"


def query():
    pass

def getContacts(name: Optional[str]):
    threshold = 80
    account = O365Auth(SCOPES)
    contacts = account.address_book().get_contacts()

    if not name:
        contact_reports = []

        for contact in contacts:
            email_addresses = ', '.join([email.address for email in contact.emails])

            home_phones = ', '.join(contact.home_phones) if contact.home_phones else 'None'
            business_phones = ', '.join(contact.business_phones) if contact.business_phones else 'None'
            
            contact_report = (f"Name: {contact.full_name}\n"
                              f"Email: {email_addresses}\n"
                              f"Phone: {home_phones}, {business_phones}")
            
            contact_reports.append(contact_report)

        contact_reports = "\n".join(contact_reports)
    
    else:
        contact_reports = []
        for contact in contacts:
            # Calculate the fuzzy match score
            match_score = fuzz.ratio(contact.full_name.lower(), name.lower())
            
            if match_score >= threshold:
                email_addresses = ', '.join([email.address for email in contact.emails])

                home_phones = ', '.join(contact.home_phones) if contact.home_phones else 'None'
                business_phones = ', '.join(contact.business_phones) if contact.business_phones else 'None'
                
                contact_report = (f"Name: {contact.full_name}\n"
                                f"Email: {email_addresses}\n"
                                f"Phone: {home_phones}, {business_phones}\n"
                                f"__Match_Score: {match_score}")
                
                contact_reports.append(contact_report)

        contact_reports = "\n".join(contact_reports)

    return contact_reports


 # ==== file path: agent\..\src\ais\functions\math.py ==== 

import requests

def mathSolver():
    pass


 # ==== file path: agent\..\src\ais\functions\misc.py ==== 

import requests
import os
import dateparser
import geocoder

from geopy.geocoders import Nominatim
from typing import Optional
from datetime import datetime
from geotext import GeoText

from src.utils.tools import get_context


def getDate():
    return datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

def getLocation():
    g = geocoder.ip('me').city
    geolocator = Nominatim(user_agent="User")
    location = geolocator.geocode(g)
    return location.address

def getWeather(msg: Optional[str]):
    api_key = os.environ.get("OPENWEATHER_API_KEY")

    time = get_context(msg, ["TIME", "DATE"])
    location = get_context(msg, ["GPE"])

    if location == "":
        g = geocoder.ip('me').city
        geolocator = Nominatim(user_agent="User")
        location = geolocator.geocode(g)
        lat, lon = location.latitude, location.longitude

    else:
        location = GeoText(location).cities

        geolocator = Nominatim(user_agent="User")
        location = geolocator.geocode(location[0])
        lat = location.latitude
        lon = location.longitude

    try:
        time = dateparser.parse(time).timestamp()

    except:
        time = datetime.now().timestamp()
        
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}"

    response = requests.get(url)

    if response.status_code == 200:
        # Successful API call
        data = response.json()

        match = min(data['list'], key=lambda x: abs(x['dt'] - int(time)))
        main = match['main']

        temperature = main['temp']
        humidity = main['humidity']
        weather_description = match['weather'][0]['description']
        
        weather_report = (f"Location: {location}\n"
                          f"Time: {datetime.fromtimestamp(time)}\n"
                          f"Temperature: {temperature - 273.15}°C\n"
                          f"Humidity: {humidity}%\n"
                          f"Description: {weather_description.capitalize()}")
        return weather_report
    else:
        # API call failed this usually happens if the API key is invalid or not provided
        return f"Failed to retrieve weather data: {response.status_code}"



 # ==== file path: agent\..\src\ais\functions\office.py ==== 

import csv

import pandas as pd

from src.utils.files import get_file_hashmap, find


def findFile(client, asst_id, filename: str):

    file_id_by_name = get_file_hashmap(client, asst_id)
    
    file_id = file_id_by_name.get(filename, "File not found")

    return file_id

def csvWriter(filename:str, data: list):
    # path = find(filename)
    # with open(path, 'r', encoding='utf-8') as file:
    #     writer = csv.writer(file)
    # TODO: Implement csvWriter
    pass



 # ==== file path: agent\..\src\ais\functions\web.py ==== 

from src.utils.tools import web_parser

    
def webText(url: str):
    print(f"\n debug-- Called webText with url: {url}")
    text = web_parser(url).get_text()
    print(f"\n debug-- webText returned: {text}")

    return text

def webMenus(url: str):
    soup = web_parser(url)
    menus = soup.find_all(['a', 'nav', 'ul', 'li'], class_=['menu', 'nav', 'nav-menu', 'nav-menu-item'])
    menu_list = []
    for menu in menus:
        menu_list.append(menu.text)
    return "\n".join(menu_list)

def webLinks(url: str):
    soup = web_parser(url)
    links = soup.find_all('a')
    link_list = []
    for link in links:
        link_list.append(link.get('href'))
    return "\n".join(link_list)

def webImages(url: str):
    soup = web_parser(url)
    images = soup.find_all('img')
    image_list = []
    for image in images:
        image_list.append(image.get('src'))
    return "\n".join(image_list)

def webTables(url: str):
    soup = web_parser(url)
    tables = soup.find_all('table')
    table_list = []
    for table in tables:
        table_list.append(table.text)
    return "\n".join(table_list)

def webForms(url: str):
    soup = web_parser(url)
    forms = soup.find_all('form')
    form_list = []
    for form in forms:
        form_list.append(form.text)
    return "\n".join(form_list)

# def menuInteract(url: str, menu: str):
#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

#     driver.get(url)
#     # Use XPath to find an element by text, this is one example, adjust based on the webpage structure
#     menu_item = driver.find_element(By.XPATH, f"//*[contains(text(), '{menu}')]")
#     menu_item_id = menu_item.get_attribute('id')
#     print(f"The ID of the menu item '{menu}' is: {menu_item_id}")
#     menu_item.click()
#     driver.quit()
#     time.sleep(5)  # Adjust sleep time as necessary

#     new_page_url = driver.current_url
#     return new_page_url


 # ==== file path: agent\..\src\gui\app.py ==== 

import asyncio


from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Input, Static

from src.agent.agent import Assistant


DEFAULT_DIR = "agent"


class FocusableContainer(Container, can_focus=True):  
    """Focusable container widget."""


class MessageBox(Widget, can_focus=True):  
    """Box widget for the message."""

    def __init__(self, text: str, role: str) -> None:
        self.text = text
        self.role = role
        super().__init__()

    def compose(self) -> ComposeResult:
        """Yield message component."""
        yield Static(self.text, classes=f"message {self.role}")


class ChatApp(App):
    """Chat app."""

    TITLE = "chatui"
    SUB_TITLE = "ChatGPT directly in your terminal"
    CSS_PATH = r"app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", key_display="Q / CTRL+C"),
        ("ctrl+x", "clear", "Clear"),
    ]

    def compose(self) -> ComposeResult:
        """Yield components."""
        yield Header()
        with FocusableContainer(id="conversation_box"):
            yield MessageBox(
                "Welcome to chatui!\n"
                "Type your question, click enter or 'send' button "
                "and wait for the response.\n"
                "At the bottom you can find few more helpful commands.",
                role="info",
            )
        with Horizontal(id="input_box"):
            yield Input(placeholder="Enter your message", id="message_input")
            yield Button(label="Send", variant="success", id="send_button")
        yield Footer()

    async def on_mount(self) -> None:
        """Start the conversation and focus input widget."""
        assistant = Assistant(DEFAULT_DIR)
        self.asst = await assistant.init_from_dir(False)
        self.conv = await assistant.load_or_create_conv(False)
        self.query_one(Input).focus()

    def action_clear(self) -> None:
        """Clear the conversation and reset widgets."""
        # self.conversation.clear()
        conversation_box = self.query_one("#conversation_box")
        conversation_box.remove()
        self.mount(FocusableContainer(id="conversation_box"))

    async def on_button_pressed(self) -> None:
        """Process when send was pressed."""
        await self.process_conversation()

    async def on_input_submitted(self) -> None:
        """Process when input was submitted."""
        await self.process_conversation()

    async def process_conversation(self) -> None:
        """Process a single question/answer in conversation."""
        message_input = self.query_one("#message_input", Input)
        # Don't do anything if input is empty
        if message_input.value == "":
            return
        button = self.query_one("#send_button")
        conversation_box = self.query_one("#conversation_box")

        self.toggle_widgets(message_input, button)

        # Create question message, add it to the conversation and scroll down
        message_box = MessageBox(message_input.value, "question")
        conversation_box.mount(message_box)
        conversation_box.scroll_end(animate=False)

        # Clean up the input without triggering events
        with message_input.prevent(Input.Changed):
            message_input.value = ""

        # Take answer from the chat and add it to the conversation
        res = await self.asst.chat(self.conv, message_box.text)
        # self.conversation.pick_response(choices[0])
        conversation_box.mount(
            MessageBox(
                res,
                "answer",
            )
        )

        self.toggle_widgets(message_input, button)
        # For some reason single scroll doesn't work
        conversation_box.scroll_end(animate=False)
        conversation_box.scroll_end(animate=False)

    def toggle_widgets(self, *widgets: Widget) -> None:
        """Toggle a list of widgets."""
        for w in widgets:
            w.disabled = not w.disabled



 # ==== file path: agent\..\src\gui\cli.py ==== 

import asyncio

from typing import Union

from src.agent.agent import Assistant
from src.utils.cli import asst_msg, help_menu, welcome_message


DEFAULT_DIR = "agent"

class Cmd:

    Quit = "Quit"
    RefreshAll = "RefreshAll"
    RefreshConv = "RefreshConv"
    RefreshInst = "RefreshInst"
    RefreshFiles = "RefreshFiles"
    Chat = "Chat"
    Help = "Help"
    Clear = "Clear"

    def __init__(self) -> None:
        pass

    @classmethod
    def from_input(cls, input: Union[str, object]) -> str:
        input_str = str(input)

        if input_str == "/q":
            return cls.Quit
        
        elif input_str in ["/r", "/ra"]:
            return cls.RefreshAll
        
        elif input_str == "/rc":
            return cls.RefreshConv
        
        elif input_str == "/ri":
            return cls.RefreshInst
        
        elif input_str == "/rf":
            return cls.RefreshFiles
        
        elif input_str == "/h":
            return cls.Help
        
        elif input_str.startswith("/c"):
            return "Clear"
        
        else:
            return f"{cls.Chat}: {input_str}"

async def cli():
    assistant = Assistant(DEFAULT_DIR)
    asst = await assistant.init_from_dir(False)
    conv = await assistant.load_or_create_conv(False)

    welcome_message()

    while True:
        print()
        user_input = input("User: ")
        cmd = Cmd.from_input(user_input)

        if cmd == Cmd.Quit:
            break

        elif cmd.startswith(Cmd.Chat):
            msg = cmd.split(": ", 1)[1]  
            res = await asst.chat(conv, msg)
            #print(f"{asst_msg(res)}")
            asst_msg(res)

        elif cmd == Cmd.RefreshAll:
            asst = Assistant(DEFAULT_DIR)
            await asst.init_from_dir(True)
            await asst.load_or_create_conv(True)

        elif cmd == Cmd.RefreshConv:
            await asst.load_or_create_conv(True)

        elif cmd == Cmd.RefreshInst:
            await asst.upload_instructions()
            await asst.load_or_create_conv(True)

        elif cmd == Cmd.RefreshFiles:
            await asst.upload_files(True)
            asst.load_or_create_conv(True)

        elif cmd == Cmd.Help:
            help_menu()

        elif cmd == Cmd.Clear:
            print("\033[H\033[J")
            welcome_message()




 # ==== file path: agent\..\src\utils\cli.py ==== 

import shutil

from rich.console import Console
from rich.text import Text
from rich.markdown import Markdown
from rich.panel import Panel
from rich.columns import Columns


def asst_msg(content):
    term_width = shutil.get_terminal_size().columns
    console = Console()
    markdown = Markdown(content)
    panel = Panel(markdown, title="Buranya", expand=False)
    console.print(panel, style="cyan")

def red_text(content):
    console = Console()
    text = Text(content)
    text.stylize("red")
    console.print(text)

def green_text(content):
    console = Console()
    text = Text(content)
    text.stylize("green")
    console.print(text)

def yellow_text(content):
    console = Console()
    text = Text(content)
    text.stylize("yellow")
    console.print(text)

def help_menu():
    console = Console()

    term_width = shutil.get_terminal_size().columns

    ascii_art = """
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡤⣶⠇⢳⠄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⠋⣡⣊⡴⡄⠈⠉⢧⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠔⣾⠃⠀⠀⠀⠀⠀⠀⠀⢀⠞⠉⢀⣼⠟⢹⢃⣇⣀⣀⡈⢳⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣰⠏⣼⠇⠀⠀⠀⣀⠤⠖⠚⠛⠛⠒⠒⠫⠼⢤⣼⣔⠋⡿⢹⠁⠀⣷⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢠⣄⠀⠰⡏⠀⣿⣆⣀⣴⠟⠁⠀⠀⢀⠤⠒⠒⣀⣈⣉⣩⠤⠴⠟⢒⠷⠒⠉⠉⠉⠉⠛⢦⡀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢺⠻⣦⡀⢷⡀⢣⣏⢁⢇⣠⠔⠒⠈⠉⠉⠉⠉⠉⠘⠢⢄⡫⣓⡶⠁⠀⠀⠀⠀⠀⠀⠀⠀⠙⣦⡀⠀⠀⠀
⠀⠀⠀⣀⣼⣆⠈⠛⠿⠿⠶⢽⡾⠉⠁⡀⠀⠀⠀⠠⠀⠂⢤⡤⠤⠤⢬⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⡌⣲⡄⠀
⢰⡾⠟⢛⣲⠶⠿⡶⡶⢲⠞⢡⠀⠀⠀⠈⠑⢤⣀⡀⠀⠀⠀⠹⣯⠉⢁⡆⠀⠀⠀⠀⠀⢀⣀⣀⣀⠀⠀⠀⢸⡇⠀⠀
⢸⡷⠀⠈⠒⢤⠜⡜⠀⡏⠀⡆⠀⠀⠰⡀⠀⠀⠙⡯⣵⠖⢲⣍⠉⠉⠛⢷⠀⠀⠀⡴⠊⠁⠀⠀⠀⠉⠲⡀⢈⠑⢤⡀
⠈⠳⡀⠀⢠⣃⢴⠀⢀⠀⢀⡇⡆⠀⠀⢏⡲⢄⣀⠝⠁⠀⢸⣿⣷⡀⠀⠘⣧⠀⠸⠀⠀⠀⠀⠀⠀⠀⠀⢸⣸⠖⠉⠁
⠀⠀⠳⡀⠉⠉⡛⠀⢸⠀⢸⡿⡝⣄⠀⢸⡏⠓⡏⠀⠀⠀⠀⢻⣿⣷⠀⢰⡓⠷⣔⠀⠀⠀⠀⠀⠀⠀⠀⢸⡟⠀⠀⠀
⠀⠀⠀⠑⢄⣀⡇⢰⣿⢇⠸⡇⣨⣎⠒⠚⠣⢄⣇⠀⠀⠀⠀⠀⠙⢻⡴⠁⠘⡖⡟⠑⠦⣀⡀⠀⢀⣀⠴⠋⣧⠀⠀⠀
⠀⠀⠀⠀⠀⠉⣿⡾⢻⣄⡱⠋⠀⢿⣷⡄⠀⠀⢹⠢⠤⠀⠤⠄⠞⠁⠀⠀⡘⠀⢣⡀⡠⡺⠉⢏⠹⡖⠒⠒⠛⠀⠀⠀
⠀⠀⠀⠀⠀⠀⡿⣿⢸⠈⡇⠀⠀⠈⢿⣿⣆⠀⢸⠀⣀⣀⣀⡴⢥⠀⠀⢰⠁⠀⠀⢏⢰⠃⠀⢘⣤⡇⠀⠀⠀⠀⠀⠀
⠀⠀⡀⠀⠤⢚⣿⡽⣻⠀⢣⠀⠀⠀⠀⠙⢛⠴⢁⡼⢡⠞⠁⠀⠠⡇⢠⠃⠀⠀⠀⠈⣇⢀⡠⣿⠃⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠈⠁⠀⠉⢹⡇⣏⠀⠀⠉⣶⠒⠒⠊⠁⠉⠁⠳⣏⠀⠀⣠⠞⡠⣿⠀⠀⠀⠀⠀⠀⢀⡾⠁⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣸⣷⠽⣆⡀⠀⠇⣳⣄⡀⠀⠀⠀⠀⠈⢉⣩⠴⢊⠁⡏⠀⠀⠀⠀⠀⣠⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢠⡞⠉⠀⠀⠀⠈⠑⢢⡏⢦⠈⠁⡖⠲⣖⡲⠛⠁⠀⠈⡆⠀⠀⠀⠀⣠⠞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣰⠏⠀⠀⠀⠀⠀⢀⡀⠀⠇⠀⠳⠊⢀⡠⠊⠀⠀⠀⠀⠀⠘⣄⢀⣠⠞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⡏⠀⠀⠀⠀⡠⠊⠁⠈⠱⡇⠀⢀⣴⠟⠀⠀⠀⠀⠀⠀⠀⢰⣈⡿⠘⠢⢄⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣇⠀⠀⠀⡜⠀⠀⠀⠀⣼⠥⣤⣫⠊⠀⠀⠀⠀⠀⠀⠀⠀⢸⢠⣇⣀⠀⠀⠀⢀⠬⠷⠤⣀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠙⢦⣄⠀⢣⡀⢀⡠⠊⢀⠇⢨⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⢨⡾⠁⠀⠉⠀⠲⣇⠤⢄⣀⠀⠙⢦⡀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠈⢉⣙⣛⣯⣣⣄⡎⢠⣃⡠⠤⠐⣲⣶⣦⣄⡀⠀⠀⢸⣧⡀⢀⡀⠀⠀⠓⠤⣤⣈⠱⡄⠀⢻⡄⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣿⣿⣶⡀⠀⠀⠙⠻⠋⠀⣠⠞⠋⠉⠀⠀⠈⠳⡀⡜⠁⢱⠀⠈⠓⢄⡀⠀⠀⠉⢲⡇⠀⠀⣷⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⡄⠀⠀⠀⢀⣞⣁⠀⠀⠀⠀⠀⠀⠀⣱⡇⣠⠴⢏⠲⣄⠈⠑⢤⡀⢀⡼⠃⠀⢠⡿⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⡀⠀⠀⠸⣿⣿⣿⣦⡀⠀⠀⠀⢠⣿⠿⢷⣄⡀⠙⢮⡳⢄⡀⠈⠁⠀⣠⢔⡿⠁⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣷⣤⣀⠀⣽⣿⣿⣿⣧⠀⠀⠀⠚⠁⠀⠀⠈⢻⡄⠀⠉⠢⢭⣩⣉⡩⠖⠋⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠙⢿⣿⣿⣿⣿⣿⣿⣿⠋⠉⠹⣿⣧⠀⠀⠀⠀⠀⠀⠀⣠⡷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠉⣻⣿⡃⠀⠀⠀⣿⣿⣿⣶⣦⣤⣶⣶⣿⣏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢀⣤⠴⠦⠤⣄⡀⢀⡾⠁⠀⠉⠳⣄⣸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢠⣞⣁⣀⠀⠀⠈⢷⠟⠋⠓⢦⡀⠀⢘⣿⣿⣿⡿⠿⠛⢿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢸⣿⣿⣿⣿⣶⡀⠘⣦⣄⠀⠀⢱⡀⢠⡏⠉⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠸⣿⣿⣿⣿⣿⣧⠀⠈⢻⡃⠀⢸⣷⠋⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠹⣿⣿⣿⣿⣿⠀⠀⠀⠑⣤⠞⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢨⣿⣿⣿⣿⡆⠀⣠⣾⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠈⢿⣿⣿⣿⡹⣄⣿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠙⢿⣿⡧⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    
    """
    help_message_1 = Text("Here are some commands you can use:\n", style="bold")
    help_message_2 = Text("\n    - '\h' : Display this help menu", style="")
    help_message_3 = Text("\n    - '\q' : Quit the program", style="")
    help_message_4 = Text("\n    - '\r' : Recreate the assistant", style="")
    help_message_5 = Text("\n    - '\ra' : Refresh all data", style="")
    help_message_6 = Text("\n    - '\rc' : Refresh the conversation", style="")
    help_message_7 = Text("\n    - '\ri' : Refresh the instructions", style="")
    help_message_8 = Text("\n    - '\rf' : Refresh the files", style="")
    help_message_9 = Text("\n    - '\c' : Clear the screen", style="")
    help_message_10 = Text("\n\nHow can I help you today?", style="bold")

    help_message = help_message_1 + help_message_2 + help_message_3 + help_message_4 + help_message_5 + \
        help_message_6 + help_message_7 + help_message_8 + help_message_9

    art_panel = Panel(ascii_art, title="Buranya", expand=False)

    if term_width < 80:
        message_panel = Panel(help_message, title="Message", expand=False, border_style="green")
        console.print(Columns([art_panel, message_panel], expand=True, equal=True))

    else:
        message_panel = Panel(help_message, title="Message", expand=False, border_style="green", width=term_width // 2)
        console.print(Columns([art_panel, message_panel], expand=True))

def welcome_message():
    console = Console()

    term_width = shutil.get_terminal_size().columns

    ascii_art = """
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀   ⢀⡔⣻⠁⠀⢀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢀⣾⠳⢶⣦⠤⣀⠀⠀⠀⠀⠀⠀⠀⣾⢀⡇⡴⠋⣀⠴⣊⣩⣤⠶⠞⢹⣄⠀⠀⠀
⠀⠀⠀⠀⢸⠀⠀⢠⠈⠙⠢⣙⠲⢤⠤⠤⠀⠒⠳⡄⣿⢀⠾⠓⢋⠅⠛⠉⠉⠝⠀⠼⠀⠀⠀
⠀⠀⠀⠀⢸⠀⢰⡀⠁⠀⠀⠈⠑⠦⡀⠀⠀⠀⠀⠈⠺⢿⣂⠀⠉⠐⠲⡤⣄⢉⠝⢸⠀⠀⠀
⠀⠀⠀⠀⢸⠀⢀⡹⠆⠀⠀⠀⠀⡠⠃⠀⠀⠀⠀⠀⠀⠀⠉⠙⠲⣄⠀⠀⠙⣷⡄⢸⠀⠀⠀
⠀⠀⠀⠀⢸⡀⠙⠂⢠⠀⠀⡠⠊⠀⠀⠀⠀⢠⠀⠀⠀⠀⠘⠄⠀⠀⠑⢦⣔⠀⢡⡸⠀⠀⠀
⠀⠀⠀⠀⢀⣧⠀⢀⡧⣴⠯⡀⠀⠀⠀⠀⠀⡎⠀⠀⠀⠀⠀⢸⡠⠔⠈⠁⠙⡗⡤⣷⡀⠀⠀
⠀⠀⠀⠀⡜⠈⠚⠁⣬⠓⠒⢼⠅⠀⠀⠀⣠⡇⠀⠀⠀⠀⠀⠀⣧⠀⠀⠀⡀⢹⠀⠸⡄⠀⠀
⠀⠀⠀⡸⠀⠀⠀⠘⢸⢀⠐⢃⠀⠀⠀⡰⠋⡇⠀⠀⠀⢠⠀⠀⡿⣆⠀⠀⣧⡈⡇⠆⢻⠀⠀
⠀⠀⢰⠃⠀⠀⢀⡇⠼⠉⠀⢸⡤⠤⣶⡖⠒⠺⢄⡀⢀⠎⡆⣸⣥⠬⠧⢴⣿⠉⠁⠸⡀⣇⠀
⠀⠀⠇⠀⠀⠀⢸⠀⠀⠀⣰⠋⠀⢸⣿⣿⠀⠀⠀⠙⢧⡴⢹⣿⣿⠀⠀⠀⠈⣆⠀⠀⢧⢹⡄
⠀⣸⠀⢠⠀⠀⢸⡀⠀⠀⢻⡀⠀⢸⣿⣿⠀⠀⠀⠀⡼⣇⢸⣿⣿⠀⠀⠀⢀⠏⠀⠀⢸⠀⠇
⠀⠓⠈⢃⠀⠀⠀⡇⠀⠀⠀⣗⠦⣀⣿⡇⠀⣀⠤⠊⠀⠈⠺⢿⣃⣀⠤⠔⢸⠀⠀⠀⣼⠑⢼ 
⠀⠀⠀⢸⡀⣀⣾⣷⡀⠀⢸⣯⣦⡀⠀⠀⠀⢇⣀⣀⠐⠦⣀⠘⠀⠀⢀⣰⣿⣄⠀⠀⡟⠀⠀
⠀⠀⠀⠀⠛⠁⣿⣿⣧⠀⣿⣿⣿⣿⣦⣀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣴⣿⣿⡿⠈⠢⣼⡇⠀⠀
⠀⠀⠀⠀⠀⠀⠈⠁⠈⠻⠈⢻⡿⠉⣿⠿⠛⡇⠒⠒⢲⠺⢿⣿⣿⠉⠻⡿⠁⠀⠀⠈⠁⠀⠀
⢀⠤⠒⠦⡀⠀⠀⠀⠀⠀⠀⠀⢀⠞⠉⠆⠀⠀⠉⠉⠉⠀⠀⡝⣍⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⡎⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀⡰⠋⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⢡⠈⢦⠀⠀⠀⠀⠀⠀⠀⠀⠀
⡇⠀⠀⠸⠁⠀⠀⠀⠀⢀⠜⠁⠀⠀⠀⡸⠀⠀⠀⠀⠀⠀⠀⠘⡄⠈⢳⡀⠀⠀⠀⠀⠀⠀⠀
⡇⠀⠀⢠⠀⠀⠀⠀⠠⣯⣀⠀⠀⠀⡰⡇⠀⠀⠀⠀⠀⠀⠀⠀⢣⠀⢀⡦⠤⢄⡀⠀⠀⠀
⢱⡀⠀⠈⠳⢤⣠⠖⠋⠛⠛⢷⣄⢠⣷⠁⠀⠀⠀⠀⠀⠀⠀⠀⠘⡾⢳⠃⠀⠀⠘⢇⠀⠀⠀
⠀⠙⢦⡀⠀⢠⠁⠀⠀⠀⠀⠀⠙⣿⣏⣀⠀⠀⠀⠀⠀⠀⠀⣀⣴⣧⡃⠀⠀⠀⠀⣸⠀⠀⠀
⠀⠀⠀⠈⠉⢺⣄⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣗⣤⣀⣠⡾⠃⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠣⢅⡤⣀⣀⣠⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠉⠉⠉⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠉⠁⠀⠉⣿⣿⣿⣿⣿⡿⠻⣿⣿⣿⣿⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣿⣿⣿⠀⠀⠀⠀⣿⣿⣿⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⣿⣿⣿⣟⠀⠀⢠⣿⣿⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⣿⣿⣿⠀⠀⢸⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⡏⠀⠀⢸⣿⣿⣿⣿⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣿⣿⠀⠀⠀⢺⣿⣿⣿⣿⣿⣿⣷⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠈⠉⠻⣿⣿⣿⠟⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢿⣿⣿⣿⠏ 

    """

    welcome_message_1 = Text("Hello! I'm Buranya, your personal assistant.\n", style="bold")
    welcome_message_2 = Text("\nI can help you with your daily tasks.", style="")
    welcome_message_3 = Text("\nYou can ask me to do things like:", style="")
    welcome_message_4 = Text("\n    - Send an email", style="")
    welcome_message_5 = Text("\n    - Check the weather", style="")
    welcome_message_6 = Text("\n    - Set a reminder", style="")
    welcome_message_7 = Text("\n    - Check your calendar", style="")
    welcome_message_8 = Text("\n    - And more...", style="")
    welcome_message_9 = Text("\n\nFor a list of commands, type '\h'")
    welcome_message_10 = Text("\n\nHow can I help you today?", style="bold")

    welcome_message = welcome_message_1 + welcome_message_2 + welcome_message_3 + welcome_message_4 + \
        welcome_message_5 + welcome_message_6 + welcome_message_7 + welcome_message_8 + welcome_message_9 + welcome_message_10
    art_panel = Panel(ascii_art, title="Buranya", expand=False)

    if term_width < 80:
        message_panel = Panel(welcome_message, title="Message", expand=False, border_style="green")
        console.print(Columns([art_panel, message_panel], expand=True, equal=True))

    else:
        message_panel = Panel(welcome_message, title="Message", expand=False, border_style="green", width=term_width // 2)
        console.print(Columns([art_panel, message_panel], expand=True))


 # ==== file path: agent\..\src\utils\database.py ==== 

import sqlite3
import os
import datetime

def create_or_load_db() -> sqlite3.Connection:
    if not os.path.exists(r"agent\.agent\persistance\memory.db"):
        con = sqlite3.connect(r"agent\.agent\persistance\memory.db")
        cur = con.cursor()

        cur.execute("CREATE TABLE IF NOT EXISTS memory (role TEXT, time TEXT, message TEXT)")
    
    return sqlite3.connect(r"agent\.agent\persistance\memory.db")

def write_to_memory(role, val):

    con = create_or_load_db()
    cur = con.cursor()
    cur.execute("INSERT INTO memory (role, time, message) VALUES (?, ?, ?)", (role, datetime.datetime.now(), val))
    con.commit()
    con.close()



 # ==== file path: agent\..\src\utils\files.py ==== 


import tomli
import asyncio
import os
import json
import fnmatch
from pathlib import Path
from typing import TypeVar, List, Optional

from src.utils.database import create_or_load_db

T = TypeVar('T')

def load_from_toml(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File '{path}' not found")
    
    with open(path, 'rb') as f:  # TOML files should be opened in binary mode for `tomli`
        data = tomli.load(f)

    return data


def read_to_string(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File '{path}' not found")
    
    with open(path, 'r') as f:
        data = f.read()

    return data

def load_from_json(file: Path) -> T:
    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_to_json(file: Path, val: T) -> None:
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(val, f, indent=4)

def ensure_dir(dir_path: Path) -> bool:
    if dir_path.is_dir():
        return False
    else:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True

def base_dir_exclude_globs(directory_path: Path, exclude_patterns=None):
    if exclude_patterns is None:
        exclude_patterns = ['.git*', 'target*']
    return get_glob_set(directory_path, exclude_patterns)

def get_glob_set(directory_path: Path, globs):
    matched_files = []
    for root, dirs, files in os.walk(directory_path):
        for file in files + dirs:
            full_path = Path(root) / file
            if any(fnmatch.fnmatch(str(full_path), pattern) for pattern in globs):
                matched_files.append(full_path)
    return matched_files

def bundle_to_file(files, dst_file):
    try:
        with open(dst_file, 'w', encoding='utf-8') as writer:

            for file_path in files:
                file_path = Path(file_path)

                if not file_path.is_file():
                    raise FileNotFoundError(f"File not found: {file_path}")
                
                with open(file_path, 'r', encoding='utf-8') as reader:
                    writer.write(f"\n # ==== file path: {file_path} ==== \n\n")

                    for line in reader:
                        writer.write(f"{line}")

                    writer.write("\n\n")

    except Exception as e:
        return f"An error occurred: {e}"
    
    return "Success"

def list_files(dir_path: Path, include_globs: Optional[List[str]] = None, exclude_globs: Optional[List[str]] = None) -> List[Path]:
    def is_match(path: Path, patterns: Optional[List[str]]) -> bool:
        if patterns is None:
            return True
        return any(fnmatch.fnmatch(str(path), pattern) for pattern in patterns)

    # Determine depth based on include globs (simplified approach)
    depth = 100 if include_globs and any("**" in glob for glob in include_globs) else 1

    matched_files = []
    for root, dirs, files in os.walk(dir_path):
        # Calculate current depth
        current_depth = len(Path(root).parts) - len(dir_path.parts)
        if current_depth > depth:
            # Stop diving into directories if max depth is exceeded
            del dirs[:]
            continue

        paths = [Path(root) / file for file in files]
        for path in paths:
            # Exclude directories or files based on exclude_globs
            if exclude_globs and is_match(path, exclude_globs):
                continue
            # Include files based on include_globs
            if is_match(path, include_globs):
                matched_files.append(path)
                
    return matched_files

def db_to_json():

    con = create_or_load_db()
    cur = con.cursor()

    cur.execute("SELECT * FROM memory")

    rows = cur.fetchall()

    data = {}

    for role, date, message in rows:
        if role not in data:
            data[role] = {}
        data[role][date] = {"message": message}

    con.close()

    with open(r"agent\.agent\persistance\memory.json", "w") as f:
        json.dump(data, f, indent=4)

def find(name, path=os.path.dirname(os.path.abspath(__file__))):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)

async def get_file_hashmap(client, asst_id: str):
    assts = client.beta.assistants
    assistant_files = assts.files.list(assistant_id=asst_id).data
    asst_file_ids = {file.id for file in assistant_files}

    org_files = client.files.list().data
    file_id_by_name = {org_file.filename: org_file.id for org_file in org_files if org_file.id in asst_file_ids}
    
    return file_id_by_name


 # ==== file path: agent\..\src\utils\tools.py ==== 

import spacy
import requests

from bs4 import BeautifulSoup


def get_context(string: str, tokens: list[str]):
    if not set(tokens).issubset({"TIME", "DATE", "GPE"}):
        raise ValueError("Invalid token; must be one of 'TIME', 'DATE', or 'GPE'")

    nlp = spacy.load("en_core_web_sm")

    try:
        doc = nlp(string)

        res = [ent.text for ent in doc.ents if ent.label_ in tokens]

        result = " ".join(res)

        return result
    
    except:
        return ""

def html_to_text(html: str, ignore_script_and_style: bool = True):
    soup = BeautifulSoup(html, "html.parser")
    
    # Optional: Remove script and style elements
    if ignore_script_and_style:
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
    
    # Get text
    text = soup.get_text()
    
    # Break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # Drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    return text

def web_parser(url: str):
    response = requests.get(url)
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Extract and print the text in a readable form
        # This removes HTML tags and leaves plain text
        return soup
    else:
        return f"Failed to retrieve the webpage. Status code: {response.status_code}"


 # ==== file path: agent\..\src\utils\__init__.py ==== 



