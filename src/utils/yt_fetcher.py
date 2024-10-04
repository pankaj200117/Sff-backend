from pytubefix import YouTube
from configs import config
import os

def download_audio_from_yt(yt_url: str, local_audio_path: str|None = None) -> str|None:
    """
    Download audio from youtube video.

    Args:
        yt_url (str): Youtube video url.
        local_audio_path (str|None): Local path to save audio file. If None, saves to UPLOAD_AUDIO_DIR.
    
    Returns:
        str|None: Local path to saved audio file. None if download failed.
    """
    yt = YouTube(yt_url, use_oauth=True)
    audio = sorted(yt.streams.filter(only_audio=True), key=lambda x: int(x.abr[:-4]))[-1]  # get audio with highest bitrate
    if local_audio_path is None:
        local_audio_path = os.path.join(config.UPLOAD_AUDIO_DIR, f"{yt.title}.mp3")
    if audio:
        audio.download(filename=local_audio_path)
        return local_audio_path
    return None
