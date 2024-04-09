from quart import Quart, render_template, request, current_app
from src.agent.agent import Assistant
import asyncio

get_bot_response = lambda x: "You said: " + x

app = Quart(__name__)
DEFAULT_DIR = "agent"


@app.route("/")
async def home():
    return await render_template("chat.html")

@app.before_serving
async def initialize_agent():
    assistant = Assistant(DEFAULT_DIR)
    asst = await assistant.init_from_dir(False)
    conv = await assistant.load_or_create_conv(False)
    app.asst = asst
    app.conv = conv

@app.route("/chat", methods=["POST"])
async def chat():
    if request.method == 'POST':
        form_data = await request.form
        message = form_data['message']
        
        # Process the message and get the response
        response = await current_app.asst.chat(current_app.conv, message)
        # Return the response
        return response

def process_message(message):
    response = get_bot_response(message)
    return response

@app.route('/upload', methods=['GET', 'POST'])
async def upload_file():
    if request.method == 'POST':
        form_files = await request.files
        f =  form_files['the_file']
        # f.save('/var/www/uploads/uploaded_file.txt')



def webapp():
    app.run(debug=True)