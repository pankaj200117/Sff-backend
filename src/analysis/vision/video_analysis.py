import os
from configs.config import KEYFRAMES_DIR, UPLOAD_VIDEO_DIR
from src.utils import extract_filename, delete_old_files
from src.utils.frame_detection import encode_image
from src.analysis import client
import logging
from typing import Tuple

logger = logging.getLogger(__name__)
steps_logger = logging.getLogger("steps_info")


async def video_analysis(file_path: str, video_description_prompt: str,
                         video_summarization_prompt: str, gpt_model: str = 'gpt-4o') -> Tuple[str, str]:
    """
    Analyzes a video by generating a description and summarizing the description.
    Note: call this function after frames have been extracted!

    Args:
        file_path (str): Path to the video file.
        video_description_prompt (str): Prompt for generating the video description.
        video_summarization_prompt (str): Prompt for summarizing the video description.
        gpt_model (str): OpenAI's GPT model to use for analysis

    Returns:
        tuple: Contains the video description and summarization
        If an error occurs, returns the exception.
    """
    try:
        steps_logger.info(f"Started analyzing video for {file_path}")
        delete_old_files(UPLOAD_VIDEO_DIR)
        description = await describe_video(file_path, video_description_prompt, gpt_model)
        video_summary = await video_summarization(video_summarization_prompt, description, gpt_model)

        steps_logger.info(f"Finished analyzing video for {file_path}")
        return description, video_summary

    except Exception as e:
        logger.exception(f"Error while analyzing video {file_path}: {e}")
        raise e


async def describe_video(file_path: str, video_description_prompt: str, gpt_model: str = 'gpt-4o') -> str:
    """
    Generates a description of the video based on extracted keyframes.

    Args:
        file_path (str): Path to the video file.
        video_description_prompt (str): Prompt for generating the video description.
        gpt_model (str): OpenAI's GPT model to use for analysis

    Returns:
        str: Description of the video.
    """
    steps_logger.info(f"Started describing video {file_path}")
    filename = extract_filename(file_path)
    frames_folder = os.path.join(KEYFRAMES_DIR, filename)
    frames = [encode_image(os.path.join(frames_folder, name)) for name in [
        f"keyframe{i+1}.jpg" for i in range(len(os.listdir(frames_folder)))]]

    contents = [{"type": "text", "text": video_description_prompt}] + [
        {'type': 'image_url', 'image_url': {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "low"}} for base64_image in frames]

    if gpt_model == "gpt-4 + vision": 
        gpt_model = "gpt-4-vision-preview"
    
    response = await client.chat.completions.create(
        model=gpt_model,
        messages=[{"role": "user", "content": contents}],
        max_tokens=700
    )

    description = response.choices[0].message.content
    steps_logger.info(f"Finished describing video.\nVideo Description: {description}")
    return description


async def video_keyword_extraction(keyword_extraction_prompt: str, video_description_output: str, gpt_model: str = 'gpt-4o'):
    """
    Extracts keywords from the video description.

    Args:
        keyword_extraction_prompt (str): Prompt for extracting keywords.
        video_description_output (str): The description of the video.
        gpt_model (str): The GPT model to use for keyword extraction.

    Returns:
        str: Extracted keywords from the video description.
    """
    steps_logger.info(f"Started extracting keywords from video description. Video Description: {video_description_output[:100]}...")
    contents = [{"type": "text", "text": keyword_extraction_prompt}] + [{"type": "text", "text": video_description_output}]

    if gpt_model == "gpt-4 + vision": 
        gpt_model = "gpt-4"

    response = await client.chat.completions.create(
        model=gpt_model,
        messages=[{"role": "user", "content": contents}],
    )

    keywords = response.choices[0].message.content.rstrip(",").replace(".", "").lower()
    steps_logger.info(f"Finished extracting keywords from video description.\nKeywords: {keywords}")
    return keywords.lower()


async def video_summarization(video_summarization_prompt, video_description, gpt_model: str = 'gpt-4o') -> str:
    """
    Summarizes the video description.

    Args:
        video_summarization_prompt (str): Prompt for summarizing the video description.
        video_description (str): The description of the video.
        gpt_model (str): The GPT model to use for summarization.

    Returns:
        str: Summarized video description.
    """
    steps_logger.info(f"Started summarizing video description. Video Description: {video_description[:100]}...")
    contents = [{"type": "text", "text": video_summarization_prompt}] + [{"type": "text", "text": video_description}]

    if gpt_model == "gpt-4 + vision": 
        gpt_model = "gpt-4"

    response = await client.chat.completions.create(
        model=gpt_model,
        max_tokens=500,
        messages=[{"role": "user", "content": contents}],
    )

    summarization = response.choices[0].message.content
    steps_logger.info(f"Finished summarizing video description.\nSummarization: {summarization}")
    return summarization
