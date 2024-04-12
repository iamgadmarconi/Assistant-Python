import csv
import asyncio
import pandas as pd
from typing import Optional

from src.utils.files import get_file_hashmap, find


async def findFile(client, asst_id, filename: Optional[str] = None) -> str:
    """
    The findFile function takes in a filename and returns the file_id of that file.
        If the file is not found, it will return 'File not found'.

    Parameters
    ----------
        client
            Access the database
        asst_id
            Get the assignment id
        filename: str
            Specify the name of the file that you want to find

    Returns
    -------

        The file_id of the file with name filename
    """
    print(f"\nDebug--- Called findFile with parameters: {filename}\n")

    if filename:
        file_id_by_name = await get_file_hashmap(client, asst_id)

        file_id = file_id_by_name.get(filename, "File not found")

    else:
        org_files = client.files.list().data
        most_recent_file = sorted(
            org_files, key=lambda x: x["created_at"], reverse=True
        )[0]
        file_id = most_recent_file["id"]

        assts = client.beta.assistants
        assistant_files = assts.files.list(assistant_id=asst_id).data
        asst_file_ids = {file.id for file in assistant_files}

        if not file_id in asst_file_ids:
            file_id = "File exists but not in assistant's files."

    print(f"\nDebug--- File ID: {file_id}\n")

    return file_id


def csvWriter(filename: str, data: list):
    # path = find(filename)
    # with open(path, 'r', encoding='utf-8') as file:
    #     writer = csv.writer(file)
    # TODO: Implement csvWriter
    pass
