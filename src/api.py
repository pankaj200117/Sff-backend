import uvicorn
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from multiprocessing import Process, Lock
import uuid
import httpx
import multiprocessing, threading, queue
import logging
from typing import Dict
from src.external_api import cyanite, suno_api
from src.utils import load_settings, setup_logging
from configs import config
from src.api_logic.service import process_video, apply_weight, search_similar_music_from_audio, analyze_storyboard_api, save_file
from src.api_logic.queue_processors import (
    process_frames_ext_queue, process_audio_queue, process_queue_wrapper, process_storyboard_queue, s3_upload_worker)
import os
from src.analysis.audio import generate_track_title
from src.utils.yt_fetcher import download_audio_from_yt
from src.api_logic.s3_handler import process_suno_audio, generate_s3_url
import nest_asyncio
nest_asyncio.apply()

setup_logging(log_file_path="logs/api.log")
logger = logging.getLogger(__name__)

app = FastAPI(root_path=config.API_ROOT_PATH)

origins = [
    "*",
]  # the origin (frontend) that is calling the api

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/latest_settings")
async def latest_settings_endpoint() -> JSONResponse:
    """
    Endpoint to retrieve and display the latest settings.

    Returns:
        JSONResponse: A JSON response containing the latest settings.
    """
    logger.info("Retrieving latest settings.")
    latest_settings = load_settings(config.API_SETTINGS_PATH)

    if latest_settings is not None:
        return JSONResponse(content=latest_settings, status_code=200)
    else:
        logger.error("ERROR: Failed to retrieve latest settings.")
        return JSONResponse(content={"error": "Failed to retrieve latest settings."}, status_code=500)
    

@app.get("/quota_information")
async def quota_information_endpoint() -> JSONResponse:
    """
    Endpoint to retrieve and display the SUNO AI quota information.

    Returns:
        JSONResponse: A JSON response containing the quota information.
    """
    try:
        logger.info("Retrieving quota information.")
        quota_info = await suno_api.get_quota_information()
        return JSONResponse(content=quota_info, status_code=200)
    except Exception as e:
        error_message = f"Error retrieving quota information: {str(e)}"
        logger.error(error_message)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload_video/")
async def upload_video_endpoint(file: UploadFile = File(...)) -> JSONResponse:
    """
    Endpoint to upload a video file to the server.

    Args:
        file (UploadFile): The video file to be uploaded.

    Returns:
        JSONResponse: A JSON response containing the generated UUID for the uploaded video.
    """
    try:
        logger.info("Uploading video.")
        video_uuid = str(uuid.uuid4())
        video_path = await save_file(file, video_uuid, "mp4", config.UPLOAD_VIDEO_DIR)
        logger.info(f"Video uploaded: {video_path}")
        return JSONResponse(content={"uuid": video_uuid}, status_code=200)
    except Exception as e:
        error_message = f"Error uploading video: {str(e)}"
        logger.error(error_message)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process_video")
async def process_video_endpoint(video_uuid: str) -> JSONResponse:
    """
    Endpoint to process a video by extracting frames, performing audio analysis, and extracting keywords.

    Args:
        video_uuid (uuid.UUID): The UUID of the uploaded video.

    Returns:
        JSONResponse: A JSON response containing a sorted list of keywords based on their importance.
    """
    try:
        logger.info(f"Processing video: {video_uuid}")
        keywords, video_summarization = await process_video(video_uuid,
                                                            app.state.frames_ext_completion_dict, app.state.audio_completion_dict,
                                                            app.state.frames_ext_queue, app.state.audio_queue)
        logger.info(f"Successfully extracted keywords for video: {video_uuid}")
        keywords_dict = {i+1: keywords[i] for i in range(len(keywords))}
        return JSONResponse(content={"keywords": keywords_dict, "video_summerization": video_summarization}, status_code=200)

    except Exception as e:
        error_message = f"Error processing video {video_uuid}: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze_storyboard/")
