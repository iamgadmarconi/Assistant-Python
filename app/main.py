import asyncio
from dotenv import load_dotenv

from src.gui.app import ChatApp
from src.gui.cli import cli


def main(mode=False):
    load_dotenv()
    term = cli()
    gui = ChatApp()

    if mode:
        gui.run()

    else:
        asyncio.run(term)


if __name__ == "__main__":
    main()
