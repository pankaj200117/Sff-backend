import requests
from typing import Dict, Union
import time

# Set the base URL and video file path for the FastAPI application
BASE_URL: str = "http://127.0.0.1:5010" # https://api.sushiandfrenchfries.com
VIDEO_FILE_PATH: str = "sample_videos/EVERY_NIGHT__15__EN_1006_no_music.mp4"  # Replace with the actual path to the video file
MUSIC_FILE_PATH: str = "sample_audio/0bikalam download1music.ir (1).mp3"  # Replace with the actual path to the music file

def make_request(url, method, **kwargs):
    """
    Make an HTTP request and print the duration.

    Args:
        url (str): The URL to make the request to.
        method (str): The HTTP method for the request (e.g., 'post', 'get').
        **kwargs: Additional keyword arguments to pass to `requests.request`.

    Returns:
        requests.Response: The HTTP response object.
    """
    start_time = time.time()
    response = requests.request(method, url, **kwargs)
    duration = time.time() - start_time
    print(f"⏱️ Request to {url} took {duration:.2f} seconds")
    return response

def upload_video(file_path: str) -> Union[Dict, None]:
    """
    Uploads a video file to the FastAPI application.

    Args:
        file_path (str): The path to the video file.

    Returns:
        dict or None: The upload result JSON.
    """
    with open(file_path, 'rb') as file:
        files = {'file': file}
        upload_url = f"{BASE_URL}/upload_video/"
        response = make_request(upload_url, 'post', files=files)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error during video upload: {response.status_code}, {response.text}")
            return None