async def analyze_storyboard_endpoint(file: UploadFile = File(...)) -> JSONResponse:
    """
    Endpoint to receive a PDF file and call storyboard_analysis on it.

    Args:
        file (UploadFile): The PDF file to be analyzed.

    Returns:
        JSONResponse: A JSON response containing the analysis results.
    """
    try:
        logger.info(f"Analyzing storyboard: {file.filename}")
        if os.path.splitext(file.filename)[-1] != '.pdf':
            raise Exception("Not a PDF file.")

        pdf_uuid = str(uuid.uuid4())
        temp_file_path = await save_file(file, pdf_uuid, "pdf", config.TEMP_PATH)
        
        keywords, summary = await analyze_storyboard_api(temp_file_path, 
                                                         app.state.storyboard_completion_dict, 
                                                         app.state.storyboard_analysis_queue)
        os.remove(temp_file_path)
        keywords_dict = {i+1: keywords[i] for i in range(len(keywords))}
        logger.info(f"Successfully analyzed storyboard: {file.filename}")

        return JSONResponse(content={"keywords": keywords_dict, "storyboard_summarization": summary}, status_code=200)
    except Exception as e:
        error_message = f"Error analyzing storyboard: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=500, detail=error_message)


@app.post("/search_music_weighted/")
async def search_music_weighted_endpoint(
        keywords_weights: Dict[str, float]
) -> JSONResponse:
    """
    Endpoint to search music based on a dictionary of words and their weights.

    Args:
        keywords_weights (Dict[str, float]): Dictionary of words and their weights.

    Returns:
        JSONResponse: A JSON response containing a list of music results along with aggregated keywords.
    """
    try:
        logger.info(f"Searching music with weighted keywords: {keywords_weights}")
        aggregated_keywords = apply_weight(keywords_weights)
        music_results = await cyanite.songsearch(aggregated_keywords)
        logger.info(f"Successfully searched music with weighted keywords: {keywords_weights}")
        return JSONResponse(content={"music_results": music_results, "cyanite_query": aggregated_keywords},
                            status_code=200)

    except Exception as e:
        error_message = f"Error searching music with weighted keywords: {str(e)}"
        logger.error(error_message)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search_music_text/")
async def search_music_text_endpoint(text_input: str) -> JSONResponse:
    """
    Endpoint to search music based on pure text input.

    Args:
        text_input (str): Input text for music search.

    Returns:
        JSONResponse: A JSON response containing the input text and a list of music results.
    """
    try:
        logger.info(f"Searching music with text input: {text_input}")
        music_results = await cyanite.songsearch(text_input)
        logger.info(f"Successfully searched music with text input: {text_input}")
        return JSONResponse(content={"music_results": music_results, "cyanite_query": text_input},
                            status_code=200)

    except Exception as e:
        error_message = f"Error searching music with text input: {str(e)}"
        logger.error(error_message)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search_similar_music_yt/")
async def search_similar_music_yt_endpoint(yt_url: str) -> JSONResponse:
    """
    Endpoint to search music based on a YouTube URL.

    Args:
        yt_url (str): The YouTube URL for which music will be searched.

    Returns:
        JSONResponse: A JSON response containing a list of music results.
    """
    try:
        logger.info(f"Searching music with YouTube URL: {yt_url}")
        audio_path = download_audio_from_yt(yt_url)
        if audio_path is None:
            raise HTTPException(status_code=500, detail=str("Could not download audio from youtube url!"))

        yt_video_title = audio_path.split("/")[-1]
        music_results = await search_similar_music_from_audio(audio_file=None, 
                                                              local_audio_path=audio_path, 
                                                              save_track=False, 
                                                              title=yt_video_title)
        
        logger.info(f"Successfully searched music with YouTube URL: {yt_url}")
        return JSONResponse(content={"music_results": music_results}, status_code=200)

    except Exception as e:
        error_message = f"Error searching music with YouTube URL: {str(e)}"
        logger.error(error_message)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search_similar_music/")
