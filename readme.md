# Assistant--Python

## Description

Assistant is a tool designed to simplify your daily tasks through natural language commands. This project leverages the power of the OpenAI Assistants API to provide you with an interactive AI assistant capable of performing a variety of functions, whether you need the weather forecast, want to manage your calendar, handle your emails, or even interact with your files more intuitively.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Setup](#setup)
- [Contributing](#contributing)
- [License](#license)

## Installation

To get started with Assistant, follow these steps:

 1. Installation: Clone this repository to your local machine. Ensure you have the necessary environment to run Python code.

 2. Dependencies: Install all required dependencies by running pip install -r requirements.txt from the project's root directory.

 3. Configuration: Follow the instructions in the setup section below to set up your environment variables and any necessary API keys.

 4. Running The Assistant: Navigate to the source directory and run main.py to start your assistant.

## Setup

This project requires you to provide several API keys for full functionality. These should be inserted into `.env` in the root directory of the project. You will need:

1. OpenAI API key. (Default model is gpt-4-turbo, change it in `agent.toml` to avoid high costs or if you don't have the model available)
2. OpenWeather API key
3. Azure Client_ID
4. Azure Client_secret

You can copy and paste the following into `.env`

```text
OPENAI_API_KEY=sk-
OPENWEATHER_API_KEY=
CLIENT_ID=
CLIENT_SECRET=
CLIENT_SECRET_ID=
```

For the last two keys, you have to create an application in Microsoft Azure for the Graph API:

## Oauth Authentication

This section is explained using Microsoft Graph Protocol, almost the same applies to the Office 365 REST API.

### Authentication Steps

1. To allow authentication you first need to register your application at Azure App Registrations.

    1. Login at Azure Portal (App Registrations)

    2. Create an app. Set a name.

    3. In Supported account types choose "Accounts in any organizational directory and personal Microsoft accounts (e.g. Skype, Xbox, Outlook.com)", if you are using a personal account.

    4. Set the redirect uri (Web) to: <https://login.microsoftonline.com/common/oauth2/nativeclient> and click register. This needs to be inserted into the "Redirect URI" text box as simply checking the check box next to this link seems to be insufficent. This is the default redirect uri used by this library, but you can use any other if you want.

    5. Write down the Application (client) ID. You will need this value.

    6. Under "Certificates & secrets", generate a new client secret. Set the expiration preferably to never. Write down the value of the client secret created now. It will be hidden later on.

    7. Under Api Permissions:

        1. When authenticating "on behalf of a user":

            1. add the delegated permissions for Microsoft Graph you want (see scopes).

            2. It is highly recommended to add "offline_access" permission. If not the user you will have to re-authenticate every hour.

        2. When authenticating "with your own identity":

            1. add the application permissions for Microsoft Graph you want.

            2. Click on the Grant Admin Consent button (if you have admin permissions) or wait until the admin has given consent to your application.

2. For full support of all features, the following permissions are required:

    1. "<https://graph.microsoft.com/User.Read>"

    2. "<https://graph.microsoft.com/Calendars.ReadWrite>"

    3. "<https://graph.microsoft.com/Tasks.ReadWrite>"

    4. "<https://graph.microsoft.com/Mail.ReadWrite>"

    5. "<https://graph.microsoft.com/Contacts.ReadWrite>"

    6. "<https://graph.microsoft.com/Mail.Send>"

Granting the `offline_access` permission also makes it such that you don't have to refresh the token every hour.

## Usage

Interacting with the Assistant is straightforward. After starting the assistant, simply type in your queries or commands, and the Assistant will respond accordingly.

 -For weather forecasts, try: "What's the weather like in Paris tomorrow?"

 -To check your calendar, ask: "Am I free next Monday?"

 -To manage emails, you could say: "Read my latest emails" or "Write an email to <john.doe@outlook.com>."

 -If you want the assistant to interact with files, upload them in the `files` folder, you can ask for a file by its file name.

For a more detailed guide on how to use each feature, refer to the User Manual section. (WIP)

## Contributing

Guidelines for contributing to the project, including reporting issues and submitting pull requests.

## License

MIT License

Copyright (c) [2024] [Gad Marconi]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
