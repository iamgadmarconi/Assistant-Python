# def pretty_print(messages):
#     print(messages)
#     for m in messages:
#         print(f"{m.role}: {m.content[0].text.value}")
#     print("\n")

# def pretty_print(messages):
#     m = messages
#     # print(f"{m.role}: {m.content[0].text.value}")
#     # print("\n")
#     print(m)

# def get_text_content(messages):
#     msg_content = [m.content[0].text.value for m in messages]
    
#     if not msg_content:
#         return "No messages found"

#     return msg_content

class CreateMessageRequest:
    def __init__(self, role, content, **kwargs):
        self.role = role
        self.content = content
        for key, value in kwargs.items():
            setattr(self, key, value)

class MessageContentText:
    def __init__(self, text):
        self.text = text

class MessageContentImageFile:
    pass

class MessageObject:
    def __init__(self, content):
        self.content = content

def user_msg(content):
    return CreateMessageRequest(
        role="user",
        content=str(content),  # Converts the content into a string
    )

def get_text_content(msg):
    if not msg.content:
        raise ValueError("No content found in message")

    msg_content = next(iter(msg.content), None)

    if msg_content is None:
        raise ValueError("No content found in message")

    if isinstance(msg_content.text.value, str):
        return msg_content.text.value
    else:
        raise ValueError("Unsupported message content type")
