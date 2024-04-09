import asyncio
from dotenv import load_dotenv

from src.gui.app import ChatApp
from src.gui.cli import cli
from webapp.app import webapp


def main(mode="Web"):
    if mode.lower() not in ["web", "terminal", "cli"]:
        raise ValueError(
            "Invalid mode. Please choose either 'Web', 'Terminal', or 'CLI'."
        )
    load_dotenv()

    if mode.lower() == "terminal":
        gui = ChatApp()
        gui.run()

    elif mode.lower() == "web":
        wapp = webapp()
        asyncio.run(wapp)
    else:
        term = cli()
        asyncio.run(term)


if __name__ == "__main__":
    main()
