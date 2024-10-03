import os
from src.utils import extract_filename, delete_old_subfolders
from src.utils.frame_detection import encode_image
from src.analysis import client
from configs.config import STORYBOARD_EXTRACTION_DIR
from pdf2image import convert_from_path
import logging
import asyncio
from typing import List

logger = logging.getLogger(__name__)
steps_logger = logging.getLogger("steps_info")


def pdf_to_images(file_path: str):
    """
    Converts a PDF file to images and saves them in a folder with the same name as the PDF file.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        list: List of extracted images
    """
    try:
        steps_logger.info(f"Started extracting images from storyboard {file_path}")
        delete_old_subfolders(STORYBOARD_EXTRACTION_DIR)
        output_folder = os.path.join(STORYBOARD_EXTRACTION_DIR, extract_filename(file_path))
        os.makedirs(output_folder, exist_ok=True)

        images = convert_from_path(file_path, size=(512, 512))

        for i in range(len(images)):
            images[i].save(os.path.join(output_folder, 'page' + str(i) + '.jpg'), 'JPEG')

        return images
    except Exception as e:
        logger.exception(f"Error while extracting images from storyboard {file_path}: {e}")
        raise e


async def analyze_storyboard(file_path : str, storyboard_description_prompt: str, keyword_extraction_prompt: str | List, 
                             storyboard_summarization_prompt: str, extract_images=True, gpt_model: str ='gpt-4o'):
    """
    Analyzes a storyboard by generating a description, extracting keywords and summarizing the description.

    Args:
        file_path (str): Path to the storyboard PDF file.
        storyboard_description_prompt (str): Prompt for generating the storyboard description.
        keyword_extraction_prompt (str | List): Prompt for extracting keywords from the storyboard description.
            if multiple prompts are provided, the function will return a list of keywords, one for each prompt.
        storyboard_summarization_prompt (str): Prompt for summarizing the storyboard description.
        extract_images (bool): Whether to extract images from the storyboard PDF file.
        gpt_model (str): OpenAI's GPT model to use for analysis.

    Returns:
        tuple: Contains the storyboard description, extracted keywords and summarization.
        If an error occurs, returns the exception.
    """
    try:
        steps_logger.info(f"Started analyzing storyboard for {file_path}")
        if extract_images:
            pdf_to_images(file_path)
        description = await describe_storyboard(file_path, storyboard_description_prompt, gpt_model)
        summary_task = asyncio.create_task(storyboard_summarization(storyboard_summarization_prompt, description, gpt_model))

        if isinstance(keyword_extraction_prompt, str): 
            keywords = (await storyboard_keyword_extraction(keyword_extraction_prompt, description, gpt_model))
        else:
            keywords_tasks = []
            for prompt in keyword_extraction_prompt:
                keywords_tasks.append(asyncio.create_task(storyboard_keyword_extraction(prompt, description, gpt_model)))
            keywords = await asyncio.gather(*keywords_tasks)

        summary = await summary_task
        steps_logger.info(f"Finished analyzing storyboard for {file_path}.")
        return description, keywords, summary

    except Exception as e:
        logger.exception(f"Error while analyzing storyboard {file_path}: {e}")
        raise e


async def describe_storyboard(file_path: str, storyboard_description_prompt: str, gpt_model='gpt-4o') -> str:
    """
    Generates a description of the storyboard based on extracted images.

    Args:
        file_path (str): Path to the storyboard PDF file.
        storyboard_description_prompt (str): Prompt for generating the storyboard description.

    Returns:
        str: Description of the storyboard.
    """
    # Extract images from the storyboard PDF file
    storyboard_folder = os.path.join(STORYBOARD_EXTRACTION_DIR, extract_filename(file_path))
    storyboard_pages = [encode_image(os.path.join(storyboard_folder, f)) for f in os.listdir(storyboard_folder) if f.endswith('.jpg')]

    contents = [{"type": "text", "text": storyboard_description_prompt}] + [
        {'type': 'image_url', 'image_url': {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "low"}} for base64_image in
        storyboard_pages]
    
    if gpt_model == "gpt-4 + vision": 
        gpt_model = "gpt-4-vision-preview"

    response = await client.chat.completions.create(
        model=gpt_model,
        messages=[{"role": "user", "content": contents}],
        max_tokens=700
    )

    description = response.choices[0].message.content
    steps_logger.info(f"Finished describing storyboard.\Storyboard Description: {description}")
    return description


async def storyboard_keyword_extraction(keyword_extraction_prompt: str, storyboard_description: str, gpt_model='gpt-4o') -> list:
    """
    Extracts keywords from the storyboard description using OpenAI's GPT model.

    Args:
        keyword_extraction_prompt (str): Prompt for extracting keywords from the storyboard description.
        storyboard_description (str): Description of the storyboard.

    Returns:
        list: Extracted keywords.
    """
    contents = [{"type": "text", "text": keyword_extraction_prompt}] + [{"type": "text", "text": storyboard_description}]

    if gpt_model == "gpt-4 + vision": 
        gpt_model = "gpt-4"

    response = await client.chat.completions.create(
        model=gpt_model,
        messages=[{"role": "user", "content": contents}],
    )

    keywords = response.choices[0].message.content.rstrip(",").replace(".", "").lower()
    steps_logger.info(f"Finished extracting keywords from storyboard.\nKeywords: {keywords}")
    return keywords


async def storyboard_summarization(storyboard_summarization_prompt, storyboard_description_output, gpt_model='gpt-4o'):
    """
    Summarizes the storyboard description using OpenAI's GPT model.
    Args:
        storyboard_summarization_prompt (str): Prompt for summarizing the storyboard description.
        storyboard_description_output (str): Description of the storyboard.
    Returns:
        str: Summarized description of the storyboard.
    """
    contents = [{"type": "text", "text": storyboard_summarization_prompt}] + [{"type": "text", "text": storyboard_description_output}]

    if gpt_model == "gpt-4 + vision": 
        gpt_model = "gpt-4"

    response = await client.chat.completions.create(
        model=gpt_model,
        max_tokens=500,
        messages=[{"role": "user", "content": contents}],
    )

    summarization = response.choices[0].message.content

    return summarization


# def extract_text_from_pdf(inputpath):
#     doc = fitz.open(inputpath)
#     all_text = ""
#     for page in doc:
#         text = page.get_text()
#         all_text += text + "\n"
#     all_text = all_text.strip()
#     return all_text