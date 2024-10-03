import torch
import os
from configs import config
from src.utils import extract_filename, delete_old_files
import logging
import os

SAMPLING_RATE = 16000
logger = logging.getLogger(__name__)
steps_logger = logging.getLogger("steps_info")


def group_speech_segments(segments, sampling_rate):
    """
    Group speech segments based on the maximum chunk duration.

    Args:
        segments: Speech segments with start and end timestamps.
        sampling_rate: Sampling rate of the audio.

    Returns:
        List: List of grouped speech segments.
        None: If the total duration of the segments is less than the minimum speech duration.
    """
    total_duration = sum((seg['end'] - seg['start']) / sampling_rate for seg in segments)

    if total_duration < config.MIN_SPEACH_DURATION:
        return None

    grouped_segments = []
    current_group = []
    current_duration = 0

    for segment in segments:
        segment_duration = (segment['end'] - segment['start']) / sampling_rate

        if current_duration + segment_duration <= config.MAX_CHUNK_DURATION:
            current_group.append(segment)
            current_duration += segment_duration
        else:
            grouped_segments.append(current_group)
            current_group = [segment]
            current_duration = segment_duration

    # append the last group if it exists
    if current_group:
        grouped_segments.append(current_group)

    return grouped_segments


def extract_speech(file_path: str):
    """
    Perform voice activity detection on an audio file.
    The speech segments are grouped based on the maximum chunk duration and saved as separate audio files.

    Args:
        file_path (str): Path to the audio file.

    Returns:
        str: Path to the folder containing extracted speech chunks.
    """
    try:
        steps_logger.info(f"Started performing VAD on {file_path}")
        model, utils = torch.hub.load(repo_or_dir='romberol/silero-vad',
                                      model='silero_vad',
                                      trust_repo=True)

        (get_speech_timestamps,
         save_audio,
         read_audio,
         VADIterator,
         collect_chunks) = utils

        wav = read_audio(file_path, sampling_rate=SAMPLING_RATE)
        speech_timestamps = get_speech_timestamps(wav, model)
        steps_logger.info(f"Finished performing VAD on {file_path}")

        grouped_segments = group_speech_segments(speech_timestamps, SAMPLING_RATE)
        if grouped_segments is None:
            logger.warning(f"Speech duration is less than {config.MIN_SPEACH_DURATION} seconds for {file_path}")
            return None

        delete_old_files(config.TEMP_PATH)
        output_folder = os.path.join(config.TEMP_PATH, extract_filename(file_path))
        os.makedirs(output_folder, exist_ok=True)
        for i, group in enumerate(grouped_segments):
            chunk_name = os.path.join(output_folder, f"chunk_{i}.wav")
            save_audio(chunk_name, collect_chunks(group, wav), sampling_rate=SAMPLING_RATE)
        return output_folder

    except Exception as e:
        logger.error(f"Error while performing VAD on {file_path}: {e}")
        return None


if __name__ == "__main__":
    extract_speech("data/uploaded_videos/1.mp3")
