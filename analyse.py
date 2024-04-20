import json
import sqlite3
from datetime import datetime
import requests

INPUT_FILE = 'cl100k_base.txt'
DATABASE_FILE = 'tokens.db'


def now():
    return datetime.now().strftime('%H:%M:%S')


def process_tokens(tokens: list):

    with open("template.txt", "r", encoding='utf-8') as f:
        template = f.read()

    llm_url = "http://localhost:11434/api/generate"
    prompt = f"{template}\n\n" + "\n".join(tokens)

    generation_request = {
        "model": "llama3:instruct",
        # Phi3 is faster, but less accurate, reliable
        # "model": "phi3:instruct",
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {
            "seed": 123,
            "temperature": 0
        }
    }

    print(f"[{now()}] Processing: {tokens}")

    try:
        response = requests.post(
            llm_url, json=generation_request, timeout=1000)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Request failed with error: {e}")
        return

    try:
        json_response = response.json()
        response = json.loads(json_response["response"])
        return response
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Failed to decode LLM response JSON: {e}")
        print(f"Response: {response.text}")
        return


def write_tokens_to_database(file_path, database_path):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS tokens (id INTEGER PRIMARY KEY AUTOINCREMENT, token TEXT UNIQUE, type TEXT, lang TEXT, definition TEXT)""")

    with open(file_path, 'r', encoding='utf-8') as file:

        for token in file:
            token = token.strip()
            if token == "":
                # don't write any empty tokens
                continue

            cursor.execute(
                "INSERT OR IGNORE INTO tokens (token) VALUES (?)", (token,))

        conn.commit()
        count = len(cursor.execute('SELECT * FROM tokens').fetchall())
        print(f"[{now()}] Written {count} tokens to database")

    conn.close()


def status_update(database_path):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM tokens")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tokens WHERE type IS NULL")
    todo = cursor.fetchone()[0]
    percentage = round((total - todo) / total * 100)

    print(f"[{now()}] Tokens processed: {todo} / {total} ({percentage}% done)")
    conn.close()


def process_batch(database_path):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT token FROM tokens WHERE type IS NULL ORDER BY RANDOM() LIMIT 20")
    tokens = [row[0] for row in cursor.fetchall()]

    processed = process_tokens(tokens)

    for token, item in processed.items():
        try:
            print(f"[{now()}] '{token}' ---> {item}")
            cursor.execute("UPDATE tokens SET type = ?, lang = ?, definition = ? WHERE token = ?",
                           (item['type'], item['lang'], item["definition"], token))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error updating {token}: {e}")

    conn.close()


write_tokens_to_database(INPUT_FILE, DATABASE_FILE)

while True:
    try:
        status_update(DATABASE_FILE)
        process_batch(DATABASE_FILE)
    except Exception as error:
        print(f"Failed to process batch: {error}")
