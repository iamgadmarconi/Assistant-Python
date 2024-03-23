from rich.console import Console
from rich.text import Text
from rich.markdown import Markdown


def asst_msg(content):
    console = Console()
    markdown = Markdown(content)
    console.print(markdown, style="cyan")

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

