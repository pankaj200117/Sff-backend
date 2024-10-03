import os
import httpx

async def search_instrumental_tracks(prompt: str) -> dict:
    """
    Search for instrumental tracks using the Reprtoir API.
    """
    url = f"https://reprtoir.io/api/tracks/search?search_mode=prompt&query={prompt}&sort_field=_score&sort_order=desc&page=1&per_page=10"

    payload = { "instrumental": True }
    
    headers = {
        "X-API-Key": os.getenv("REPRTOIR_API_KEY"),
        "accept": "application/json",
        "content-type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
    return response.json()

# Example usage
prompt = "instrumental song"
print(search_instrumental_tracks(prompt))
