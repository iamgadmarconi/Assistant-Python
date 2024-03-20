import asyncio
import backoff
from time import sleep
from openai import NotFoundError
import json
import os
import re

from src.ais.msg import get_text_content, user_msg
from src.utils.database import write_to_memory
from src.utils.files import find

from ais.functions.azure import getCalendar, readEmail, writeEmail, sendEmail
from ais.functions.misc import getWeather


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
        print(f"Assistant '{config['name']}' deleted")

    if asst_id is not None:
        print(f"Assistant '{config['name']}' loaded")
        return asst_id
    
    else:
        asst_obj = await create(client, config)
        print(f"Assistant '{config['name']}' created")
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
        print(f"Instructions uploaded to assistant '{config['name']}'")

    except Exception as e:
        print(f"Failed to upload instruction: {e}")
        raise  

async def delete(client, asst_id: str):
    assts = client.beta.assistants 
    assistant_files = client.files

    file_hashmap = await get_file_hashmap(client, asst_id)

    for file_id in file_hashmap.values():
        del_res = assistant_files.delete(file_id)

        if del_res.deleted:
            print(f"File '{file_id}' deleted")

    for key in file_hashmap.keys():
        path = find(key, "agent")
        if os.path.exists(path):
            os.remove(path)

    try:
        if os.path.exists(find("memory.json", "agent")):
            os.remove(find("memory.json", "agent"))
    except:
        pass
    
    try:
        if os.path.exists(find("memory.db", "agent")):
            os.remove(find("memory.db", "agent"))
    except:
        pass

    assts.delete(assistant_id=asst_id)
    print(f"Assistant deleted")

async def get_file_hashmap(client, asst_id: str):
    assts = client.beta.assistants
    assistant_files = assts.files.list(assistant_id=asst_id).data
    asst_file_ids = {file.id for file in assistant_files}

    org_files = client.files.list().data
    file_id_by_name = {org_file.filename: org_file.id for org_file in org_files if org_file.id in asst_file_ids}
    
    return file_id_by_name

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

    _message_obj = threads.messages.create(
        thread_id=thread_id,
        content=message,
        role="user",
    )

    try:

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

    while True:
            print("-", end="", flush=True)
            run = threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

            if run.status in ["Completed", "completed"]:
                print("\n")
                return await get_thread_message(client, thread_id)
            elif run.status in ["Queued", "InProgress", "run_in_progress", "in_progress", "queued"]:
                pass  

            elif run.status in ['pending', 'Pending']:
                pass
            elif run.status in ['requires_input', 'RequiresInput', 'requires_action', 'RequiresAction']:
                await call_required_function(client, thread_id, run.id, run.required_action)
            else:
                print("\n") 
                await delete(client, asst_id)
                raise Exception(f"Unexpected run status: {run.status}")

            sleep(0.5)

async def call_required_function(client, thread_id: str, run_id: str, required_action):
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
                    message = args.get("message", None),
                    subject = args.get("subject", None),
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
                    message = args.get("message", None)
                )
                tool_outputs.append(
                    {
                        "tool_call_id": action[1].tool_calls[0].id,
                        "output": outputs
                    }
                )

            else:
                raise ValueError(f"Function '{func_name}' not found")

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
        txt = get_text_content(msg)

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
            print(f"File '{filename}' already uploaded")
            return file_id, False
    
    if file_id:
        try:
            assistant_files.delete(file_id)

        except Exception as e:
            print(f"Failed to delete file '{filename}': {e}")
            raise

        try:
            assts.files.delete(
                assistant_id=asst_id,
                file_id=file_id,
            )
        
        except Exception as e:
            print(f"Couldn't remove assistant file '{filename}': {e}")
            raise

    with open(filename, "rb") as file:
        uploaded_file = client.files.create(
            file=file,
            purpose="assistants",
        )

    assistant_files.create(
        assistant_id=asst_id,
        file_id=uploaded_file.id,
    )

    print(f"File '{filename}' uploaded")
    return uploaded_file.id, True

