import csv

import pandas as pd

from src.utils.files import get_file_hashmap, find


def findFile(client, asst_id, filename: str):

    file_id_by_name = get_file_hashmap(client, asst_id)
    
    file_id = file_id_by_name.get(filename, "File not found")

    return file_id

def csvWriter(filename:str, data: list):
    # path = find(filename)
    # with open(path, 'r', encoding='utf-8') as file:
    #     writer = csv.writer(file)
    # TODO: Implement csvWriter
    pass
