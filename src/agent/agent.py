import os
import asyncio
import json
from aiofiles import open as aio_open
from pathlib import Path
from openai import OpenAI
from src.utils.files import load_from_toml, read_to_string, list_files, bundle_to_file, load_from_json, load_to_json, ensure_dir, db_to_json
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
            await upload_file_by_name(self.oac, asst_id=self.asst_id, filename=Path(r"agent\.agent\persistance\memory.json"), force=recreate)
        except:
            print("No previous memory")

        await self.upload_instructions()
        await self.upload_files(recreate)

        return self

    async def upload_instructions(self):
        file_path = os.path.join(self.dir, self.config["instructions_file"])
        if os.path.exists(file_path):
            async with aio_open(file_path, 'r') as file:
                inst_content = await file.read()
            await upload_instruction(self.oac, self.config, self.asst_id, inst_content)  # Assuming an async upload_instruction function
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
            src_dir = Path(self.dir).joinpath(bundle['src_dir'])

            if src_dir.is_dir():
                src_globs = bundle['src_globs']

                files = list_files(src_dir, src_globs, None)

                if files:
                    bundle_file_name = f"{self.name}-{bundle['bundle_name']}-{self.asst_id}.{bundle['dst_ext']}"
                    bundle_file = self.data_files_dir().joinpath(bundle_file_name)

                    force_reupload = recreate or not bundle_file.exists()

                    # Assuming bundle_to_file bundles files into the specified bundle_file
                    bundle_to_file(files, bundle_file)

                    _, uploaded = await upload_file_by_name(self.oac, self.asst_id, bundle_file, force_reupload)
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
            print(f"Conversation loaded")  

        except (FileNotFoundError, json.JSONDecodeError):
            thread_id = await create_thread(self.oac)
            print(f"Conversation created")  
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