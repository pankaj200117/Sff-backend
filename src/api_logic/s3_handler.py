import httpx
import aioboto3
import os
from botocore.exceptions import ClientError
import logging
from configs import config
import aiofiles

logger = logging.getLogger(__name__)
steps_logger = logging.getLogger("steps_info")

S3_BUCKET_NAME = os.getenv('AWS_BUCKET')
S3_REGION_NAME = os.getenv('AWS_REGION')

async def download_audio(url: str, local_filename: str) -> str:
    """
    Download the audio stream from the given URL and save it to a local file.

    Args:
        url (str): The URL to download the audio from.
        local_filename (str): The local file path to save the audio to.

    Returns:
        str: The local file path of the saved audio.
    """
    async with httpx.AsyncClient() as client:
        timeout = httpx.Timeout(10.0, read=None)
        async with client.stream("GET", url, timeout=timeout) as response:
            steps_logger.info(f"Saving {url} -> {local_filename}")
            if response.status_code != 200:
                logger.error(f"Failed to stream audio from {url}, status code: {response.status_code}")
                return None

            with open(local_filename, 'wb') as file:
                async for chunk in response.aiter_bytes():
                    file.write(chunk)
        
        steps_logger.info(f"Downloaded and saved audio to {local_filename}")
        return local_filename


async def download_from_s3(s3_key: str, local_filename: str):
    """
    Download file from the specified S3 bucket.

    Args:
        s3_key (str): The path of the file in the S3 bucket to download.
        local_filename (str): The local file path where the audio will be saved.
    
    Returns:
        bool: True if the download was successful, False otherwise
    """
    try:
        session = aioboto3.Session()
        steps_logger.info(f"Downloading {s3_key} -> {local_filename}")
        async with session.client('s3') as s3_client:
            s3_ob = await s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
            async with aiofiles.open(local_filename, 'wb') as file_data:
                while True:
                    data = await s3_ob['Body'].read(1024)  # Adjust chunk size as needed
                    if not data:
                        break
                    await file_data.write(data)
                steps_logger.info(f"Downloaded {s3_key} to {local_filename}")
        return True
    except ClientError as e:
        logger.error(f"Downloading {s3_key} from s3 failed: {e}")
        return False



async def upload_to_s3(local_filename: str, s3_key: str):
    """
    Upload the local file to the specified S3 bucket.

    Args:
        local_filename (str): The local file path to upload.
        s3_key (str): Path to save the file in the S3 bucket.
    """
    try:
        session = aioboto3.Session()
        steps_logger.info(f"Uploading {local_filename} -> {s3_key}")
        async with session.client('s3') as s3_client:
            with open(local_filename, 'rb') as file_data:
                await s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=s3_key, Body=file_data)
                steps_logger.info(f"Uploaded {s3_key} to S3")
    except ClientError as e:
        logger.error(f"Uploading {local_filename} to s3 failed: {e}")


async def process_suno_audio(url, filename):
    """
    Download audio and then upload it to S3.
    Args:
        url (str): The URL to download the audio from.
        filename (str): The name of the file to save and upload.
    """
    local_filename = os.path.join(config.TEMP_PATH, filename)
    s3_key = os.path.join(config.SUNO_S3_FOLDER, filename).replace("\\", "/")

    saved_file = await download_audio(url, local_filename)
    if saved_file:
        await upload_to_s3(saved_file, s3_key)


def generate_s3_url(s3_key: str) -> str:
    """Generate a public URL for the uploaded S3 object."""
    return f"https://{S3_BUCKET_NAME}.s3.{S3_REGION_NAME}.amazonaws.com/{s3_key}".replace(" ", "+")