def process_video(video_uuid: str, n_frames: int = 10, frame_extraction_method: str = "uniform_sampling") -> Union[Dict, None]:
    """
    Processes a video using the FastAPI application.

    Args:
        video_uuid (str): The UUID of the uploaded video.
        n_frames (int): Number of frames to extract (default is 10).
        frame_extraction_method (str): Frame extraction method (default is "uniform_sampling").

    Returns:
        dict or None: The process result JSON.
    """
    params = {
        "video_uuid": video_uuid,
        "n_frames": n_frames,
        "frame_extraction_method": frame_extraction_method
    }

    response = make_request(f"{BASE_URL}/process_video", 'post', params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error during video processing: {response.status_code}, {response.text}")
        return None

def search_music_weighted(keywords_weights: Dict[str, int]) -> Union[Dict, None]:
    """
    Searches for music with weighted keywords using the FastAPI application.

    Args:
        keywords_weights (dict): Dictionary containing keyword weights.

    Returns:
        dict or None: The search result JSON for music.
    """
    search_url = f"{BASE_URL}/search_music_weighted/"

    response = make_request(search_url, 'post', json=keywords_weights)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error during music search: {response.status_code}, {response.text}")
        return None

def search_similar_music(file_path: str, save_track: bool, title: str = "API Track") -> Union[Dict, None]:
    """
    Uploads an audio file to the server and requests a search for similar music.

    Parameters:
    - file_path (str): The local file path to the audio file to be uploaded.
    - save_track (bool): Whether to save the track to the library or not.
    - title (str): The title of the track.

    Returns:
    - dict or None: If the upload and search are successful (HTTP status code 200),
      the function returns a dictionary containing the search results in JSON format.
      If there is an error during the upload or search, the function prints an error
      message and returns None.
    """
    with open(file_path, 'rb') as file:
        files = {'audio_file': file}
        upload_url = f"{BASE_URL}/search_similar_music/?save_track=false&title={title}"
        response = make_request(upload_url, 'post', files=files)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error during music search: {response.status_code}, {response.text}")
            return None

def search_music_text(text_input: str) -> Union[Dict, None]:
    """
    Test function for the search_music_text.

    Args:
        text_input (str): Input text for music search.

    Returns:
        dict or None: If the request is successful (HTTP status code 200),
          the function returns a dictionary containing the music results in JSON format.
          If there is an error during the request, the function prints an error
          message and returns None.
    """
    try:
        url = f"{BASE_URL}/search_music_text/?text_input={text_input}"
        response = make_request(url, 'post')

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error during search_music_text request: {response.status_code}, {response.text}")
            return None

    except Exception as e:
        print(f"❌ Exception during search_music_text request: {str(e)}")
        return None

def search_spotify_music(track_id: str) -> Union[Dict, None]:
    """
    Test function for the search_spotify_music_endpoint.

    Args:
        track_id (str): Spotify track ID for music search.

    Returns:
        dict or None: If the request is successful (HTTP status code 200),
          the function returns a dictionary containing the music results in JSON format.
          If there is an error during the request, the function prints an error
          message and returns None.
    """
    try:
        url = f"{BASE_URL}/search_spotify_music/{track_id}"
        response = make_request(url, 'get')

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error during search_spotify_music request: {response.status_code}, {response.text}")
            return None

    except Exception as e:
        print(f"❌ Exception during search_spotify_music request: {str(e)}")
        return None

def library_search_similar_music(track_id: str) -> Union[Dict, None]:
    """
    Function to search for music similar to the provided track ID.

    Args:
        track_id (str): The ID of the track for which similar music will be searched.

    Returns:
        dict or None: If the request is successful, returns a dictionary containing
          the music results in JSON format. If there is an error during the request,
          the function prints an error message and returns None.
    """
    try:
        url = f"{BASE_URL}/library_search_similar_music/?track_id={track_id}"
        response = make_request(url, 'post')

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error during library_search_similar_music request: {response.status_code}, {response.text}")
            return None

    except Exception as e:
        print(f"❌ Exception during library_search_similar_music request: {str(e)}")
        return None

if __name__ == "__main__":
    # Upload video
    upload_result = upload_video(VIDEO_FILE_PATH)

    if upload_result:
        print(f"✅ Upload Result: {upload_result['uuid']}\n")

        # Process video
        process_result = process_video(upload_result['uuid'])

        if process_result:
            print(f"✅ Process Result: keywords: \n {process_result['keywords']}\n video summerization: {process_result['video_summerization']}")

            # Search music with weighted keywords
            keywords_weights = {"warm": 2, "hopeful": 3}
            music_results = search_music_weighted(keywords_weights)

            if music_results:
                print(f"📃 Cyanite Query: {music_results['cyanite_query']}")
                print(f"✅ Search Result:")
    
                for result in music_results["music_results"]:
                    print(f"ID: {result['id']}, Title: {result['title']}")
                print()

    # Text-based music search
    music_results = search_music_text("relaxing and quiet song for meditation")
    if music_results:
        print(f"📃 Cyanite Query: {music_results['cyanite_query']}")
        print(f"✅ Text-based Music Search Result:")

        for result in music_results["music_results"]:
            print(f"ID: {result['id']}, Title: {result['title']}")
        print()

    # Similar music search
    music_results = search_similar_music(MUSIC_FILE_PATH, False, "WantedSongTitle")
    if music_results:
        print(f"✅ Similar Music Search Result:")

        for result in music_results["music_results"]:
            print(f"ID: {result['id']}, Title: {result['title']}")
        print()

    # Spotify track ID-based music search
    track_id = "7D5r1Va0UQDozLEzCTBY20"
    music_results = search_spotify_music(track_id)
    if music_results:
        print(f"✅ Spotify Track ID-based Music Search Result for Track ID {track_id}:")
        
        for result in music_results["music_results"]:
            print(f"ID: {result['id']}, Title: {result['title']}")
        print()

    # Similar music search by track_id
    track_id = 17961237
    music_results = library_search_similar_music(track_id)
    if music_results:
        print(f"✅ Library Similar Music Search Result for Track ID {track_id}:")
        
        for result in music_results["music_results"]:
            print(f"ID: {result['id']}, Title: {result['title']}")
