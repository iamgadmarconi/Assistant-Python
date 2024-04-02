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
    help_message_2 = Text("\n    - '/h' : Display this help menu", style="")
    help_message_3 = Text("\n    - '/q' : Quit the program", style="")
    help_message_4 = Text("\n    - '/r' : Recreate the assistant", style="")
    help_message_5 = Text("\n    - '/ra' : Refresh all data", style="")
    help_message_6 = Text("\n    - '/rc' : Refresh the conversation", style="")
    help_message_7 = Text("\n    - '/ri' : Refresh the instructions", style="")
    help_message_8 = Text("\n    - '/rf' : Refresh the files", style="")
    help_message_9 = Text("\n    - '/c' : Clear the screen", style="")
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