import asyncio
import os
import shutil
import time
from typing import Dict, List, Tuple
from fastapi import File, UploadFile, HTTPException
import aiofiles
from configs import config
from src.analysis import vision, keywords_ext
from src.external_api import cyanite
from src.utils import load_settings, delete_old_files
import uuid
import httpx
import logging

logger = logging.getLogger(__name__)
steps_logger = logging.getLogger("steps_info")


def apply_weight(keywords_weights: Dict[str, float]) -> str:
    """
    Apply weights to keywords based on a dictionary.

    Args:
        keywords_weights (Dict[str, float]): Dictionary of keywords and their weights.

    Returns:
        str: Aggregated keywords with weights applied.
    """
    keyword_list = []
    for keyword, weight in keywords_weights.items():
        keyword_list.extend([keyword] * int(weight))
    aggregated_keywords = ', '.join(keyword_list)
    return aggregated_keywords


async def save_file(file, uuid: str, extension: str, directory: str) -> str:
    """
    Async save a file to the specified directory with the specified UUID.

    Args:
        file (UploadFile): The file to be saved.
        uuid (str): The UUID to be used for the saved file.
        extension (str): The extension of the file.
        directory (str): The directory to save the file.
    Returns:
        str: The path to the saved file.
    """
    os.makedirs(directory, exist_ok=True)
    output_path = os.path.join(directory, f"{uuid}.{extension}")
    async with aiofiles.open(output_path, "wb") as output_file:
        await output_file.write(await file.read())
    steps_logger.info(f"File saved successfully: {output_path}")
    return output_path


async def wait_for_completion(file_path, completion_dict, sleep_time, error_message):
    """
    Wait for the completion of a task by checking the completion dictionary.

    Args:
        file_path (str): The path of the file to wait for.
        completion_dict (multiprocessing.Dict[str, bool]): The dictionary containing the completion status of each file.
        sleep_time (float): The time to sleep between checks.
        error_message (str): The error message to raise if the file is not completed
    """
    while file_path not in completion_dict:
        await asyncio.sleep(sleep_time)
    if completion_dict[file_path] == False:  # can be None if audio has no speech
        logger.error(f"{error_message}: {file_path}")
        raise HTTPException(status_code=500, detail=error_message)


async def process_video(video_uuid: str, frames_ext_completion_dict: Dict[str, bool], audio_completion_dict: Dict[str, bool],
                        frames_ext_queue, audio_analysis_queue) -> Tuple[List[str], str]:
    """
    Process a video by extracting frames, analyzing audio and video, and summarizing the video.

    Args:
        video_uuid (str): The UUID of the video to be processed.
        frames_ext_completion_dict (multiprocessing.Dict[str, bool]): A dictionary to store the completion status of frame extraction.
        audio_completion_dict (multiprocessing.Dict[str, bool]): A dictionary to store the completion status of audio analysis.
        frames_ext_queue (multiprocessing.Queue): The queue containing frame extraction tasks.
        audio_analysis_queue (multiprocessing.Queue): The queue containing audio analysis tasks.

    Returns:
        Tuple[List[str], str]: A tuple containing the list of keywords and the video summarization result.
    """
    settings = load_settings(config.API_SETTINGS_PATH)
    if not settings:
        raise ValueError("Error: File containing the last saved settings is empty.")

    video_path = f"{config.UPLOAD_VIDEO_DIR}/{video_uuid}.mp4"

    # Extract frames from the video
    output_folder = os.path.join(config.KEYFRAMES_DIR, video_uuid)
    if os.path.exists(output_folder):  # if we previously processed video with the same uuid, delete the folder
        shutil.rmtree(output_folder, ignore_errors=True)

    start = time.time()
    frames_ext_queue.put((video_path, settings["number_of_frames"], settings["extract_frames_as_collage"]))

    # Extract keywords from audio
    audio_analysis_queue.put(video_path)

    await wait_for_completion(video_path, frames_ext_completion_dict, 0.25, "Failed to extract frames from video")
    del frames_ext_completion_dict[video_path]

    steps_logger.info(f"Time taken to extract frames: {time.time() - start:.3f} seconds for video: {video_uuid}")

    # Extract keywords from video
    video_analysis_task = asyncio.create_task(vision.video_analysis(video_path, settings["video_description_prompt"],
                                                            settings["video_summarization_prompt"], settings["gpt_model"]))

    await wait_for_completion(video_path, audio_completion_dict, 0.25, "Failed to analyze audio for video")
    audio_transcription = audio_completion_dict[video_path]
    del audio_completion_dict[video_path]

    video_description, video_summary = await video_analysis_task

    
    if settings["model_type_for_keywords_extraction"] == "OpenAI Assistant (will use gpt-4o)":
        # Extract keywords from video description and audio transcription for all 4 creativity levels
        keywords_extraction_prompts = [
            settings["assistant_keyword_extraction_prompt_1"], settings["assistant_keyword_extraction_prompt_2"],
            settings["assistant_keyword_extraction_prompt_3"], settings["assistant_keyword_extraction_prompt_4"]]
        extraction_function = keywords_ext.video_audio_extraction_assistant
        args = [video_description, audio_transcription]
    else:
        # Extract keywords from video description and audio transcription for all 4 creativity levels
        keywords_extraction_prompts = [
            settings["video_audio_keyword_extraction_prompt_1"], settings["video_audio_keyword_extraction_prompt_2"],
            settings["video_audio_keyword_extraction_prompt_3"], settings["video_audio_keyword_extraction_prompt_4"]]
        extraction_function = keywords_ext.video_audio_extraction
        strucutred_output = settings["model_type_for_keywords_extraction"] == "Structured output (will use gpt-4o-2024-08-06)"
        args = [video_description, audio_transcription, settings["gpt_model"], strucutred_output]
    
    keywords = await keywords_ext.video_audio_creative_extraction(extraction_function,
                                                                  keywords_extraction_prompts, 
                                                                  *args)

    keywords_splitted = [[word.lower() for word in keywords_string.split(', ') if word.strip()] for keywords_string in keywords]

    steps_logger.info(f"Keywords successfully extracted for video: {video_uuid}.\nKeywords: {keywords}.\n"
                      f"Video summarization: {video_summary}")
    return keywords_splitted, video_summary


