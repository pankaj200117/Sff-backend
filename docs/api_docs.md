# API

## Settings
Path to the settings file with prompts should be specified in `configs/config.py` file.
By default, the path is set to `configs/api_settings.json`.
```python
API_SETTINGS_PATH = 'configs/api_settings.json'
```
Additionally, you can specify the number of parallel processes that 
- extract frames from the video: `N_FRAME_EXTRACTION_PROCESSES` 
- analyze audio: `N_AUDIO_PROCESSES`
- analyze video: `N_VIDEO_PROCESSES`
- analyze storyboards: `N_STORYBOARD_PROCESSES`

Also, you can have multiple api workers by setting `N_API_WORKERS` to the desired number.



## Usage
To start the API, execute the following command in your terminal:
```sh
python -m src.api
```
Application will run on port 5011.

Port 5011 is used by default and can be changed in the `configs/config.py` file.

Logs will be printed to the console and saved to `logs/api.log`. Note, that log file will have more detailed information
about each step of the process.

## API Endpoints
### 1. Retrieve Latest Settings
`GET /latest_settings`
- **Description**: Retrieves and displays the latest settings for keywords retrieval.
- **Response**: JSON response containing the latest settings.

### 2. Upload Video
`POST /upload_video/`
- **Description**: Uploads a video file to the server.
- **Request**:
  - `file` (UploadFile): The video file to be uploaded.
- **Response**: JSON response containing the generated UUID for the uploaded video.

### 3. Analyze storyboard
`POST /analyze_storyboard/`
- **Description**: Analyzes storyboard by extracting keywords and performing summarization
- **Request**:
  - `file` (UploadFile): The PDF file to be analyzed.
- **Response**: JSON response containing the analysis results with 
  - `keywords` (Dict[int, List[str]]): A dictionary where keys are creativity levels (1 to 4), and values are lists of keywords extracted using prompts corresponding to these creativity levels.
    - `1`: List of keywords extracted using a creativity level 1 prompts.
    - `2`: List of keywords extracted using a creativity level 2 prompts.
    - `3`: List of keywords extracted using a creativity level 3 prompts.
    - `4`: List of keywords extracted using a creativity level 4 prompts.
  - `storyboard_summarization` (str): Summary of the storyboard analysis.

### 4. Process Video
`POST /process_video`
- **Description**: Processes a video by extracting frames, performing audio and video analysis to extract keywords using different creativity levels and summarizing the video content. The keywords are categorized by the creativity level of the analysis prompts.
- **Request**:
  - `video_uuid` (str): The UUID of the uploaded video.
- **Response**: JSON response containing a dictionary of keywords categorized by creativity levels and a video summarization.
  - `keywords` (Dict[int, List[str]]): A dictionary where keys are creativity levels (1 to 4), and values are lists of keywords extracted using prompts corresponding to these creativity levels.
    - `1`: List of keywords extracted using a creativity level 1 prompts.
    - `2`: List of keywords extracted using a creativity level 2 prompts.
    - `3`: List of keywords extracted using a creativity level 3 prompts.
    - `4`: List of keywords extracted using a creativity level 4 prompts.
  - `video_summerization` (str): Summary of the video content.


### 5. Search Music with Weighted Keywords
`POST /search_music_weighted/`
- **Description**: Searches music based on a dictionary of words and their weights.
- **Request**:
  - (Dict[str, float]): Dictionary of words and their weights.
- **Response**: JSON response containing a list of music results along with aggregated keywords.

### 6. Search Music with Text Input
`POST /search_music_text/`
- **Description**: Searches music based on pure text input.
- **Request**:
  - `text_input` (str): Input text for music search.
- **Response**: JSON response containing the input text and a list of music results.

### 7. Search Similar Music with Audio File
`POST /search_similar_music/`
- **Description**: Searches for music similar to the provided audio file.
- **Request**:
  - `audio_file` (UploadFile): The audio file for which similar music will be searched.
  - `save_track` (bool): Whether to save the track to the library or not (default: False).
  - `title` (str): The title of the track (default: "API Track").
- **Response**: JSON response containing a list of similar music results.

### 8. Search Music from YouTube URL
`POST /search_similar_music_yt/`

- **Description**: Searches for music based on audio from provided YouTube URL.
- **Request**:
  - `yt_url` (str): The YouTube URL for which music will be searched.
- **Response**: JSON response containing a list of music results.

### 9. Search Spotify Music by Track ID
`GET /search_spotify_music/{track_id}`
- **Description**: Searches music on Spotify based on a track ID.
- **Request**:
  - `track_id` (str): ID of the track on Spotify.
- **Response**: JSON response containing information about the searched track on Spotify.

### 10. Library Search for Similar Music
`POST /library_search_similar_music/`
- **Description**: Searches for music similar to the provided audio file.
- **Request**:
  - `track_id` (str): The ID of the track for which similar music will be searched.
- **Response**: JSON response containing a list of similar music results.


### 11. Generate Audio
`POST /generate_audio`
- **Description**: Generates audio based on the provided keywords and their respective weights. Waits for the generation to finish and returns the title of the audio and the URL to the generated audio.
- **Request**:
  - (Dict[str, float]): A dictionary where keys are keywords and values are their respective weights.
- **Response**: JSON response containing a list of 2 generated audio results. Each result includes:
  - `title` (str): The title of the generated audio. Title is generated by Suno AI.
  - `audio_url` (str): The URL to S3 bucket where the audio is saved.

### 12. Generate Audio Progress
`POST /generate_audio_progress`
- **Description**: Generates audio based on the provided keywords and their respective weights. Returns link to s3 bucket and title of the audio immediately after generation starts.
- **Request**:
  - (Dict[str, float]): A dictionary where keys are keywords and values are their respective weights.
- **Response**: JSON response containing a list of 2 generated audio results. Each result includes:
  - `title` (str): The title of the generated audio. Title is generated by Suno AI.
  - `audio_url` (str): The URL to S3 bucket where audio will be saved after generation is finished.

### 13. Generate Audio Details
`POST /generate_audio_details`

- **Description**: Generates audio titles based on the provided keywords and their respective weights.
- **Request**: (Dict[str, float]): A dictionary where keys are keywords and values are their respective weights.
- **Response**: JSON response containing a list of 2 generated audio titles.

### 14. Quota Information
`GET /quota_information`

- **Description**: Retrieves and displays the SUNO AI quota information.
- **Response**: JSON response containing the quota information.