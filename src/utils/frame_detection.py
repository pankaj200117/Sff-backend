import os
import cv2
import numpy as np
from PIL import Image
from configs.config import KEYFRAMES_DIR
from typing import Tuple
import base64
import logging
import ffmpeg
import subprocess
from io import BytesIO
from src.utils import extract_filename, delete_old_subfolders

logger = logging.getLogger(__name__)
steps_logger = logging.getLogger("steps_info")


def extract_frames(video_path: str, n_frames: int, return_collage: bool) -> None | list:
    """
    Extract frames from the video and save keyframes based on the selection method.

    Args:
        video_path (str): Path to the input video.
        n_frames (int): Number of frames to extract.
        return_collage (bool): Whether to return a collage of 4 frames as a single keyframe.
    """
    try:
        steps_logger.info(f"Started extracting frames from {video_path}.")
        # Delete old frames before extracting new ones
        delete_old_subfolders(KEYFRAMES_DIR)

        saved_frames = uniform(video_path, n_frames, return_collage=return_collage)

        steps_logger.info(f"Successfully extracted frames from {video_path}")
        return saved_frames

    except Exception as e:
        logger.error(f"Failed to extract frames {video_path}: {e}")
        raise e


def canny_edge_detection(frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Perform Canny edge detection on a frame.

    Args:
        frame (np.ndarray): Input frame.

    Returns:
        Tuple[np.ndarray, np.ndarray]: Tuple containing blurred frame and edges.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(src=gray, ksize=(3, 5), sigmaX=0.5)
    edges = cv2.Canny(blurred, 70, 135)
    return blurred, edges


def extract_frame_at_timestamp(file_path, timestamp):
    command = [
        'ffmpeg',
        '-ss', str(timestamp),
        '-i', file_path,
        '-frames:v', '1',
        '-f', 'image2pipe',
        '-vcodec', 'bmp',
        'pipe:1'
    ]

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    frame = Image.open(BytesIO(result.stdout))
    return frame


def uniform(file_path: str, n_frames: int, return_collage: bool) -> list:
    """
    Extract keyframes uniformly from the video using ffmpeg with fast seeking.

    Args:
        file_path (str): Path to the input video.
        n_frames (int): Number of frames to extract.
        return_collage (bool): Whether to return a collage of 4 frames as a single keyframe.

    Returns:
        list: List of paths to extracted keyframes.
    """
    try:
        output_folder = os.path.join(KEYFRAMES_DIR, extract_filename(file_path))
        os.makedirs(output_folder, exist_ok=True)

        # Get total number of frames and duration using ffmpeg
        probe = ffmpeg.probe(file_path)
        for stream in probe['streams']:
            if stream['codec_type'] == 'video':
                frame_width = stream['width']
                frame_height = stream['height']
                frame_rate = stream['r_frame_rate'].split('/')
                frame_rate = int(frame_rate[0]) / int(frame_rate[1])
                duration = float(stream['duration'])
        if duration == 0:
            raise ValueError("Video file is empty")


        step_size = duration / n_frames
        edge_threshold = 500
        extracted_frames = 0
        saved_frames = []
        collage_frames = []

        for i in range(n_frames):
            timestamp = i * step_size
            frame = extract_frame_at_timestamp(file_path, timestamp)
            frame_np = np.array(frame)

            _, edges = canny_edge_detection(frame_np)
            edge_count = np.count_nonzero(edges)

            if edge_count < edge_threshold:
                replaced = False
                for j in range(1, int(step_size * frame_rate) + 1, 3):
                    next_timestamp = min(timestamp + j / frame_rate, duration)
                    new_frame = extract_frame_at_timestamp(file_path, next_timestamp)
                    new_frame_np = np.array(new_frame)
                    _, new_edges = canny_edge_detection(new_frame_np)
                    new_edge_count = np.count_nonzero(new_edges)
                    if new_edge_count >= edge_threshold:
                        frame = new_frame
                        replaced = True
                        break
                if not replaced:
                    continue
            
            if not return_collage:
                output_filename = f'keyframe{extracted_frames + 1}.jpg'
                output_path = os.path.join(output_folder, output_filename)
                frame.save(output_path)
                saved_frames.append(output_path)
                extracted_frames += 1
            
            else:
                collage_frames.append(frame)
                if len(collage_frames) == 4:
                    collage_image = Image.new('RGB', (frame_width * 2, frame_height * 2))

                    collage_image.paste(collage_frames[0], (0, 0))
                    collage_image.paste(collage_frames[1], (frame_width, 0))
                    collage_image.paste(collage_frames[2], (0, frame_height))
                    collage_image.paste(collage_frames[3], (frame_width, frame_height))

                    output_filename = f'keyframe{extracted_frames // 4 + 1}.jpg'
                    output_path = os.path.join(output_folder, output_filename)
                    collage_image.save(output_path)
                    saved_frames.append(output_path)
                    extracted_frames += 4
                    collage_frames = []
                
        # Save any remaining frames if they are less than 4
        if collage_frames:
            new_frame_width = {1: frame_width, 2: frame_width * 2, 3: frame_width * 2}
            new_frame_height = {1: frame_height, 2: frame_height, 3: frame_height * 2}
            collage_image = Image.new('RGB', (new_frame_width[len(collage_frames)], new_frame_height[len(collage_frames)]))

            for idx, frame in enumerate(collage_frames):
                x = (idx % 2) * frame_width
                y = (idx // 2) * frame_height
                collage_image.paste(frame, (x, y))

            output_filename = f'keyframe{extracted_frames // 4 + 1}.jpg'
            output_path = os.path.join(output_folder, output_filename)
            collage_image.save(output_path)
            saved_frames.append(output_path)
            extracted_frames += len(collage_frames)

        return saved_frames
    except Exception as e:
        logger.error(f"Error while processing {file_path}: {e}")
        raise e


def encode_image(file_path: str) -> str:
    """
    Encodes an image file to base64 format.

    Args:
        file_path (str): Path to the image file.

    Returns:
        str: Base64 encoded image.
    """
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


if __name__ == "__main__":
    extract_frames("data/videos/Instacart - Desk Drinks 30sec - 3003 ALT - rev 03 - NO MUSIC.mp4", n_frames=10)
