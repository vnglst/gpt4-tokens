import json
import requests

system_prompt = """
Can you categorize the following list of tokens into predefined interest areas: programming languages (such as Python, JavaScript abbreviated as "js", C#, etc.), general coding contexts, English language words as 'en', 'es', 'de', 'nl', other languages abbreviated with their specific name. Characters (abbreviated as "char") with their language 'en', 'fr', etc. If the token is a language, specify if it's a "noun", "proper noun", "verb or "adj", etc. If it's a proper noun specify if it's a well known "brand" or "person". The categorization should specify which areas each token belongs to. Try to provide always at least 3 tags. The results should be presented in a JSON structure that clearly defines categories for each token. Here’s an example of how to structure this JSON:

```json
{
  "liability": ["lang", "en", "noun"],
  "beam": ["lang", "en", "noun"],
  "NotFound": ["comp", "js"],
  "harvest": ["lang", "en", "noun", "verb"],
  "Charles": ["lang", "en", "proper noun", "person"],
  ".SequentialGroup": ["code", "python"],
  "олько": ["lang", "ru"],
  "_person": ["code", "python"],
  ".history": ["code", "python", "js"],
  "TextView": ["code", "java", "c#"],
  "PDF": ["code", "js", "c#"],
  "kar": ["char"],
  "__": ["code", "python"],
  ":": ["char"],
  "_messages": ["code", "general"],
  "ís": ["char", "es"],
}
```

Do a linguistic analysis of each token the following tokens. Respond with only JSON. Nothing more.

"""


def process_tokens(tokens):
    url = "http://localhost:11434/api/generate"

    prompt = system_prompt + "\n" + "\n".join(tokens)

    data = {
        "model": "llama3",
        # "model": "gemma:2b",
        "prompt": prompt,
        "stream": False
    }

    print(f"Processing: {tokens}")

    response = requests.post(url, json=data, timeout=1000)

    if response.status_code == 200:
        try:
            print(f"JSON: {response.json()['response']}")
            return response.json()['response']
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON: {e}")
            print(f"Response: {response.text}")
            return []

    print(f"Request failed with status code {response.status_code}")
    return []


def process_large_file(file_path, batch_size=5):
    results = {"tokens": {}}
    with open(file_path, 'r', encoding='utf-8') as file:
        while True:
            lines = [file.readline().strip() for _ in range(batch_size)]
            if not lines[0]:
                break
            processed = process_tokens(lines)
            results["tokens"].update(processed)
    return results


def write_to_json(data, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)


tokens_batch = process_large_file('gpt-4-tokens.txt')
write_to_json(tokens_batch, 'processed_tokens.json')
