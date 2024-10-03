import asyncio
import gradio as gr
import os
import logging
from src.analysis import audio, vision, keywords_ext
from src.api_logic.service import search_similar_music_from_audio
from src.api_logic import s3_handler
from src.external_api import suno_api, cyanite
from src.utils import load_settings, save_settings, frame_detection, setup_logging
from configs import config
import requests
import uuid
from src.utils.yt_fetcher import download_audio_from_yt
import subprocess
import json
import moviepy.editor as mpe


setup_logging(log_file_path="logs/app.log")
logger = logging.getLogger(__name__)


GRADIO_PLAYGROUND_SETTINGS_LIST = [
    "number_of_frames", "gpt_model", "extract_frames_as_collage", "model_type_for_keywords_extraction",
    "video_description_prompt", 
    "video_audio_keyword_extraction_prompt_1", "video_audio_keyword_extraction_prompt_2",
    "video_audio_keyword_extraction_prompt_3", "video_audio_keyword_extraction_prompt_4",
    "assistant_keyword_extraction_prompt_1", "assistant_keyword_extraction_prompt_2",
    "assistant_keyword_extraction_prompt_3", "assistant_keyword_extraction_prompt_4",
    "video_summarization_prompt"
]
GRADIO_STORYBOARD_SETTINGS_LIST = [
    "storyboard_description_prompt", "storyboard_keyword_extraction_prompt_1", "storyboard_keyword_extraction_prompt_2", 
    "storyboard_keyword_extraction_prompt_3", "storyboard_keyword_extraction_prompt_4", "storyboard_summarization_prompt"
]


# Gradio components can't accept lists as inputs, so we need to create separate components for each prompt O_o
async def video_audio_analysis(video_path: str, video_description_prompt: str,
                               video_audio_keyword_extraction_prompt_1: str, video_audio_keyword_extraction_prompt_2: str,
                               video_audio_keyword_extraction_prompt_3: str, video_audio_keyword_extraction_prompt_4: str,
                               assistant_keyword_extraction_prompt_1: str, assistant_keyword_extraction_prompt_2,
                               assistant_keyword_extraction_prompt_3, assistant_keyword_extraction_prompt_4,
                               video_summarization_prompt: str, 
                               gpt_model: str, creativity: int, gpt_model_for_extraction: str) -> tuple:
    """
    Runs all processes. Analyzes both video and audio, returning their respective keywords.

    Returns:
        tuple: A tuple containing the keywords for video and audio.
    """
    try:
        logger.info(f"Analyzing video and audio for: {video_path}")
        
        video_analysis_task = asyncio.create_task(vision.video_analysis(
            video_path, video_description_prompt, video_summarization_prompt, gpt_model))

        transcript = await audio.audio_analysis(video_path)
        video_description, video_summary = await video_analysis_task


        # Handle the case where audio text is empty
        if transcript is None:
            transcript = "No speech detected in the video"
            gr.Warning("No speech detected in the video!")

        video_audio_keywords = await video_audio_keyword_extraction_gradio(
            video_audio_keyword_extraction_prompt_1, video_audio_keyword_extraction_prompt_2, 
            video_audio_keyword_extraction_prompt_3, video_audio_keyword_extraction_prompt_4,
            assistant_keyword_extraction_prompt_1, assistant_keyword_extraction_prompt_2,
            assistant_keyword_extraction_prompt_3, assistant_keyword_extraction_prompt_4,
            creativity, video_description, transcript, gpt_model, gpt_model_for_extraction, False)

        logger.info(f"Successfully analyzed video and audio for: {video_path}")
        return video_description, video_audio_keywords, video_summary, transcript

    except Exception as e:
        logger.error(f"Failed to analyze video and audio: {e}")
        gr.Warning(f"Failed to analyze video and audio!")
        return '', '', '', ''


async def storyboard_analysis_gradio(file_path: str, storyboard_description_prompt: str, 
                                     keyword_extraction_prompt_1: str, keyword_extraction_prompt_2: str,
                                     keyword_extraction_prompt_3: str, keyword_extraction_prompt_4: str,
                                     storyboard_summarization_prompt: str, gpt_model: str, creativity: int) -> tuple:
    """
    Wrapper function for analyzing storyboards.
    """
    try:
        logger.info(f"Analyzing storyboard: {file_path}")
        keyword_extraction_prompts = [keyword_extraction_prompt_1, keyword_extraction_prompt_2,
                                      keyword_extraction_prompt_3, keyword_extraction_prompt_4]
        description, keywords, summarization = await vision.analyze_storyboard(file_path, storyboard_description_prompt,
                                                         keyword_extraction_prompts[creativity-1], storyboard_summarization_prompt,
                                                         extract_images=False, gpt_model=gpt_model)
        logger.info(f"Successfully analyzed storyboard: {file_path}")
        return description, keywords, summarization
    except Exception as e:
        logger.error(f"Failed to analyze storyboard: {e}")
        gr.Warning(f"Failed to analyze storyboard!")
        return '', ''


