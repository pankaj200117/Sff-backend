from configs import config
import httpx
from typing import List, Dict
import requests
import os
import aiofiles


async def generate_audio_by_prompt(prompt: str, make_instrumental: bool = True, wait_audio: bool = True,
                                   save_audio: bool = False) -> List[Dict[str, str]]:
    """
    Generate audio using the Suno API.

    Args:
        prompt (str): The prompt to generate audio.
        make_instrumental (bool): Whether to make the audio instrumental or not.
        wait_audio (bool): Whether to wait for the audio to be generated or not.
        save_audio (bool): Whether to save the audio files or not.
    
    Returns:
        List[Dict[str, str]]: A list of dictionaries containing the title and audio URL of the generated audio.
    """
    payload = {
        "prompt": prompt, 
        "make_instrumental": make_instrumental,
        "wait_audio": wait_audio
    }
    url = config.SUNO_API_APP_URL + "/api/generate"

    async with httpx.AsyncClient(timeout=100) as client:
        suno_api_response = await client.post(url, json=payload, headers={'Content-Type': 'application/json'})
    suno_api_response = suno_api_response.json()
    
    audio_urls = []
    if save_audio:
        audio_urls = [
            download_audio(audio["audio_url"], os.path.join(config.TEMP_PATH, f"{audio['title']} {i + 1}.mp3")) 
            for i, audio in enumerate(suno_api_response)
        ]
    else:
        audio_urls = [audio["audio_url"] for audio in suno_api_response]

    response = [
        {"title": f"{song['title']} {i + 1}", "audio_url": audio_urls[i]} for i, song in enumerate(suno_api_response)
    ]

    return response


async def get_quota_information():
    """
    Get the quota information for the Suno API.

    Returns:
        Dict: A dictionary containing the quota information.
    """
    url = config.SUNO_API_APP_URL + "/api/get_limit"

    async with httpx.AsyncClient() as client:
        quota_response = await client.get(url)

    return quota_response.json()


# def download_audio(url: str, path: str) -> str:
#     """
#     Download an audio file from a URL.

#     Args:
#         url (str): The URL of the audio file.
#         path (str): The path to save the audio file.
    
#     Returns:
#         str: The local file path where the audio was saved.
#     """
#     response = requests.get(url, stream=True)

#     if response.status_code == 200:
#         with open(path, "wb") as audio_file:
#             for chunk in response.iter_content(chunk_size=8192):  # 8KB chunks
#                 if chunk:  # Filter out keep-alive new chunks
#                     audio_file.write(chunk)
#         return path
    
#     raise Exception("Failed to download audio: " + url)

async def download_audio(url: str, path: str) -> str:
    """
    Asynchronously download an audio file from a URL.

    Args:
        url (str): The URL of the audio file.
        path (str): The path to save the audio file.

    Returns:
        str: The local file path where the audio was saved.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(url, stream=True)

        if response.status_code == 200:
            async with aiofiles.open(path, "wb") as audio_file:
                async for chunk in response.aiter_bytes(8192):  # 8KB chunks
                    if chunk:
                        await audio_file.write(chunk)
            return path
        
        raise Exception(f"Failed to download audio. Status code: {response.status_code}")
