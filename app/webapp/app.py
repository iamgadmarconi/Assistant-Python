from quart import Quart, render_template, request, current_app
from werkzeug.utils import secure_filename
from src.agent.agent import Assistant
from src.ais.assistant import upload_file_by_name
from pathlib import Path
import asyncio
import os


get_bot_response = lambda x: "You said: \n" + x

app = Quart(__name__)
DEFAULT_DIR = "agent"
SAVE_DIRECTORY = r"app/files/documents"


@app.route("/")
async def home():
    return await render_template("chat.html")


@app.before_serving
async def initialize_agent():
    app.assistant = Assistant(DEFAULT_DIR)
    app.asst = await current_app.assistant.init_from_dir(False)
    app.conv = await current_app.assistant.load_or_create_conv(False)



@app.route("/chat", methods=["POST"])
async def chat():
    if request.method == "POST":
        form_data = await request.form
        message = form_data["message"]

        # Process the message and get the response
        response = await current_app.asst.chat(current_app.conv, message)
        # response = get_bot_response(message)  # testing
        # Return the response
        return response


def process_message(message):
    response = get_bot_response(message)
    return response


@app.route("/upload", methods=["GET", "POST"])
async def upload_file():
    if request.method == "POST":
        form_files = await request.files
        f = form_files["the_file"]
        file_path = os.path.join(SAVE_DIRECTORY, secure_filename(f.filename))
        await f.save(file_path)
        await upload_file_by_name(current_app.assistant.oac, current_app.assistant.asst_id, Path(file_path), force=True)

        return "File uploaded successfully", 200


def webapp():
    app.run(debug=False, use_reloader=True)