def load_settings_gradio(settings_path: str = None, keys: list = None) -> list:
    """
    Loads settings for the playground or storyboards section.
    Args:
        settings_path (str): Path to the settings file.
        keys (list): List of names of the settings to load.
    """
    settings_dict = load_settings(settings_path)
    if settings_dict is None:
        gr.Warning("Failed to load settings.")
        return None
    
    settings = [settings_dict[key] for key in keys]
    gr.Info("Settings loaded successfully.")
    return settings


def save_settings_gradio(output_path, dict_keys, *args):
    assert len(dict_keys) == len(args), "Number of keys and values do not match!"
    new_settings = {key: value for key, value in zip(dict_keys, args)}
    if not save_settings(output_path, new_settings):
        gr.Warning("Failed to save settings for video analysis!")
    else:
        gr.Info("Settings for video analysis saved successfully.")


def extract_frames_gradio(video_path: str, n_frames: int, return_collage: bool) -> list:
    try:
        frames_ = frame_detection.extract_frames(video_path, n_frames, return_collage=return_collage)
        return frames_
    except Exception as e:
        logger.error(f"Failed to extract frames: {e}")
        gr.Warning(f"Failed to extract frames! Reupload the video.")
        return []


async def video_audio_keyword_extraction_gradio(video_audio_prompt1, video_audio_prompt2, video_audio_prompt3, video_audio_prompt4,
                                                assistant_prompt1, assistant_prompt2, assistant_prompt3, assistant_prompt4,
                                                creativity, video_description, audio_transcription, model, gpt_model_for_extraction,
                                                show_warnings=True):
    if video_description == "" or video_description is None and show_warnings:
        gr.Warning("No video description provided!")
    if audio_transcription == "" or audio_transcription is None or audio_transcription == "No speech detected in the video" and show_warnings:
        gr.Warning("No transcription provided!")
    
    if gpt_model_for_extraction == "OpenAI Assistant (will use gpt-4o)":
        prompt = [assistant_prompt1, assistant_prompt2, assistant_prompt3, assistant_prompt4][creativity - 1]
        return await keywords_ext.video_audio_extraction_assistant(prompt, video_description, audio_transcription)
    
    prompt = [video_audio_prompt1, video_audio_prompt2, video_audio_prompt3, video_audio_prompt4][creativity - 1]
    if gpt_model_for_extraction == "No structured output (will use gpt model specified above)":
        use_structured_outputs = False
    else: # "Structured output (will use gpt-4o-2024-08-06)"
        use_structured_outputs = True
    return await keywords_ext.video_audio_extraction(prompt, video_description, audio_transcription, model, use_structured_outputs)


async def storyboard_keyword_extraction_gradio(prompt1, prompt2, prompt3, prompt4, creativity, description, model):
    if description == "" or description is None:
        gr.Warning("No description provided!")
        return ""
    prompt = [prompt1, prompt2, prompt3, prompt4][creativity - 1]
    return await vision.storyboard_keyword_extraction(prompt, description, model)


async def generate_audio_gradio(prompt: str):
    """
    Generate audio using the Suno API and update the audio components.
    Returns:
    list that contains:
        audio_links: List of audio links, from which audio will be streamed
        titles: List of audio titles
        file_paths: Path to the audio files, where the audio stream will be saved
    """
    logger.info(f"Generating audio using Suno AI for prompt: {prompt}")
    if prompt == "" or prompt is None:
        gr.Warning("No query provided! Please provide an assembled query to generate audio.")
        return [None, None]
    generated_audio = await suno_api.generate_audio_by_prompt(prompt, save_audio=False)

    audio_links = [audio["audio_url"] for audio in generated_audio]
    audio_titles = [gr.update(label=audio["title"]) for audio in generated_audio]
    file_paths = [os.path.join(config.TEMP_PATH, uuid.uuid4().hex + ".mp3") for _ in range(2)]

    logger.info(f"Successfully generated audio using Suno AI.")
    return audio_links + audio_titles + file_paths


