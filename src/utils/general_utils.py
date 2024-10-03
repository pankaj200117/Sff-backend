import json
import logging
import os
import time
import shutil

logger = logging.getLogger(__name__)


def load_settings(settings_path: str = "configs/default_settings.json"):
    """
    Load settings from a JSON file.

    Args:
        settings_path (str): The path to the settings JSON file.

    Returns:
        dict: The settings as a dictionary.
        None: If the file is not found, an error message is printed, and None is returned.
    """
    try:
        with open(settings_path, 'r') as file:
            settings = json.load(file)
        return settings

    except FileNotFoundError as e:
        logger.error(f"Error: {settings_path} not found.")
        return None


def save_settings(output_path: str, new_settings: dict) -> bool:
    """
    Saves settings to a JSON file.
    Will save new settings to the file if it already exists.
    Returns True if the settings are saved successfully, otherwise False.
    """
    try:
        if os.path.exists(output_path):
            previous_settings = load_settings(output_path)
            for key, value in new_settings.items():
                previous_settings[key] = value
            new_settings = previous_settings

        with open(output_path, 'w') as file:
            json.dump(new_settings, file, indent=4)
        return True

    except Exception as e:
        logger.error(f"Error saving settings to {output_path}: {e}")
        return False


def extract_filename(file_path: str) -> str:
    """
    Extracts filename from the given file path.

    Args:
        file_path (str): Input file path.

    Returns:
        str: Extracted filename.
    """
    base_name = os.path.basename(file_path)
    return os.path.splitext(base_name)[0]


def delete_old_files(folder_path: str) -> None:
    """
    Delete old files from the specified folder.

    Args:
        folder_path (str): Path to the folder containing frames.
    """
    current_time = time.time()
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        creation_time = os.path.getctime(file_path)
        if current_time - creation_time > 3600:  # 3600 seconds = 1 hour
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error during deleting {file_path}: {e}")



def delete_old_subfolders(folder_path: str) -> None:
    """
    Delete old subfolders from the specified folder.

    Args:
        folder_path (str): Path to the folder containing frames.
    """
    try:
        current_time = time.time()
        for subfolder_name in os.listdir(folder_path):
            subfolder_path = os.path.join(folder_path, subfolder_name)
            creation_time = os.path.getctime(subfolder_path)
            if current_time - creation_time > 3600:  # 3600 seconds = 1 hour
                shutil.rmtree(subfolder_path, ignore_errors=True)
    except Exception as e:
        logger.error(f"Error during deleting old subfolders in {folder_path}: {e}")