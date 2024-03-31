import csv
import asyncio
import pandas as pd

from src.utils.files import get_file_hashmap, find


async def findFile(client, asst_id, filename: str):
    print(f"Debug--- Called findFile with parameters: {filename}")

    file_id_by_name = await get_file_hashmap(client, asst_id)
    
    file_id = file_id_by_name.get(filename, "File not found")

    return file_id

def csvWriter(filename:str, data: list):
    # path = find(filename)
    # with open(path, 'r', encoding='utf-8') as file:
    #     writer = csv.writer(file)
    # TODO: Implement csvWriter
    pass
