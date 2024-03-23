import asyncio

from typing import Union

from src.agent.agent import Assistant
from src.utils.cli import asst_msg


DEFAULT_DIR = "agent"

class Cmd:

    Quit = "Quit"
    RefreshAll = "RefreshAll"
    RefreshConv = "RefreshConv"
    RefreshInst = "RefreshInst"
    RefreshFiles = "RefreshFiles"
    Chat = "Chat"

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
        else:
            return f"{cls.Chat}: {input_str}"

async def cli():
    assistant = Assistant(DEFAULT_DIR)
    asst = await assistant.init_from_dir(False)
    conv = await assistant.load_or_create_conv(False)

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

