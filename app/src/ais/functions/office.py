import csv
import asyncio
import pandas as pd

from src.utils.files import get_file_hashmap, find


async def findFile(client, asst_id, filename: str) -> str:
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
    print(f"Debug--- Called findFile with parameters: {filename}")

    file_id_by_name = await get_file_hashmap(client, asst_id)

    file_id = file_id_by_name.get(filename, "File not found")

    print(f"Debug--- File ID: {file_id}")

    return file_id


def csvWriter(filename: str, data: list):
    # path = find(filename)
    # with open(path, 'r', encoding='utf-8') as file:
    #     writer = csv.writer(file)
    # TODO: Implement csvWriter
    pass
