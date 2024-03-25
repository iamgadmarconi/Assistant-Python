# Assistant--Python

## Description

Assistant is a tool designed to simplify your daily tasks through natural language commands. This project leverages the power of advanced machine learning models to provide you with an interactive AI assistant capable of performing a variety of functions, whether you need the weather forecast, want to manage your calendar, handle your emails, or even interact with your files more intuitively.

Assistant offers a comprehensive suite of features that include but are not limited to:

 • Weather Reporting: Getting detailed weather forecasts for any location and time with a simple query.
 
 • Calendar Management: Viewing, creating, and managing calendar events. Ask about your schedule; the Assistant will keep you updated and organized.
 
 • Email Handling: Reading your most recent emails, composing new ones, attaching files, and sending them—all through natural language interactions.
 
 • File Exploration: Browsing and retrieving files with the myfiles browser makes managing documents easier without leaving the conversation. (WIP)
 
 • Personalized Assistance: Engaging in friendly, natural language conversations with the Assistant who can remember past interactions for a more personalized experience.
 

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Setup](#setup)
- [Contributing](#contributing)
- [License](#license)

## Installation

To get started with Assistant, follow these steps:

 1 Installation: Clone this repository to your local machine. Ensure you have the necessary environment to run Python code.
 
 2 Dependencies: Install all required dependencies by running pip install -r requirements.txt from the project's root directory.
 
 3 Configuration: Follow the instructions in the setup section below to set up your environment variables and any necessary API keys.
 
 4 Running The Assistant: Navigate to the source directory and execute main.py to start your assistant.
 
## Setup

This project requires you to provide several API keys for full functionality. These should be inserted into `.env`. You will need:
1. OpenAI API key. (Default model is gpt-4-turbo, change it in `agent.toml` to avoid high costs or if you don't have the model available

2. OpenWeather API key

3. Azure Client_ID
4. Azure Client_secret

For the last two keys, you have to create an application in Microsoft Azure for the Graph API, you can find detailed instructions on google, but for full functionality you need to enable the following permissions:
1. Mail (Read/Write)
2. Calendar (Read/Write)
3. Offline usage
4. etc. (WIP)

## Usage

Interacting with the Assistant is straightforward. After starting the assistant, simply type in your queries or commands, and the Assistant will respond accordingly.

 • For weather forecasts, try: "What's the weather like in Paris tomorrow?"
 
 • To check your calendar, ask: "Am I free next Monday?"
 
 • To manage emails, you could say: "Read my latest emails" or "Compose an email to John.Doe@outlook.com." (Contact support and name lookup WIP)
 

For a more detailed guide on how to use each feature, refer to the User Manual section. (WIP)

## Contributing

Guidelines for contributing to the project, including reporting issues and submitting pull requests.

## License

Information about the project's license.