async def analyze_storyboard_api(file_path: str, storyboard_completion_dict: Dict[str, bool], storyboard_queue) -> Tuple[List[str], str]:
    """
    Analyze a storyboard by generating a description, extracting keywords, and summarizing the description.

    Args:
        file_path (str): Path to the storyboard file.
        storyboard_completion_dict (multiprocessing.Dict[str, bool]): A dictionary to store the completion status of storyboard analysis.
        storyboard_queue (multiprocessing.Queue): The queue containing storyboard analysis tasks.

    Returns:
        Tuple: Contains the extracted keywords and summarization.
    """
    settings = load_settings(config.API_SETTINGS_PATH)
    if not settings:
        raise ValueError("Error: File containing the last saved settings is empty.")
    
    keywords_prompts = [settings["storyboard_keyword_extraction_prompt_1"], settings["storyboard_keyword_extraction_prompt_2"],
                         settings["storyboard_keyword_extraction_prompt_3"], settings["storyboard_keyword_extraction_prompt_4"]]
    
    storyboard_queue.put((file_path, settings["storyboard_description_prompt"], keywords_prompts,
                                    settings["storyboard_summarization_prompt"], settings["gpt_model"]))
    
    await wait_for_completion(file_path, storyboard_completion_dict, 0.25, "Failed to analyze storyboard")
    keywords, summary = storyboard_completion_dict[file_path]
    keywords = [keyword.lower().split(", ") for keyword in keywords]
    del storyboard_completion_dict[file_path]

    return keywords, summary


async def search_similar_music_from_audio(
        audio_file: UploadFile = File(...),
        local_audio_path: str = None,
        save_track: bool = False,
        title: str = "API Track"
):
    """
    Search for music similar to the provided audio file.

    Args:
        audio_file (UploadFile): The audio file for which similar music will be searched.
        local_audio_path (str): The local path of the audio file, if already saved.
        save_track (bool): Whether to save the track to the library or not.
        title (str): The title of the track.

    Returns:
        list of similar music results.
    """
    # Create the directory if it doesn't exist
    os.makedirs(config.UPLOAD_AUDIO_DIR, exist_ok=True)
    delete_old_files(config.UPLOAD_AUDIO_DIR)

    if local_audio_path:
        audio_path = local_audio_path
    else:
        # Save the audio file to the server
        audio_uuid = str(uuid.uuid4())
        audio_path = os.path.join(config.UPLOAD_AUDIO_DIR, f"{audio_uuid}.mp3")
        async with aiofiles.open(audio_path, "wb") as audio_file_saved:
            await audio_file_saved.write(await audio_file.read())
    audio_path = audio_path.replace("\\", "/")

    timeout = httpx.Timeout(10.0, read=None)
    async with httpx.AsyncClient(timeout=timeout) as client:
        # Get file upload request
        file_upload_request = await cyanite.get_file_upload_request(client)

        if not file_upload_request:
            raise HTTPException(status_code=500, detail="Failed to obtain file upload request.")

        upload_url = file_upload_request['uploadUrl']
        file_upload_id = file_upload_request['id']

        # Upload the file
        if not await cyanite.upload_file(client, upload_url, audio_path):
            raise HTTPException(status_code=500, detail="File upload failed.")

        steps_logger.info(f"File uploaded successfully with ID: {file_upload_id}")

        # Create library track using file upload ID
        created_track_id = await cyanite.create_library_track(client, file_upload_id, title)

        if not created_track_id:
            raise HTTPException(status_code=500, detail="Library Track creation failed.")

        steps_logger.info(f"Library Track created successfully with ID: {created_track_id}")

        # Now you can enqueue analysis for the created library track
        await cyanite.enqueue_library_track_analysis(client, created_track_id)

        # Simulating a delay for analysis completion (adjust as needed)
        for i in range(20):
            similar_tracks = await cyanite.search_similar_music(client, created_track_id, False)
            if similar_tracks:
                break
            steps_logger.info("Retrying to search similar music. Retry count: " + str(i+1))
            await asyncio.sleep(5)

        if not save_track:
            await cyanite.delete_library_tracks(client, created_track_id)

        return similar_tracks