async def search_similar_music_endpoint(audio_file: UploadFile = File(...), save_track: bool = False,
                                        title: str = "API Track") -> JSONResponse:
    """
    Endpoint to search for music similar to the provided audio file.

    Args:
        audio_file (UploadFile): The audio file for which similar music will be searched.
        save_track (bool): Whether to save the track to the library or not.
        title (str): The title of the track.

    Returns:
        JSONResponse: A JSON response containing a list of similar music results.
    """
    try:
        logger.info(f"Searching similar music for audio file: {audio_file.filename}")
        similar_tracks = await search_similar_music_from_audio(audio_file, save_track=save_track, title=title)
        logger.info(f"Successfully searched similar music for audio file: {audio_file.filename}")

        return JSONResponse(content={"music_results": similar_tracks}, status_code=200)

    except Exception as e:
        error_message = f"Error searching similar music: {str(e)}"
        logger.error(error_message)
        # Catch any unexpected exceptions and return a 500 status code with details
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search_spotify_music/{track_id}")
async def search_spotify_music_endpoint(
        track_id: str = Path(..., description="ID of the track on Spotify")
) -> JSONResponse:
    """
    Endpoint to search music on Spotify based on a track ID.

    Args:
        track_id (str): ID of the track on Spotify.

    Returns:
        JSONResponse: A JSON response containing information about the searched track on Spotify.
    """
    try:
        logger.info(f"Searching Spotify music with track ID: {track_id}")
        async with httpx.AsyncClient() as client:
            music_results = await cyanite.search_spotify_music(client, track_id)
        logger.info(f"Successfully searched Spotify music with track ID: {track_id}")
        return JSONResponse(content={"music_results": music_results}, status_code=200)

    except Exception as e:
        error_message = f"Error searching Spotify music with track ID {track_id}: {str(e)}"
        logger.error(error_message)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/library_search_similar_music/")
async def library_search_similar_music(track_id: str) -> JSONResponse:
    """
    Endpoint to search for music similar to the provided track ID.

    Args:
        track_id (str): The ID of the track for which similar music will be searched.

    Returns:
        JSONResponse: A JSON response containing a list of similar music results.
    """
    try:
        logger.info(f"Searching similar music for track ID: {track_id}")
        async with httpx.AsyncClient() as client:
            similar_tracks = await cyanite.search_similar_music(client, track_id)
        logger.info(f"Successfully searched similar music for track ID: {track_id}")
        return JSONResponse(content={"music_results": similar_tracks}, status_code=200)

    except Exception as e:
        error_message = f"Error searching similar music: {str(e)}"
        logger.error(error_message)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate_audio")
async def generate_audio_endpoint(keywords_weights: Dict[str, float]) -> JSONResponse:
    """
    Endpoint to generate audio from text.

    Args:
        keywords_weights (Dict[str, float]): Dictionary of words and their weights.

    Returns:
        JSONResponse: A JSON response containing the audio file.
    """
    try:
        logger.info(f"Generating audio for keywords: {keywords_weights}")
        aggregated_keywords = apply_weight(keywords_weights)
        audio_files = await suno_api.generate_audio_by_prompt(aggregated_keywords, make_instrumental=True, wait_audio=True)
        upload_tasks = []
        # upload generated audio to s3
        for audio_file in audio_files:
            filename = uuid.uuid4().hex + ".mp3"
            upload_tasks.append(process_suno_audio(audio_file["audio_url"], filename))
            audio_file["audio_url"] = generate_s3_url(os.path.join(config.SUNO_S3_FOLDER, filename).replace("\\", "/"))
        await asyncio.gather(*upload_tasks)
        logger.info(f"Successfully generated audio.")
        return JSONResponse(content=audio_files, status_code=200)

    except Exception as e:
        error_message = f"Error generating audio for text: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/generate_audio_details")
async def generate_audio_details_endpoint(keywords_weights: Dict[str, float]) -> JSONResponse:
    """
    Generates audio title from audio description.

    Args:
        keywords_weights (Dict[str, float]): Dictionary of words and their weights.
    
    Returns:
        JSONResponse: A JSON response containing the audio title.
    """
    try:
        logger.info(f"Generating audio title for keywords.")
        aggregated_keywords = apply_weight(keywords_weights)
        audio_title = await generate_track_title(aggregated_keywords)
        audio_titles = [audio_title + " 1", audio_title + " 2"]
        logger.info(f"Successfully generated audio title.")
        return JSONResponse(audio_titles, status_code=200)

    except Exception as e:
        error_message = f"Error generating audio title for text: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate_audio_progress")
