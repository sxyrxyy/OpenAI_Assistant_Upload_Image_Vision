from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def delete_all_openai_files():
    file_list = client.files.list()
    if len(file_list.data) == 0:
        print("No files found; nothing to delete.")
        return
    print('Files Found:')
    for file in file_list:
        print(f'Filename: {file.filename}\nID: {file.id}\n\n')

    response = input("Are you sure you want to delete ALL these files? (y/n): ").strip().lower()
    if response not in ("y", "yes"):
        print("Aborted. No files deleted.")
        return

    for file in file_list:
        deleted_info = client.files.delete(file.id)
        print(f"Deleted file: {file.filename} - {file.id}, response: {deleted_info}")
    print("\nAll files deleted!")


if __name__ == "__main__":
    # Make sure your OpenAI API key is set (e.g., via environment variable: OPENAI_API_KEY)
    delete_all_openai_files()