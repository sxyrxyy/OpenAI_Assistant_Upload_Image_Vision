import asyncio
import os
import time
from dotenv import load_dotenv
import json
import httpx
import aiofiles
from typing import Optional

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

HEADERS = {
    "OpenAI-Beta": "assistants=v2",
    "Authorization": f"Bearer {api_key}"
}
BASE_URL = "https://api.openai.com/v1"


async def create_thread(messages: list[dict]) -> dict:
    url = f"{BASE_URL}/threads"
    body = {"messages": messages}

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=HEADERS, json=body)
        response.raise_for_status()
        return response.json()


async def upload_file(file_path: str, purpose="vision") -> dict:
    url = f"{BASE_URL}/files"
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with aiofiles.open(file_path, "rb") as f:
            file_content = await f.read()

        files = {
            "file": (os.path.basename(file_path), file_content),
            "purpose": (None, purpose),
        }

        response = await client.post(url, headers=HEADERS, files=files)
        response.raise_for_status()
        return response.json()


async def create_message(thread_id: str, role: str, content) -> dict:
    url = f"{BASE_URL}/threads/{thread_id}/messages"
    print(f'Message URL: {url}')
    body = {
        "role": role,
        "content": content
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=HEADERS, json=body)
        response.raise_for_status()
        return response.json()


async def run_thread(thread_id: str, assistant_id: str) -> dict:
    url = f"{BASE_URL}/threads/{thread_id}/runs"
    print(f'Run Thread URL: {url}')
    body = {"assistant_id": assistant_id}
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=HEADERS, json=body)
        response.raise_for_status()
        return response.json()


async def fetch_latest_assistant_message(thread_id: str) -> Optional[dict]:
    url = f"{BASE_URL}/threads/{thread_id}/messages"
    print(f'Fetch Messages URL: {url}')
    params = {
        "limit": 10,
        "order": "desc"
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

    messages = data.get("data", [])
    for msg in messages:
        if msg.get("role") == "assistant":
            return msg
    return None


async def delete_last_file(file_id: str) -> Optional[dict]:
    url = f"{BASE_URL}/files/{file_id}"
    print(f'Last File URL: {url}')
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.delete(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()


async def delete_thread(thread_id: str) -> dict:
    url = f"{BASE_URL}/threads/{thread_id}"
    print(f'Thread URL: {url}')
    async with httpx.AsyncClient() as client:
        response = await client.delete(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()


async def main():
    # 1) Upload the image
    file_path = "my_image.png"  # Replace with your actual local file
    print("Uploading file...")
    file_response = await upload_file(file_path)
    file_id = file_response["id"]
    print("File uploaded with ID:", file_id)

    # Create thread
    print("Creating a new thread...")
    initial_messages = [
        {
            "role": "user",
            "content": "Hello!"
        }
    ]
    new_thread = await create_thread(initial_messages)
    thread_id = new_thread["id"]
    print(f"New thread created with ID: {thread_id}")

    # 2) Create a user message in the existing thread referencing the image
    content = [
        {"type": "text", "text": "Picture:"},
        {"type": "image_file", "image_file": {"file_id": file_id, "detail": "auto"}}
    ]
    print(f"\nPosting user message to thread: {thread_id}")
    message_response = await create_message(thread_id, role="user", content=content)
    print("User message created. Message ID:", message_response["id"])

    # 3) Run the thread with your assistant
    assistant_id = ASSISTANT_ID
    print("\nRunning the thread to generate assistant response...")
    run_response = await run_thread(thread_id, assistant_id)
    time.sleep(5)
    # print("Thread run response:")
    # print(json.dumps(run_response, indent=2))

    latest_assistant_msg = await fetch_latest_assistant_message(thread_id)
    if latest_assistant_msg is not None:
        # print("\nAssistant’s Latest Reply:")
        # print(json.dumps(latest_assistant_msg["content"], indent=2))
        content = latest_assistant_msg.get("content", [])

        text_item = next(
            (item for item in content if item.get("type") == "text"),
            None
        )

        if text_item is not None:
            value = text_item["text"]["value"]
            print("Assistant's text value:", value)
            delete_thread_info = await delete_thread(thread_id)
            print("Delete Thread:", delete_thread_info)
        else:
            print("No text item found in assistant content.")
            delete_thread_info = await delete_thread(thread_id)
            print("Delete Thread:", delete_thread_info)
    else:
        print("No assistant message found.")
        delete_thread_info = await delete_thread(thread_id)
        print("Delete Thread:", delete_thread_info)

    delete_thread_info = await delete_thread(thread_id)
    print("Delete Thread:", delete_thread_info)

    delete_last_file_info = await delete_last_file(file_id)
    print("Delete File:", delete_last_file_info)


if __name__ == "__main__":
    asyncio.run(main())