def stream_audio_from_links(url1: str, url2: str, file_path1: str, file_path2: str):
    """
    Stream audio from two given URLs and save the audio data to the specified file paths.
    Args:
        url1 (str): The URL of the first audio source.
        url2 (str): The URL of the second audio source.
        file_path1 (str): The file path to save the audio data from the first source.
        file_path2 (str): The file path to save the audio data from the second source.
    Yields:
        tuple: A tuple containing the audio data chunks from the first and second sources.
    """
    response1 = requests.get(url1, stream=True)
    response2 = requests.get(url2, stream=True)


    if response1.status_code == 200 and response2.status_code == 200:
        with open(file_path1, 'wb') as file1, open(file_path2, 'wb') as file2:
            for chunk1, chunk2 in zip(response1.iter_content(chunk_size=8192), response2.iter_content(chunk_size=8192)):
                if chunk1 and chunk2:
                    file1.write(chunk1)
                    file2.write(chunk2)
                    yield chunk1, chunk2


def setup_audio_generation(button, querry, stream_components, file_components, links, file_paths):
    """
    Sets up the audio generation process.
    """
    button.click(
        # make the audio components, that will stream the audio, visible, and the file components invisible
        lambda: [gr.update(visible=True) for _ in range(2)] + [gr.update(visible=False) for _ in range(2)],
        outputs=[*stream_components, *file_components]
    ).then(
        # get audio titles and links for audio streaming
        generate_audio_gradio,
        inputs=[querry],
        outputs=[*links, *stream_components, *file_paths]
    ).then(
        # stream audio from the links
        stream_audio_from_links,
        inputs=[*links, *file_paths],
        outputs=[*stream_components]
    ).then(
        # make the audio components, that will stream the audio, invisible, and the file components visible
        # this is done to allow the user to replay the audio, because gr.Audio(..., streaming=True) does not work properly after the first play
        lambda *args: [gr.update(value=audio, visible=True) for audio in args] + [gr.update(value=None, visible=False) for _ in range(2)],
        inputs=[*file_paths],
        outputs=[*file_components, *stream_components]
    )

def update_tabs(model_for_extraction, creativity):
    """
    Makes the tabs with prompts visible based on the model for extraction.
    """
    structured = model_for_extraction != "OpenAI Assistant (will use gpt-4o)"
    updates = [gr.update(visible=structured), gr.update(visible=not structured),
                gr.Tabs(selected=creativity), gr.Tabs(selected=creativity)]
    return updates


def download_audio_from_yt_gradio(yt_url: str):
    """
    Downloads audio from a given YouTube link.
    Returns:
        str: The path to the downloaded audio file.
    returns filepath two times because the second return value is used in invisible component, to store filepath
    """
    try:
        local_audio_path = download_audio_from_yt(yt_url)
        if local_audio_path:
            return local_audio_path, local_audio_path
        else:
            gr.Warning("Failed to download audio from YouTube!")
            return None, None
    except Exception as e:
        logger.error(f"Failed to download audio from YouTube(link={yt_link}): {e}")
        gr.Warning("Failed to download audio from YouTube!")
        return None, None

async def search_song_from_prompt_gradio(prompt: str) -> str:
    results = await cyanite.songsearch(prompt)
    string = ""
    for res in results:
        string += f"ID: {res['id']}, Title: {res['title']}\n"
    return string

async def search_similar_music_from_audio_gradio(audio_path: str|None):
    if audio_path is None:
        gr.Warning("No audio provided!")
        return None
    
    search_results = await search_similar_music_from_audio(audio_file=None, local_audio_path=audio_path)
    string = ""
    for res in search_results:
        string += f"ID: {res['id']}, Title: {res['title']}\n"
    return string