async def generate_audio_progress_endpoint(keywords_weights: Dict[str, float]) -> JSONResponse:
    """
    Endpoint to generate audio from text. This endpoint does not wait for the audio to be generated.

    Args:
        keywords_weights (Dict[str, float]): Dictionary of words and their weights.

    Returns:
        JSONResponse: A JSON response containing s3 links to the audio file and audio titles.
    """
    try:
        logger.info(f"Generating audio for keywords: {keywords_weights}")
        aggregated_keywords = apply_weight(keywords_weights)
        audio_files = await suno_api.generate_audio_by_prompt(aggregated_keywords, make_instrumental=True, wait_audio=True)
        # upload generated audio to s3
        for audio_file in audio_files:
            filename = uuid.uuid4().hex + ".mp3"
            app.state.upload_s3_queue.put((audio_file["audio_url"], filename))
            audio_file["audio_url"] = generate_s3_url(os.path.join(config.SUNO_S3_FOLDER, filename).replace("\\", "/"))
        logger.info(f"Successfully generated audio.")
        return JSONResponse(content=audio_files, status_code=200)

    except Exception as e:
        error_message = f"Error generating audio for text: {str(e)}"
        logger.exception(error_message)
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    logger.info("API logging started.")
    os.makedirs(config.UPLOAD_VIDEO_DIR, exist_ok=True)
    os.makedirs(config.TEMP_PATH, exist_ok=True)
    os.makedirs(config.UPLOAD_AUDIO_DIR, exist_ok=True)
    os.makedirs(config.STORYBOARD_EXTRACTION_DIR, exist_ok=True)

    # multiprocessing.set_start_method('spawn', force=True)
    manager = multiprocessing.Manager()

    # Create a shared dictionary to store the completion status of processes.
    frames_ext_completion_dict = manager.dict()
    audio_completion_dict = manager.dict()
    storyboard_completion_dict = manager.dict()

    # Create a shared queue to pass requests to processes.
    frames_ext_queue = manager.Queue()
    audio_queue = manager.Queue()
    storyboard_analysis_queue = manager.Queue()

    frames_ext_queue_processors = [
        Process(target=process_queue_wrapper,
                args=(process_frames_ext_queue, frames_ext_queue, frames_ext_completion_dict), daemon=True) for _ in range(config.N_FRAME_EXTRACTION_PROCESSES)
    ]
    audio_queue_processors = [
        Process(target=process_queue_wrapper,
                args=(process_audio_queue, audio_queue, audio_completion_dict, Lock()), daemon=True) for _ in range(config.N_AUDIO_PROCESSES)
    ]
    storyboard_queue_processors = [
        Process(target=process_queue_wrapper,
                args=(process_storyboard_queue, storyboard_analysis_queue, storyboard_completion_dict, Lock()), daemon=True) for _ in range(config.N_STORYBOARD_PROCESSES)
    ]

    for process in frames_ext_queue_processors + audio_queue_processors + storyboard_queue_processors:
        process.start()

    logger.info(f"Started {config.N_FRAME_EXTRACTION_PROCESSES} frame extraction processes.")
    logger.info(f"Started {config.N_AUDIO_PROCESSES} audio analysis processes.")
    logger.info(f"Started {config.N_STORYBOARD_PROCESSES} storyboard analysis processes.")

    app.state.frames_ext_completion_dict = frames_ext_completion_dict
    app.state.audio_completion_dict = audio_completion_dict

    app.state.frames_ext_queue = frames_ext_queue
    app.state.audio_queue = audio_queue

    app.state.storyboard_completion_dict = storyboard_completion_dict
    app.state.storyboard_analysis_queue = storyboard_analysis_queue

    #Thread to upload generated suno tracks to S3
    app.state.upload_s3_queue = queue.Queue()
    upload_worker_thread = threading.Thread(target=process_queue_wrapper, args=(s3_upload_worker, app.state.upload_s3_queue,), daemon=True)
    upload_worker_thread.start()

    # Thread to delete uploaded tracks from Cyanite
    # app.state.delete_cyanite_queue = queue.Queue()
    # delete_cyanite_thread = threading.Thread(target=process_queue_wrapper, args=(delete_cyanite_tracks, app.state.delete_cyanite_queue,), daemon=True)
    # delete_cyanite_thread.start()


if __name__ == "__main__":
    uvicorn.run("__main__:app", host="127.0.0.1", port=config.API_PORT, workers=config.N_API_WORKERS, loop="asyncio")
