from src.analysis import client
from pydantic import BaseModel
from configs import config
from typing import List
import asyncio
import logging
import os

logger = logging.getLogger(__name__)
steps_logger = logging.getLogger("steps_info")

class KeywordList(BaseModel):
    keywords: list[str]

async def video_audio_extraction(keyword_extraction_prompt: str, 
                                 video_description: str, 
                                 audio_transcription: str, 
                                 gpt_model: str = 'gpt-4o',
                                 structured_output: bool = False):
    """
    Extracts keywords from the video description and audio transcription.

    Args:
        keyword_extraction_prompt (str): Prompt for extracting keywords.
        video_description (str): The description of the video
        audio_transcription (str): The transcription of the audio
        gpt_model (str): The GPT model to use for keyword extraction
        structured_output (bool): Whether to return structured output (list of keywords)

    Returns:
        str: Keywords extracted from the video description and audio transcription.
    """
    steps_logger.info(f"Started extracting keywords from video description and audio transcription.")
    if audio_transcription is None: 
        audio_transcription = ""
    contents = [{"type": "text", "text": keyword_extraction_prompt}, 
                {"type": "text", "text": "Video Description: " + video_description},
                {"type": "text", "text": "Audio Transcription: " + audio_transcription}]
    
    if not structured_output:
        if gpt_model == "gpt-4 + vision":
            gpt_model = "gpt-4"
        
        response = await client.chat.completions.create(
            model=gpt_model,
            messages=[{"role": "user", "content": contents}],
        )

        keywords = response.choices[0].message.content.rstrip(",").replace(".", "").lower()
        keywords = keywords.lower().strip(" ,")
    else:
        response = await client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[{"role": "user", "content": contents}],
            response_format=KeywordList
        )
        keywords = ", ".join(response.choices[0].message.parsed.keywords)
    steps_logger.info(f"Finished extracting keywords from video description and audio transcription.\nKeywords: {keywords}")
    return keywords


async def video_audio_creative_extraction(extraction_function,
                                          keywords_extraction_prompts: List[str],
                                          *function_args):
    """
    Extracts keywords from the video description and audio transcription.

    Args:
        extraction_function (function): The function to extract keywords.
        keywords_extraction_prompts (List[str]): Prompts for extracting keywords.
        *function_args: Arguments for the extraction function.
    
    Returns:
        str: Keywords extracted from the video description and audio transcription
    """
    keyword_extraction_tasks = []
    for prompt in keywords_extraction_prompts:
        keyword_extraction_tasks.append(asyncio.create_task(
            extraction_function(prompt, *function_args)))
    keywords = await asyncio.gather(*keyword_extraction_tasks)
    return keywords


async def video_audio_extraction_assistant(keyword_extraction_prompt: str,
                                           video_description: str, 
                                           audio_transcription: str):
    """
    Extracts keywords from the video description and audio transcription using the OpenAI Assistant.

    Args:
        keyword_extraction_prompt (str): Prompt for extracting keywords.
        video_description (str): The description of the video
        audio_transcription (str): The transcription of the audio
    
    Returns:
        str: Keywords extracted from the video description and audio transcription.
    """
    if audio_transcription is None or audio_transcription == "":
        audio_transcription = "No speech detected in the video."
    thread = await client.beta.threads.create()
    
    message = await client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="Based on knowledge.json, recommend keywords for this video. Video description: " + video_description + "\nAudio transcription: " + audio_transcription,
        attachments = [{"file_id": os.getenv("ASSISTANT_KNOWLEDGE_FILE_ID"), "tools": [{"type": "file_search"}]}]
    )

    run = await client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=os.getenv("ASSISTANT_ID"),
        tools=[{"type": "file_search"}],
        instructions=keyword_extraction_prompt
    )

    while not run.status == "completed":
        await asyncio.sleep(5)
        run = await client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        if run.status == "failed":
            print(run)
            raise Exception("Assistant run failed.")

    messages = await client.beta.threads.messages.list(
        thread_id=thread.id
    )

    keywords = messages.data[0].content[0].text.value.split("【")[0].strip()
    return keywords