async def add_cyanite_track_to_video_gradio(cyanite_id: str, video_path: str, mute_original_audio: bool):
    """
    Adds a track from Cyanite to a video.
    """
    try:
        logger.info(f"Adding Cyanite track to video: {video_path}")
        audio_title = await cyanite.get_track_title(cyanite_id)
        if not audio_title:
            gr.Warning("Audio track not found!")
            return None
        audio_filepath = os.path.join(config.TEMP_PATH, "cyanite_"+audio_title).replace(" ", "_")
        if not os.path.exists(audio_filepath):
            download_success = await s3_handler.download_from_s3("mp3/" + audio_title, audio_filepath)
            if not download_success:
                gr.Warning("Failed to download the audio track!")
                return None
        video_title, ext = os.path.splitext(video_path)
        video_title = video_title.replace("\\", "/").split("/")[-1].replace(" ", "_")
        ext = ".mp4"
        output_path = os.path.join(config.TEMP_PATH, f"{video_title}_cyanite{ext}")

        my_clip = mpe.VideoFileClip(video_path)
        audio_background = mpe.AudioFileClip(audio_filepath)
        if audio_background.duration < my_clip.duration:
            silent_audio = mpe.AudioClip(lambda t: [0], duration=my_clip.duration - audio_background.duration)
            audio_background = mpe.concatenate_audioclips([audio_background, silent_audio])
        audio_background = audio_background.subclip(0, my_clip.duration)
        if mute_original_audio:
            final_clip = my_clip.set_audio(audio_background)
        else:
            final_audio = mpe.CompositeAudioClip([my_clip.audio, audio_background])
            final_clip = my_clip.set_audio(final_audio)
        final_clip.resize(width=480).write_videofile(output_path, logger=None, codec='libx264', fps=24)
        logger.info(f"Successfully added Cyanite track to video: {video_path}")
        return output_path

    except Exception as e:
        logger.exception(f"Failed to add Cyanite track to video: {e}")
        gr.Warning("Failed to add Cyanite track to video!")
        return None


custom_css = """
    #params .tabs {
        display: flex;
        flex-direction: column;
        flex-grow: 1;
    }
    #params .tabitem[style="display: block;"] {
        flex-grow: 1;
        display: flex !important;
    }
    #params .gap {
        flex-grow: 1;
    }
    #params .form {
        flex-grow: 1 !important;
    }
    #params .form > :last-child{
        flex-grow: 1;
    }
"""


