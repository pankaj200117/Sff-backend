# Gradio App

## Description
The Gradio app provides an interactive web interface to analyze both video and audio content to extract keywords, 
which can be used to identify suitable songs based on user-provided inputs.

## Tabs
### Video Input
- Purpose: The main tab is designed to test the main pipeline with keyword extraction.
- Features:
  - Upload video files.
  - Extract frames from the video.
  - Analyze the video and audio.
  - Display audio and video analysis results.
  - Apply weights to keywords.
  - Search for music based on keywords.
  - Modify prompts.
  - Run each step of the pipeline separately.
  - Save new settings.


### Storyboard Input
- Purpose: The tab allows users to analyze storyboards and extract keywords.
- Features:
  - Get storyboard description.
  - Extract keywords from the storyboard.
  - Modify prompts.
  - Save new settings.

## Settings
Gradio app uses a settings file, path to which is specified in `configs/config.py`:
- Latest settings - stores the most recent modifications made to the prompts and settings in the Gradio app on playground tab. Loaded when the app starts.
```python
GRADIO_SETTINGS_PATH = "configs/latest_settings.json"
```
Don't forget to set the password for the Gradio app in the `.env` file:
```bash
GRADIO_PASSWORD = "password"
```

## Usage
To run the Gradio app, execute the following command in your terminal:
```sh
python -m src.app
```
Access the application interface via your web browser at `http://127.0.0.1:5002`.

Port 5002 is used by default and can be changed in the `configs/config.py` file.

Logs will be printed to the console and saved to `logs/app.log`. Note, that log file will have more detailed information
about each step of the process.