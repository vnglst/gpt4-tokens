import sqlite3

def display_processed_tokens(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM processed_tokens")
    records = cursor.fetchall()

    for record in records:
        print(record)

    conn.close()

display_processed_tokens('processed_tokens.db')

