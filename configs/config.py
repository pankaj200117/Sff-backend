KEYFRAMES_DIR = 'data/keyframes/'
UPLOAD_VIDEO_DIR = "data/uploaded_videos"
UPLOAD_AUDIO_DIR = "data/uploaded_audios"
STORYBOARD_EXTRACTION_DIR = "data/storyboards_extracted"
TEMP_PATH = 'data/temp/'

N_API_WORKERS = 1
N_FRAME_EXTRACTION_PROCESSES = 1
N_AUDIO_PROCESSES = 1
N_STORYBOARD_PROCESSES = 1

MIN_SPEACH_DURATION = 2  # (in seconds) If the speech duration is less than this, the audio is not processed.
MAX_CHUNK_DURATION = 10 * 60  # (in seconds) Maximum duration of a chunk that goes to Whisper model.

API_SETTINGS_PATH = 'configs/latest_settings.json'
GRADIO_LATEST_SETTINGS_PATH = "configs/latest_settings.json"

SUNO_API_APP_URL = "http://localhost:3000"
SUNO_S3_FOLDER = "suno-tracks"

GRADIO_ROOT_PATH = ""
API_ROOT_PATH = ""

API_PORT = 5011
GRADIO_PORT = 5002