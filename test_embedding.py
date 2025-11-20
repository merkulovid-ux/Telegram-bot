import httpx
import json
import os

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

async def test_embedding_api():
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "x-folder-id": YANDEX_FOLDER_ID,
    }
    body = {
        "modelUri": f"emb://{YANDEX_FOLDER_ID}/text-search-doc/latest",
        "text": "test text for embedding",
    }

    print(f"Sending request to: {url}")
    print(f"Headers: {headers}")
    print(f"Body: {json.dumps(body, indent=2)}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            print(f"API Response Status: {response.status_code}")
            print(f"API Response Body: {response.text}")
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print(f"Request error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {repr(e)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_embedding_api())