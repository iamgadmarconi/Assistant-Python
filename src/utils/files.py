
import tomli
import os
import json
import fnmatch
from pathlib import Path
from typing import TypeVar, Generic, List, Optional
from src.utils.database import create_or_load_db

T = TypeVar('T')

def load_from_toml(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File '{path}' not found")
    
    with open(path, 'rb') as f:  # TOML files should be opened in binary mode for `tomli`
        data = tomli.load(f)

    return data


def read_to_string(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File '{path}' not found")
    
    with open(path, 'r') as f:
        data = f.read()

    return data

def load_from_json(file: Path) -> T:
    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_to_json(file: Path, val: T) -> None:
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(val, f, indent=4)

def ensure_dir(dir_path: Path) -> bool:
    if dir_path.is_dir():
        return False
    else:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True

def base_dir_exclude_globs(directory_path: Path, exclude_patterns=None):
    if exclude_patterns is None:
        exclude_patterns = ['.git*', 'target*']
    return get_glob_set(directory_path, exclude_patterns)

def get_glob_set(directory_path: Path, globs):
    matched_files = []
    for root, dirs, files in os.walk(directory_path):
        for file in files + dirs:
            full_path = Path(root) / file
            if any(fnmatch.fnmatch(str(full_path), pattern) for pattern in globs):
                matched_files.append(full_path)
    return matched_files

def bundle_to_file(files, dst_file):
    try:
        with open(dst_file, 'w', encoding='utf-8') as writer:

            for file_path in files:
                file_path = Path(file_path)

                if not file_path.is_file():
                    raise FileNotFoundError(f"File not found: {file_path}")
                
                with open(file_path, 'r', encoding='utf-8') as reader:
                    writer.write(f"\n # ==== file path: {file_path} ==== \n\n")

                    for line in reader:
                        writer.write(f"{line}")

                    writer.write("\n\n")

    except Exception as e:
        return f"An error occurred: {e}"
    
    return "Success"

def list_files(dir_path: Path, include_globs: Optional[List[str]] = None, exclude_globs: Optional[List[str]] = None) -> List[Path]:
    def is_match(path: Path, patterns: Optional[List[str]]) -> bool:
        if patterns is None:
            return True
        return any(fnmatch.fnmatch(str(path), pattern) for pattern in patterns)

    # Determine depth based on include globs (simplified approach)
    depth = 100 if include_globs and any("**" in glob for glob in include_globs) else 1

    matched_files = []
    for root, dirs, files in os.walk(dir_path):
        # Calculate current depth
        current_depth = len(Path(root).parts) - len(dir_path.parts)
        if current_depth > depth:
            # Stop diving into directories if max depth is exceeded
            del dirs[:]
            continue

        paths = [Path(root) / file for file in files]
        for path in paths:
            # Exclude directories or files based on exclude_globs
            if exclude_globs and is_match(path, exclude_globs):
                continue
            # Include files based on include_globs
            if is_match(path, include_globs):
                matched_files.append(path)
                
    return matched_files

def db_to_json():

    con = create_or_load_db()
    cur = con.cursor()

    cur.execute("SELECT * FROM memory")

    rows = cur.fetchall()

    data = {}

    for role, date, message in rows:
        if role not in data:
            data[role] = {}
        data[role][date] = {"message": message}

    con.close()

    with open(r"agent\.agent\persistance\memory.json", "w") as f:
        json.dump(data, f, indent=4)