with gr.Blocks(title='MultiMediaAI', css=custom_css) as app:
    with gr.Tab("Video Input"):
        with gr.Row():
            with gr.Column(elem_id="params"):
                video = gr.Video(label="Input Video", height=512, width=800)
                with gr.Row():
                    n_frames = gr.Slider(minimum=1, maximum=40, label="Number of Frames.", value=10, step=1)
                    creativity_slider_main = gr.Slider(minimum=1, maximum=4, label="Creativity", value=1, step=1, interactive=True)
                with gr.Row():
                    with gr.Column(scale=3):
                        gpt_model_name = gr.Radio(choices=["gpt-4o", "gpt-4-turbo", "gpt-4 + vision"], 
                                                  label="GPT Model (used for video description and summarization)", value="gpt-4o", interactive=True)
                    with gr.Column(scale=1):
                        extract_as_collage = gr.Checkbox(label="Extract frames as Collage", interactive=True)
                with gr.Row():
                    gpt_model_for_extraction = gr.Dropdown(label="Model Type (used for keywords extraction)", choices=[
                        "No structured output (will use gpt model specified above)", 
                        "Structured output (will use gpt-4o-2024-08-06)",
                        "OpenAI Assistant (will use gpt-4o)"], 
                        value="No structured output (will use gpt model specified above)",
                        interactive=True, allow_custom_value=False)
            with gr.Column(elem_id="params"):
                frames = gr.Gallery(label='Frames', height=512)
                audio_transcription = gr.Textbox(label="Audio Transcription", lines=8, interactive=True)

        with gr.Row():
            video_analysis_btn = gr.Button(value="Run All Processes", interactive=True)


        with gr.Row():
            with gr.Column(elem_id="params"):
                video_description_prompt = gr.Textbox(lines=8, label="Video Description Prompt", interactive=True)
            with gr.Column(elem_id="params"):
                video_description_output = gr.Textbox(lines=8, label="Video Description")
        with gr.Row():
            describe_video_btn = gr.Button(value="Run Video Description Prompt", interactive=True)


        video_and_audio_creativity = gr.State(value=1)
        VIDEO_AUDIO_KEYWORD_PROMPTS = []
        ASSISTANT_KEYWORD_PROMPTS = []

        with gr.Row():
            gr.Markdown("Extract keywords from video description and audio transcription in one prompt.")
        with gr.Row():
            with gr.Column(elem_id="params"):
                with gr.Row() as video_audio_keywords_tabs_row: # Need to wrap the tabs in a row to be able to hide them
                    with gr.Tabs() as video_audio_keywords_tabs:
                        for i in range(1, 5):
                            with gr.TabItem(str(i), id=i) as video_audio_keywords_tab:
                                VIDEO_AUDIO_KEYWORD_PROMPTS.append(gr.Textbox(lines=8, label=f"Keyword Extraction Prompt #{i}",
                                                                        interactive=True))
                                # when tab is selected, set the creativity level to tab number
                                video_audio_keywords_tab.select(lambda i=i: i, None, video_and_audio_creativity)
                with gr.Row() as assistant_keywords_tabs_row:  # Need to wrap the tabs in a row to be able to hide them
                    with gr.Tabs() as assistant_keywords_tabs:
                        for i in range(1, 5):
                            with gr.TabItem(str(i), id=i) as assistant_keywords_tab:
                                ASSISTANT_KEYWORD_PROMPTS.append(gr.Textbox(lines=8, label=f"Assistant Keyword Extraction Prompt #{i}",
                                                                        interactive=True))
                                # when tab is selected, set the creativity level to tab number
                                assistant_keywords_tab.select(lambda i=i: i, None, video_and_audio_creativity)

            with gr.Column(elem_id="params"):
                with gr.Row(): pass
                with gr.Row(): pass
                video_audio_keywords_output = gr.Textbox(lines=8, label="Video and Audio Keywords")
            
        with gr.Row():
            video_audio_keyword_extraction_btn = gr.Button(value="Run Video and Audio Keyword Prompt", interactive=True)

        with gr.Row():
            with gr.Column(elem_id="params"):
                video_summarization_prompt = gr.Textbox(lines=2, label="Video Summarization Prompt",
                                                        interactive=True)
            with gr.Column(elem_id="params"):
                video_summarization_output = gr.Textbox(lines=3, label="Video Summarization")
            
        with gr.Row():
            video_summarization_btn = gr.Button(value="Run Video Summary Prompt", interactive=True)

        with gr.Row():
            with gr.Column(elem_id="params"):
                assembled_query = gr.Textbox(lines=4, label="Assembled Query", interactive=True)
            with gr.Column(elem_id="params"):
                track_list = gr.Textbox(lines=4, label="Track List", interactive=False)
        with gr.Row():
            assemble_query_btn = gr.Button(value="Assemble Query and Return Tracks", interactive=True)

        with gr.Row():
            with gr.Column(elem_id="params"):
                with gr.Row():
                    yt_link = gr.Textbox(label="YouTube Link", placeholder="Paste the YouTube link here", interactive=True)
                    yt_audio_local_filepath = gr.Textbox(visible=False)
                    dowload_from_yt_btn = gr.Button(value="Download audio", interactive=True)
                with gr.Row():
                    audio_from_yt = gr.Audio(label="Audio from YouTube", interactive=False)
            with gr.Column(elem_id="params"):
                track_list_from_yt = gr.Textbox(lines=6, label="Track List", interactive=False)
        with gr.Row():
            search_audio_from_yt_btn = gr.Button(value="Search Tracks from YouTube Audio", interactive=True)

        with gr.Row():
            with gr.Column():
                cyanite_track_id = gr.Textbox(label="Track ID", placeholder="Enter the track ID here", interactive=True)
                with gr.Row():
                    mute_original_audio = gr.Checkbox(label="Mute Original Audio", interactive=True)
            with gr.Column():
                video_with_cyanite_track = gr.Video(label="Video with Cyanite Track", height=448, width=800, interactive=False)
        with gr.Row():
            add_track_to_video_btn = gr.Button(value="Add Track to Video", interactive=True)


        with gr.Row():
            with gr.Column():
                generated_audio_1_link = gr.Textbox(visible=False)
                generated_audio_1_filepath = gr.Textbox(visible=False)
                generated_audio_1_stream = gr.Audio(label="Generated Audio 1", interactive=False, streaming=True, format="bytes")
                generated_audio_1_from_file = gr.Audio(label="Generated Audio 1", interactive=False, visible=False)
            with gr.Column():
                generated_audio_2_link = gr.Textbox(visible=False)
                generated_audio_2_filepath = gr.Textbox(visible=False)
                generated_audio_2_stream = gr.Audio(label="Generated Audio 2", interactive=False, streaming=True, format="bytes")
                generated_audio_2_from_file = gr.Audio(label="Generated Audio 2", interactive=False, visible=False)
        
        with gr.Row():
            generate_audio_btn = gr.Button(value="Generate Audio using Suno AI", interactive=True)

        with gr.Row():
            save_settings_playground_btn = gr.Button(value="Save Settings", interactive=True)
            load_latest_playground_btn = gr.Button(value="Revert To Current Settings", interactive=True)


    # Storyboards Tab
    with gr.Tab("Storyboard Input"):
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Row():
                    gr.Markdown("### Upload a storyboard *pdf file and wait for the pages to load.")
                with gr.Row():
                    storyboard = gr.File(label="Storyboard File",  interactive=True)
                with gr.Row():
                    storyboard_creativity_slider = gr.Slider(minimum=1, maximum=4, label="Creativity", value=1, step=1, interactive=True)
            with gr.Column(scale=6):
                storyboard_pages = gr.Gallery(label='Pages', height=512)

        with gr.Row():
            analyse_storyboard_btn = gr.Button(value="Run All Processes", interactive=True)
        with gr.Row():
            with gr.Column(elem_id="params"):
                storyboard_description_prompt = gr.Textbox(lines=6, label="Storyboard Description Prompt",
                                                           interactive=True)
            with gr.Column(elem_id="params"):
                storyboard_description_output = gr.Textbox(lines=8, label="Storyboard Description")
        with gr.Row():
            storyboard_description_btn = gr.Button(value="Run File Description Prompt", interactive=True)

        storyboard_creativity = gr.State(value=1)
        STORYBOARD_KEYWORD_PROMPTS = []
        with gr.Row():
            with gr.Column(elem_id="params"):
                with gr.Tabs() as storyboard_keywords_tabs:
                    for i in range(1, 5):
                        with gr.TabItem(str(i), id=i) as storyboard_keywords_tab:
                            STORYBOARD_KEYWORD_PROMPTS.append(gr.Textbox(lines=6, label=f"Storyboard Keyword Extraction Prompt #{i}",
                                                                    interactive=True))
                            # when tab is selected, set the creativity level to tab number
                            storyboard_keywords_tab.select(lambda i=i: i, None, storyboard_creativity)

            with gr.Column(elem_id="params"):
                storyboard_keywords_output = gr.Textbox(lines=2, label="Storyboard Keywords")
        with gr.Row():
            storyboard_keyword_extraction_btn = gr.Button(value="Run File Keyword Prompt",
                                                              interactive=True)
        with gr.Row():
            with gr.Column(elem_id="params"):
                storyboard_summarization_prompt = gr.Textbox(lines=3, label="Storyboard Summary Prompt",
                                                              interactive=True)
            with gr.Column(elem_id="params"):
                storyboard_summarization_output = gr.Textbox(lines=3, label="Storyboard Summary")
        with gr.Row(): 
            storyboard_summarization_btn = gr.Button(value="Run File Summary Prompt", interactive=True)

        with gr.Row():
            with gr.Column(elem_id="params"):
                assembled_query_storyboard = gr.Textbox(lines=4, label="Assembled Query", interactive=True)
            with gr.Column(elem_id="params"):
                track_list_storyboard = gr.Textbox(lines=4, label="Track List", interactive=False)
        with gr.Row():
            assemble_query_storyboard_btn = gr.Button(value="Assemble Query and Return Tracks", interactive=True)
        
        with gr.Row():
            with gr.Column():
                generated_audio_1_link_storyboard = gr.Textbox(visible=False)
                generated_audio_1_filepath_storyboard = gr.Textbox(visible=False)
                generated_audio_1_stream_storyboard = gr.Audio(label="Generated Audio 1", interactive=False, streaming=True, format="bytes")
                generated_audio_1_from_file_storyboard = gr.Audio(label="Generated Audio 1", interactive=False, visible=False)
            with gr.Column():
                generated_audio_2_link_storyboard = gr.Textbox(visible=False)
                generated_audio_2_filepath_storyboard = gr.Textbox(visible=False)
                generated_audio_2_stream_storyboard = gr.Audio(label="Generated Audio 2", interactive=False, streaming=True, format="bytes")
                generated_audio_2_from_file_storyboard = gr.Audio(label="Generated Audio 2", interactive=False, visible=False)
        
        with gr.Row():
            generate_audio_btn_storyboard = gr.Button(value="Generate Audio using Suno AI", interactive=True)

        with gr.Row():
            save_settings_storyboards_btn = gr.Button(value="Save Settings", interactive=True)
            load_latest_storyboards_btn = gr.Button(value="Revert To Current Settings", interactive=True)


    video.upload(
        extract_frames_gradio,
        inputs=[video, n_frames, extract_as_collage],
        outputs=[frames]
    )

    n_frames.release(
        extract_frames_gradio,
        inputs=[video, n_frames, extract_as_collage],
        outputs=[frames]
    )

    extract_as_collage.input(
        extract_frames_gradio,
        inputs=[video, n_frames, extract_as_collage],
        outputs=[frames]
    )

    describe_video_btn.click(
        vision.describe_video,
        inputs=[video, video_description_prompt, gpt_model_name],
        outputs=[video_description_output]
    )

    video_audio_keyword_extraction_btn.click(
        video_audio_keyword_extraction_gradio,
        inputs=[*VIDEO_AUDIO_KEYWORD_PROMPTS, *ASSISTANT_KEYWORD_PROMPTS, video_and_audio_creativity, 
                video_description_output, audio_transcription, 
                gpt_model_name, gpt_model_for_extraction],
        outputs=[video_audio_keywords_output]
    )

    video_summarization_btn.click(
        vision.video_summarization,
        inputs=[video_summarization_prompt, video_description_output, gpt_model_name],
        outputs=[video_summarization_output]
    )

    assemble_query_btn.click(
        lambda keywords, summary: keywords + ". " + summary,
        inputs=[video_audio_keywords_output, video_summarization_output],
        outputs=[assembled_query]
    ).then(
        search_song_from_prompt_gradio,
        inputs=[assembled_query],
        outputs=[track_list]
    )

    setup_audio_generation(generate_audio_btn, assembled_query, 
                           [generated_audio_1_stream, generated_audio_2_stream],
                           [generated_audio_1_from_file, generated_audio_2_from_file],
                           [generated_audio_1_link, generated_audio_2_link],
                           [generated_audio_1_filepath, generated_audio_2_filepath])


    save_settings_playground_btn.click(
        save_settings_gradio,
        inputs=[gr.State(config.GRADIO_LATEST_SETTINGS_PATH),  gr.State(GRADIO_PLAYGROUND_SETTINGS_LIST),
                n_frames, gpt_model_name, extract_as_collage, gpt_model_for_extraction, video_description_prompt, 
                *VIDEO_AUDIO_KEYWORD_PROMPTS, *ASSISTANT_KEYWORD_PROMPTS, video_summarization_prompt],
        outputs=None
    )


    load_latest_playground_btn.click(
        load_settings_gradio,
        inputs=[gr.State(config.GRADIO_LATEST_SETTINGS_PATH), gr.State(GRADIO_PLAYGROUND_SETTINGS_LIST)],
        outputs=[n_frames, gpt_model_name, extract_as_collage, gpt_model_for_extraction, video_description_prompt, 
                 *VIDEO_AUDIO_KEYWORD_PROMPTS, *ASSISTANT_KEYWORD_PROMPTS, video_summarization_prompt]
    )


    video_analysis_btn.click(
        video_audio_analysis,
        inputs=[
            video, video_description_prompt, *VIDEO_AUDIO_KEYWORD_PROMPTS, *ASSISTANT_KEYWORD_PROMPTS,
            video_summarization_prompt, gpt_model_name, creativity_slider_main, gpt_model_for_extraction
        ],
        outputs=[video_description_output, video_audio_keywords_output, video_summarization_output,
                 audio_transcription]
    ).then(
        lambda keywords, summary: keywords + ". " + summary,
        inputs=[video_audio_keywords_output, video_summarization_output],
        outputs=[assembled_query]
    ).then(
        search_song_from_prompt_gradio,
        inputs=[assembled_query],
        outputs=[track_list]
    )

    creativity_slider_main.change(
        lambda *tab_ids: [gr.Tabs(selected=tab_id) for tab_id in tab_ids], # select audio keywords tab based on the creativity level
        inputs=[creativity_slider_main, creativity_slider_main], outputs=[video_audio_keywords_tabs, assistant_keywords_tabs]
    )

    gpt_model_for_extraction.change(
        update_tabs,
        inputs=[gpt_model_for_extraction, creativity_slider_main],
        outputs=[video_audio_keywords_tabs_row, assistant_keywords_tabs_row,
                 video_audio_keywords_tabs, assistant_keywords_tabs]
    )

    dowload_from_yt_btn.click(
        download_audio_from_yt_gradio,
        inputs=[yt_link],
        outputs=[audio_from_yt, yt_audio_local_filepath]
    )

    search_audio_from_yt_btn.click(
        search_similar_music_from_audio_gradio,
        inputs=[yt_audio_local_filepath],
        outputs=[track_list_from_yt]
    )

    add_track_to_video_btn.click(
        add_cyanite_track_to_video_gradio,
        inputs=[cyanite_track_id, video, mute_original_audio],
        outputs=[video_with_cyanite_track]
    )

    # storyboard tab
    storyboard_description_btn.click(
        vision.describe_storyboard,
        inputs=[storyboard, storyboard_description_prompt, gpt_model_name],
        outputs=[storyboard_description_output]
    )

    storyboard_keyword_extraction_btn.click(
        storyboard_keyword_extraction_gradio,
        inputs=[*STORYBOARD_KEYWORD_PROMPTS, storyboard_creativity, storyboard_description_output, gpt_model_name],
        outputs=[storyboard_keywords_output]
    )

    storyboard.upload(
        vision.pdf_to_images,
        inputs=[storyboard],
        outputs=[storyboard_pages]
    )

    analyse_storyboard_btn.click(
        storyboard_analysis_gradio,
        inputs=[storyboard, storyboard_description_prompt, *STORYBOARD_KEYWORD_PROMPTS,
                storyboard_summarization_prompt, gpt_model_name, storyboard_creativity_slider],
        outputs=[storyboard_description_output, storyboard_keywords_output, storyboard_summarization_output]
    ).then(
        lambda keywords, description: keywords + ". " + description,
        inputs=[storyboard_keywords_output, storyboard_summarization_output],
        outputs=[assembled_query_storyboard]
    ).then(
        search_song_from_prompt_gradio,
        inputs=[assembled_query_storyboard],
        outputs=[track_list_storyboard]
    )

    storyboard_creativity_slider.change(
        lambda tab_id: gr.Tabs(selected=tab_id), # select keywords tab based on the creativity level
        inputs=[storyboard_creativity_slider], outputs=[storyboard_keywords_tabs]
    )

    storyboard_summarization_btn.click(
        vision.storyboard_summarization,
        inputs=[storyboard_summarization_prompt, storyboard_description_output, gpt_model_name],
        outputs=[storyboard_summarization_output]
    )

    assemble_query_storyboard_btn.click(
        lambda keywords, description: keywords + ". " + description,
        inputs=[storyboard_keywords_output, storyboard_summarization_output],
        outputs=[assembled_query_storyboard]
    ).then(
        search_song_from_prompt_gradio,
        inputs=[assembled_query_storyboard],
        outputs=[track_list_storyboard]
    )

    setup_audio_generation(generate_audio_btn_storyboard, assembled_query_storyboard, 
                           [generated_audio_1_stream_storyboard, generated_audio_2_stream_storyboard],
                           [generated_audio_1_from_file_storyboard, generated_audio_2_from_file_storyboard],
                           [generated_audio_1_link_storyboard, generated_audio_2_link_storyboard],
                           [generated_audio_1_filepath_storyboard, generated_audio_2_filepath_storyboard])
    

    save_settings_storyboards_btn.click(
        save_settings_gradio,
        inputs=[gr.State(config.GRADIO_LATEST_SETTINGS_PATH), gr.State(GRADIO_STORYBOARD_SETTINGS_LIST), 
                storyboard_description_prompt, *STORYBOARD_KEYWORD_PROMPTS, storyboard_summarization_prompt],
        outputs=None
    )


    load_latest_storyboards_btn.click(
        load_settings_gradio,
        inputs=[gr.State(config.GRADIO_LATEST_SETTINGS_PATH), gr.State(GRADIO_STORYBOARD_SETTINGS_LIST)],
        outputs=[storyboard_description_prompt, *STORYBOARD_KEYWORD_PROMPTS, storyboard_summarization_prompt]
    )

    app.load(
        load_settings_gradio, 
        inputs=[gr.State(config.GRADIO_LATEST_SETTINGS_PATH), 
                gr.State(GRADIO_PLAYGROUND_SETTINGS_LIST + GRADIO_STORYBOARD_SETTINGS_LIST)],
        outputs=[n_frames, gpt_model_name, extract_as_collage, gpt_model_for_extraction, video_description_prompt, 
                 *VIDEO_AUDIO_KEYWORD_PROMPTS, *ASSISTANT_KEYWORD_PROMPTS, video_summarization_prompt, 
                 storyboard_description_prompt, *STORYBOARD_KEYWORD_PROMPTS, storyboard_summarization_prompt]
    ).then(
        update_tabs,
        inputs=[gpt_model_for_extraction, creativity_slider_main],
        outputs=[video_audio_keywords_tabs_row, assistant_keywords_tabs_row,
                 video_audio_keywords_tabs, assistant_keywords_tabs]
    )


if __name__ == "__main__":
    logger.info("Starting the Gradio server.")
    os.makedirs(config.UPLOAD_VIDEO_DIR, exist_ok=True)
    os.makedirs(config.TEMP_PATH, exist_ok=True)
    os.makedirs(config.UPLOAD_AUDIO_DIR, exist_ok=True)
    os.makedirs(config.STORYBOARD_EXTRACTION_DIR, exist_ok=True)
    app.launch(
        server_name='127.0.0.1',
        server_port=config.GRADIO_PORT,
        root_path=config.GRADIO_ROOT_PATH,
        auth=("admin", os.getenv("GRADIO_PASSWORD"))
    )
