import re
import base64

from io import BytesIO
from PIL import Image


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


def get_text_content(client, msg):
    if not msg.content:
        raise ValueError("No content found in message")

    msg_content = next(iter(msg.content), None)

    if msg_content is None:
        raise ValueError("No content found in message")

    if hasattr(msg_content, "image_file"):
        file_id = msg_content.image_file.file_id
        resp = client.files.with_raw_response.retrieve_content(file_id)
        if resp.status_code == 200:
            image_data = BytesIO(resp.content)
            img = Image.open(image_data)
            img.show()

    msg_file_ids = next(iter(msg.file_ids), None)

    if msg_file_ids:
        file_data = client.files.content(msg_file_ids)
        file_data_bytes = file_data.read()
        with open("files", "wb") as file:
            file.write(file_data_bytes)

    message_content = msg_content.text
    annotations = message_content.annotations
    citations = []
    for index, annotation in enumerate(annotations):
        # Replace the text with a footnote
        message_content.value = message_content.value.replace(
            annotation.text, f" [{index}]"
        )

        # Gather citations based on annotation attributes
        if file_citation := getattr(annotation, "file_citation", None):
            cited_file = client.files.retrieve(file_citation.file_id)
            citations.append(
                f"[{index}] {file_citation.quote} from {cited_file.filename}"
            )
        elif file_path := getattr(annotation, "file_path", None):
            cited_file = client.files.retrieve(file_path.file_id)
            citations.append(
                f"[{index}] Click <here> to download {cited_file.filename}"
            )
            # Note: File download functionality not implemented above for brevity

    # Add footnotes to the end of the message before displaying to user
    message_content.value += "\n" + "\n".join(citations)

    if isinstance(msg_content.text.value, str):
        txt = msg_content.text.value
        # print(f"\n\ndebug --Text content: {txt}\n\n")
        pattern = r"\[bytes](.*?)\[/bytes]"
        # Find all occurrences of the pattern
        decoded_bytes_list = []
        text_parts = re.split(pattern, txt)  # Split the string into parts

        # Iterate over the split parts, decoding where necessary
        for i, part in enumerate(text_parts):
            if i % 2 != 0:  # The pattern is expected to capture every second element
                # Decode and store the bytes
                decoded_bytes = base64.b64decode(part)
                decoded_bytes_list.append(decoded_bytes)
                # Replace the original encoded string with a placeholder or remove it
                text_parts[i] = ""  # Remove or replace with a placeholder as needed

        # Reassemble the textual content without the encoded bytes
        textual_content = "".join(text_parts)
        # print(f"\n\nDecoded bytes: {decoded_bytes_list}\n\n")
        for resp in decoded_bytes_list:
            image_data = BytesIO(resp)
            img = Image.open(image_data)
            img.show()

        if len(citations) > 0:
            textual_content += "\n" + "\n".join(citations)

        return textual_content

    else:
        raise ValueError("Unsupported message content type")
