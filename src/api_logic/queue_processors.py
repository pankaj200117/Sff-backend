from src.analysis import audio, vision
import asyncio
from src.utils import frame_detection
from src.external_api import cyanite
from src.api_logic.s3_handler import process_suno_audio
import nest_asyncio
import httpx
import time


def process_queue_wrapper(process_func, *args):
    """
    Wrapper function to process requests from a queue.
    Needed, so we can create async tasks inside process_func and not await for them.
    """
    nest_asyncio.apply()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(process_func(*args))


async def create_tasks_from_queue(queue, completion_dict, process_func, lock):
    """
    Continuously processes tasks from the queue.

    We can't use queue.get(block=True) because it will block the event loop, 
        and async functions will not be able to run.
    """
    while True:
        with lock:
            if not queue.empty():
                item = queue.get()
            else:
                item = None

        if item is not None:
            asyncio.create_task(process_func(item, completion_dict))
        else:
            await asyncio.sleep(0.5)


async def process_frames_ext_queue(queue, completion_dict):
    """
    Continuously processes videos from the queue by extracting frames.

    Args:
        queue (multiprocessing.Queue): The queue containing video processing tasks.
        completion_dict (multiprocessing.Dict): A dictionary to store the completion status of each video.
    """
    while True:
        item = queue.get()
        video_path, n_frames, return_collage = item
        try:
            frame_detection.extract_frames(video_path, n_frames, return_collage)
            completion_dict[video_path] = True
        except Exception:
            completion_dict[video_path] = False


async def process_audio_queue(queue, completion_dict, lock):
    """
    Continuously processes videos from the queue by analyzing audio from them.

    Args:
        queue (multiprocessing.Queue): The queue containing audio processing tasks.
        completion_dict (multiprocessing.Dict): A dictionary to store the completion status of each audio file.
        lock: (multiprocessing.Lock): A lock to ensure multiprocessing safety.
    """
    async def audio_analysis_task(item, completion_dict):
        video_path = item
        try:
            transcript = await audio.audio_analysis(video_path)
            completion_dict[video_path] = transcript
        except Exception:
            completion_dict[video_path] = False

    await create_tasks_from_queue(queue, completion_dict, audio_analysis_task, lock)


async def process_storyboard_queue(queue, completion_dict, lock):
    """
    Continuously processes storyboards from the queue by analyzing them.

    Args:
        queue (multiprocessing.Queue): The queue containing storyboard processing tasks.
        completion_dict (multiprocessing.Dict): A dictionary to store the completion status of each storyboard.
        lock: (multiprocessing.Lock): A lock to ensure multiprocessing safety.
    """
    async def storyboard_analysis_task(item, completion_dict):
        file_path, storyboard_description_prompt, keyword_extraction_prompt, storyboard_summarization_prompt, gpt_model = item
        try:
            description, keywords, summarization = await vision.analyze_storyboard(
                file_path, storyboard_description_prompt, keyword_extraction_prompt, storyboard_summarization_prompt, 
                extract_images=True, gpt_model=gpt_model)
            completion_dict[file_path] = (keywords, summarization)
        except Exception:
            completion_dict[file_path] = False

    await create_tasks_from_queue(queue, completion_dict, storyboard_analysis_task, lock)


async def s3_upload_worker(upload_queue):
    """
    Continuously processes audio files from the queue by downloading and uploading them to S3.
    Supposed to be used as a worker in a separate thread.

    Args:
        upload_queue (queue.Queue): The queue containing audio processing tasks.
    """
    while True:
        if not upload_queue.empty():
            url, file_id = upload_queue.get()
        else: 
            url, file_id = None, None

        if url is not None:
            asyncio.create_task(process_suno_audio(url, file_id))
        else:
            await asyncio.sleep(5)

async def delete_cyanite_tracks(delete_queue):
    """
    Continuously processes audio files from the queue by deleting them from Cyanite.
    Supposed to be used as a worker in a separate thread.

    Args:
        delete_queue (queue.Queue): The queue containing audio processing tasks.
    """
    while True:
        if not delete_queue.empty():
            track_id, upload_time = delete_queue.get()
        else: 
            track_id, upload_time = None, None

        if track_id is not None:
            if time.time() - upload_time > 60 * 5:
                timeout = httpx.Timeout(10.0, read=None)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    await cyanite.delete_library_tracks(client, track_id)
                continue
            else:
                delete_queue.put((track_id, upload_time))
        await asyncio.sleep(200)