import os
import asyncio
import json
from aiofiles import open as aio_open
from pathlib import Path
from openai import OpenAI

from src.utils.files import (
    load_from_toml,
    list_files,
    bundle_to_file,
    load_from_json,
    load_to_json,
    ensure_dir,
    db_to_json,
)
from src.utils.cli import green_text, red_text, yellow_text
from src.ais.assistant import (
    load_or_create_assistant,
    upload_instruction,
    upload_file_by_name,
    get_thread,
    create_thread,
    run_thread_message,
)


class Assistant:
    """
    The Assistant class is used to represent an Assistant object.

    Attributes
    ----------
        dir: str
            The directory of the Assistant
        config: dict
            The configuration of the Assistant
        oac: OpenAI
            The OpenAI object
        asst_id: str
            The Assistant ID
        name: str
            The name of the Assistant

    Methods
    -------
        init_from_dir(recreate: bool = False)
            Initialize an agent from a directory
        upload_instructions()
            Upload the instructions file to the assignment
        upload_files(recreate: bool)
            Upload the files specified in the config file to the Assistant
        load_or_create_conv(recreate: bool)
            Load a conversation from the conv.json file, or create one if it doesn't exist
        chat(conv: dict, msg: str)
            Chat with the Assistant
        data_dir()
            Get the path to the data directory
        data_files_dir()
            Get the path to the data files directory
    """

    def __init__(self, directory: str) -> None:
        """
        Initialize the Assistant object.

        Parameters
        ----------
            self: Assistant
                Represent the instance of the class
            directory: str
                Set the value of self

        Returns
        -------

            None
        """
        self.dir = directory

    async def init_from_dir(self, recreate: bool = False):
        """
        The init_from_dir function is used to initialize an agent from a directory.

        Parameters
        ----------
            self
                Refer to the current object
            recreate: bool
                Determine whether the agent should be recreated or not

        Returns
        -------

            The agent object
        """
        self.config = load_from_toml(f"{self.dir}/agent.toml")
        self.oac = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.asst_id = await load_or_create_assistant(self.oac, self.config, recreate)
        self.name = self.config["name"]

        db_to_json()

        try:
            await upload_file_by_name(
                self.oac,
                asst_id=self.asst_id,
                filename=str(Path(r"agent\.agent\persistance\memory.json")),
                force=True,
            )
        except:
            # print("No previous memory")
            yellow_text("No previous memory")

        await self.upload_instructions()
        await self.upload_files(recreate)

        return self

    async def upload_instructions(self):
        """
        The upload_instructions function uploads the instructions file to the assignment.

        Parameters
        ----------
            self: Assistant
                Access the instance of the class

        Returns
        -------

            True if the file exists, and false otherwise
        """
        file_path = os.path.join(self.dir, self.config["instructions_file"])
        if os.path.exists(file_path):
            async with aio_open(file_path, "r") as file:
                inst_content = await file.read()
            await upload_instruction(self.oac, self.config, self.asst_id, inst_content)
            return True
        else:
            return False

    async def upload_files(self, recreate: bool) -> int:
        """
        The upload_files function uploads the files specified in the config file to the Assistant.

        Parameters
        ----------
            self: Assistant
                Refer to the object that is calling the method
            recreate: bool
                Determine if the file should be reuploaded

        Returns
        -------

            The number of files uploaded to the Assistant
        """
        num_uploaded = 0

        data_files_dir = self.data_files_dir()

        exclude_element = f"*{self.asst_id}*"

        for file in list_files(data_files_dir, ["*.rs", "*.md"], [exclude_element]):

            if ".agent" not in str(file):
                raise Exception(f"File '{file}' is not in data directory")

            os.remove(file)

        for bundle in self.config["file_bundles"]:
            # print(f"\n debug -- bundle: {bundle}\n")
            src_dir = Path(self.dir).joinpath(bundle["src_dir"])
            # print(f"\n debug -- src_dir: {src_dir}\n")
            if src_dir.is_dir():
                src_globs = bundle["src_globs"]

                files = list_files(src_dir, src_globs, None)

                # print(f"\n debug -- files: {files}\n")

                if files:

                    if bundle["bundle_name"] == "source-code":
                        bundle_file_name = f"{self.name}-{bundle['bundle_name']}-{self.asst_id}.{bundle['dst_ext']}"
                        bundle_file = self.data_files_dir().joinpath(bundle_file_name)
                        force_reupload = recreate or not bundle_file.exists()

                        bundle_to_file(files, bundle_file)
                        # print(f"\n debug -- bundle_file: {type(bundle_file)}\n")
                        _, uploaded = await upload_file_by_name(
                            self.oac, self.asst_id, bundle_file, force_reupload
                        )

                        if uploaded:
                            num_uploaded += 1
                    else:
                        for file in files:
                            if not str(file.name) == "conv.json":
                                _, uploaded = await upload_file_by_name(
                                    self.oac, self.asst_id, file.resolve(), False
                                )
                                if uploaded:
                                    num_uploaded += 1

        return num_uploaded

    async def load_or_create_conv(self, recreate: bool) -> dict:
        """
        The load_or_create_conv function is used to load a conversation from the conv.json file, or create one if it doesn't exist.
        The function takes in a boolean value called recreate which determines whether or not the conv.json file should be deleted and recreated.

        Parameters
        ----------
            self: Assistant
                Refer to the class itself
            recreate: bool
                Determine whether to recreate the conversation or not

        Returns
        -------

            A dictionary with the key 'thread_id' and a value of thread_id
        """
        conv_file = Path(self.data_dir()).joinpath("conv.json")

        if recreate and conv_file.exists():
            os.remove(conv_file)  # Removes the file

        try:
            conv = load_from_json(conv_file)
            await get_thread(self.oac, conv["thread_id"])
            # print(f"Conversation loaded")
            green_text(f"Conversation loaded")

        except (FileNotFoundError, json.JSONDecodeError):
            thread_id = await create_thread(self.oac)
            # print(f"Conversation created")
            green_text(f"Conversation created")
            conv = {"thread_id": thread_id}
            load_to_json(conv_file, conv)

        return conv

    async def chat(self, conv: dict, msg: str) -> str:
        """
        The chat function is a coroutine that takes in a conversation and message,
        and returns the response from the Assistant.

        Parameters
        ----------
            self: Assistant
                Access the attributes and methods of the class
            conv: dict:
                Get the thread_id of the conversation
            msg: str
                Pass the message to be sent

        Returns
        -------

            A string containing the response from the Assistant
        """
        res = await run_thread_message(self.oac, self.asst_id, conv["thread_id"], msg)
        return res

    def data_dir(self) -> Path:
        """
        The data_dir function returns the path to the data directory, ensuring its existence.

        Parameters
        ----------
            self: Assistant
                Represent the instance of the class

        Returns
        -------

            The path to the data directory, ensuring its existence
        """
        data_dir = Path(self.dir + r"\.agent")
        ensure_dir(data_dir)
        return data_dir

    def data_files_dir(self) -> Path:
        """
        The data_files_dir function returns the path to the data files directory within the data directory, ensuring its existence.

        Parameters
        ----------
            self: Assistant
                Represent the instance of the class

        Returns
        -------

            The path to the data files directory within the data directory, ensuring its existence
        """
        files_dir = self.data_dir().joinpath("files")
        ensure_dir(files_dir)
        return files_dir
