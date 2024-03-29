
from src.utils.files import get_file_hashmap

def findFile(client, asst_id, filename: str):

    file_id_by_name = get_file_hashmap(client, asst_id)
    
    file_id = file_id_by_name.get(filename, "File not found")

    return file_id