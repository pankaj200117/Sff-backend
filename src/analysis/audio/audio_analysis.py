import os.path
import shutil
from src.analysis import client
from typing import Tuple
import logging
from .vad_pipeline import extract_speech
import subprocess

logger = logging.getLogger(__name__)
steps_logger = logging.getLogger("steps_info")


async def audio_analysis(file_path: str) -> str:
    """
    Extract speech from the audio of a video file and transcribe it.

    Args:
        file_path (str): Path to the input video file.

    Returns:
        str: Transcription of the audio.
    """
    try:
        steps_logger.info(f"Started analyzing audio for {file_path}")
        audio_filename = os.path.splitext(file_path)[0] + '.wav'
        if not extract_audio(file_path, audio_filename):
            logger.warning(f"No audio was extracted from the video: {file_path}")
            return None

        chunks_folder = extract_speech(audio_filename)
        if os.path.exists(audio_filename):
            os.remove(audio_filename)
        
        if chunks_folder is None:
            return None
        
        transcript = await transcribe_audio(chunks_folder)
        steps_logger.info(f"Finished analyzing audio for {file_path}")
        return transcript

    except Exception as e:
        logger.exception(f"Error while analyzing audio {file_path}: {e}")
        raise e


async def audio_keywords_extraction(transcript: str, audio_prompt: str, gpt_model: str = 'gpt-4o') -> str:
    """
    Perform audio analysis using OpenAI's GPT model.

    Args:
        transcript (str): Transcription of the audio.
        audio_prompt (str): Prompt for audio analysis.
        gpt_model (str): GPT model to use for audio analysis.

    Returns:
        str: Result of the audio analysis.
    """
    steps_logger.info(f"Started extracting keywords from audio. Transcript: {transcript[:100]}...")

    if gpt_model == "gpt-4 + vision": 
        gpt_model = "gpt-4"
    
    response = await client.chat.completions.create(
        temperature=0,
        model=gpt_model,
        messages=[
            {"role": "system", "content": audio_prompt},
            {"role": "user", "content": transcript}
        ]
    )
    audio_keywords = response.choices[0].message.content
    steps_logger.info(f"Finished extracting keywords from audio.\nKeywords: {audio_keywords}")
    return audio_keywords


def extract_audio(input_video_path, output_audio_path, sample_rate=16000, channels=1):
    """
    Extracts audio from a video file and resamples it to the specified sample rate.

    Parameters:
        input_video_path (str): Path to the input video file.
        output_audio_path (str): Path to the output audio file.
        sample_rate (int): Desired audio sample rate in Hz (default is 16000 Hz).
        channels (int): Number of audio channels (default is 1 for mono).
    """
    # Construct the ffmpeg command
    command = [
        'ffmpeg',
        '-i', input_video_path,
        '-ar', str(sample_rate),
        '-ac', str(channels),
        '-vn',
        output_audio_path,
        '-y'
    ]

    try:
        # Execute the ffmpeg command
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        steps_logger.info(f"Audio extracted and saved to {output_audio_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error while extracting audio from {input_video_path}: {e}")
        return False


async def transcribe_audio(chunks_folder: str) -> str:
    """
    Perform transcription of audio using OpenAI's GPT model.

    Args:
        chunks_folder (str): Path to the folder containing audio chunks.

    Returns:
        str: Transcription of the audio.
    """
    steps_logger.info(f"Started transcribing audio for {chunks_folder}")
    result = ''

    for chunk_name in os.listdir(chunks_folder):
        with open(os.path.join(chunks_folder, chunk_name), 'rb') as audio_file:
            chunk_transcription = await client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        result += chunk_transcription.text

    shutil.rmtree(chunks_folder, ignore_errors=True)
    steps_logger.info(f"Finished transcribing audio for {chunks_folder}.\nTranscription: {result}")
    return result


if __name__ == "__main__":
    testFile = "America_s Game_31 V3_NO MUSIC"
    # extract_audio(testFile)
    # transcript(testFile)
    # audio_analysis(testFile)
    # mov2mp4("data/videos/YETI_NO MUSIC.mov")
