import os
import sqlite3

DB_DIR = os.path.abspath(os.path.dirname(__file__))
MIG_DIR = f'{DB_DIR}/migrations' 
conn = sqlite3.connect(f'{DB_DIR}/wordle.db')
with conn:
    cur = conn.cursor()
    for filename in os.listdir(MIG_DIR):
        f = os.path.join(MIG_DIR, filename)
        if os.path.isfile(f):
            with open(f, 'r') as sql_file:
                sql = sql_file.read()
            cur.execute(sql)