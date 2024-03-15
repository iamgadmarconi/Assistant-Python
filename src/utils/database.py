import sqlite3
import os
import datetime

def create_or_load_db() -> sqlite3.Connection:
    if not os.path.exists(r"agent\.agent\persistance\memory.db"):
        con = sqlite3.connect(r"agent\.agent\persistance\memory.db")
        cur = con.cursor()

        cur.execute("CREATE TABLE IF NOT EXISTS memory (role TEXT, time TEXT, message TEXT)")
    
    return sqlite3.connect(r"agent\.agent\persistance\memory.db")

def write_to_memory(role, val):

    con = create_or_load_db()
    cur = con.cursor()
    cur.execute("INSERT INTO memory (role, time, message) VALUES (?, ?, ?)", (role, datetime.datetime.now(), val))
    con.commit()
    con.close()
