# Configuration Files

### Overview
The project includes several configuration files that control various aspects of the application. These files are located in the `configs` directory.

### Configuration Files
- **latest_settings.json**: Latest settings, that are used in API and Gradio app. Can be modified in the Gradio app.
- **logging.yaml**: Specifies the configuration for logging, including log levels, formats, and handlers.
- **config.py**: Configuration settings for the gradio and api applications.


### Parameters in `config.py`
- `KEYFRAMES_DIR`, `UPLOAD_VIDEO_DIR`, `UPLOAD_AUDIO_DIR`, `STORYBOARD_EXTRACTION_DIR`: Directories for storing keyframes, uploaded videos, uploaded audio, and storyboard extraction.
- `N_..._PROCESS`: Number of processes for analyzing (video, audio, storyboards, etc), that can be run in parallel.
- `MIN_SPEACH_DURATION`: Minimum duration of speech in seconds for audio transcription. If the speech duration is less than this value, the audio will be not processed.
- `MAX_CHUNK_DURATION`: Maximum duration of audio chunks in seconds for audio that goes to the transcription API.
- `API_SETTINGS_PATH`, `GRADIO_LATEST_SETTINGS_PATH`: Paths to the API settings, latest Gradio settings files. **Note**: By defalut, API uses the **same** settings file as Gradio, so that the settings can be modified in the Gradio app.
- `SUNO_API_APP_URL`: URL of the Suno API application. Simple redirect to local port, where the Suno API App is running.
- `SUNO_S3_FOLDER`: Folder in the S3 bucket where the generated music files will be stored.
- `GRADIO_ROOT_PATH`, `API_ROOT_PATH`: [ROOT_PATH and Nginx Setup](ROOT_PATH_and_Nginx_Setup.md)

### Settings files parameters
Designed to guide the extraction and explanation of audio/video-related keywords and descriptions.
- `number_of_frames`: specifies the number of frames to be extracted from a video for analysis.
- `gpt_model`: specifies the GPT model used for video description and summarization, storyboard analysis.
- `extract_frames_as_collage`: specifies whether to extract frames as a collage(4 frames in one image) or as separate images.
- `model_type_for_keywords_extraction`: specifies the model type(with/without structured outputs, openai assistant) used for keyword extraction. Possible values can be found in gradio app.
- `video_description_prompt`: prompt for analyzing and describing the sequence of images (keyframes) from a video to get video description.
- `video_audio_keyword_extraction_prompt_[1, 2, 3, 4]`: prompt used for keyword extraction from audio transcription and video description at the same time. The number indicates the creativity level of the prompt.
- `assistant_keyword_extraction_prompt_[1, 2, 3, 4]`: prompt used for keyword extraction from audio transcription and video description at the same time by openai assistant. The number indicates the creativity level of the prompt.
- `video_summarization_prompt`: prompt for summarizing the video.
- `storyboard_description_prompt`: prompt for analyzing and describing the storyboard to get storyboard description.
- `storyboard_keyword_extraction_prompt_[1, 2, 3, 4]`: prompt used for keyword extraction from storyboard description. The number indicates the creativity level of the prompt.
- `storyboard_summarization_prompt`: prompt for summarizing the storyboard.