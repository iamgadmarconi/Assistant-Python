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
