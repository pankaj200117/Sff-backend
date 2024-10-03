from src.analysis import client
import logging

logger = logging.getLogger(__name__)
steps_logger = logging.getLogger("steps_info")


async def generate_track_title(audio_description: str, gpt_model: str = 'gpt-4o') -> str:
    """
    Generate a track title using OpenAI's GPT model.

    Args:
        audio_description (str): Description of the audio(in keywords form). Basically, the prompt for Suno AI.
        gpt_model (str): GPT model to use for generating the title.
    
    Returns:
        str: Generated track title.
    """
    steps_logger.info(f"Started generating track title for the audio.")
    prompt = f"Generate a track title for the audio, the description of which is as follows: {audio_description}. Your output should be only a track title, nothing else." 
    response = await client.chat.completions.create(
        model=gpt_model,
        messages=[{"role": "user", "content": prompt}]
    )
    tracks_title = response.choices[0].message.content
    steps_logger.info(f"Generated track title: {tracks_title}")
    return tracks_title.strip('"').strip("'")
