import sqlite3
import os
import datetime


def create_or_load_db() -> sqlite3.Connection:
    db_path = r"agent\.agent\persistance\memory.db"
    db_dir = os.path.dirname(db_path)

    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS memory (role TEXT, time TEXT, message TEXT)"
    )
    con.commit()

    return con


def write_to_memory(role, val):

    con = create_or_load_db()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO memory (role, time, message) VALUES (?, ?, ?)",
        (role, datetime.datetime.now(), val),
    )
    con.commit()
    con.close()
