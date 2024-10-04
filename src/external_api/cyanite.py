import os
import httpx
import aiofiles
import logging

CYANITE_ACCESS_TOKEN = os.getenv("CYANITE_ACCESS_TOKEN")
logger = logging.getLogger(__name__)
steps_logger = logging.getLogger("steps_info")


async def songsearch(search_text) -> list:
    """
    Search for songs based on the given text.

    Args:
        search_text (str): Text to search for.

    Returns:
        list: List of songs matching the search text.
    """
    url = 'https://api.cyanite.ai/graphql'
    headers = {"Authorization": CYANITE_ACCESS_TOKEN}
    query = """query FreeTextSearchExample {
    freeTextSearch(
      first: 10
      target: { library: {} }
      searchText: "%s"
    ) {
      ... on FreeTextSearchError {
        message
        code
      }
      ... on FreeTextSearchConnection {
        edges {
          cursor
          node {
            id
            title        
          }
        }
      }
    }
    }""" % search_text

    data = {
        "query": query
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers)
            if response.status_code != 200:
                return []

            try:
                data = response.json()
            except Exception as e:
                logger.error(f"Error parsing response: {str(e)}")
                return []

            res = []
            if data is not None:
                d = data['data']['freeTextSearch']['edges']
                for dd in d:
                    res.append(dd['node'])
            return res
    except Exception as e:
        logger.error(f"Error searching for songs: {str(e)}")
        return []


async def search_similar_music(client: httpx.AsyncClient, track_id: str, include_original: bool = True) -> list:
    """
    Search for similar music tracks.

    Args:
        client (httpx.AsyncClient): The HTTP client to use for the request.
        track_id (str): ID of the track to find similar tracks for.
        include_original (bool): Whether to include the original track in the results.

    Returns:
        list: List of similar tracks.
    """
    url = 'https://api.cyanite.ai/graphql'
    headers = {"Authorization": CYANITE_ACCESS_TOKEN}
    query = """query SimilarTracksQuery($trackId: ID!) {
        libraryTrack(id: $trackId) {
            __typename
            ... on Error {
                message
            }
            ... on Track {
                id
                title
                similarTracks(target: { library: {} }) {
                    __typename
                    ... on SimilarTracksError {
                        code
                        message
                    }
                    ... on SimilarTracksConnection {
                        edges {
                            node {
                                id
                                title
                            }
                        }
                    }
                }
            }
        }
    }"""

    variables = {
        "trackId": track_id
    }

    data = {
        "query": query,
        "variables": variables
    }
    try:
        response = await client.post(url, json=data, headers=headers)
        if response.status_code != 200:
            return []

        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return []

        similar_tracks = []
        if data and 'data' in data and 'libraryTrack' in data['data']:
            orignal_track_title = data['data']['libraryTrack']['title']
            if include_original:
                similar_tracks.append({"id": track_id, "title": orignal_track_title})
            
            similar_tracks_data = data['data']['libraryTrack']['similarTracks']['edges']
            for track_data in similar_tracks_data:
                similar_tracks.append(track_data['node'])
            return similar_tracks

        return []
    except Exception as e:
        steps_logger.error(f"Error searching for similar music: {str(e)}")
        return []


async def get_file_upload_request(client: httpx.AsyncClient) -> dict | None:
    """
    Get the file upload request.

    Args:
        client (httpx.AsyncClient): The HTTP client to use for the request.

    Returns:
        dict: File upload request details.
    """
    url = 'https://api.cyanite.ai/graphql'
    headers = {"Authorization": CYANITE_ACCESS_TOKEN}
    query = """mutation FileUploadRequestMutation {
        fileUploadRequest {
            id
            uploadUrl
        }
    }"""

    data = {
        "query": query
    }
    try:
        response = await client.post(url, json=data, headers=headers)
        if response.status_code != 200:
            return None

        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return None

        if data and 'data' in data and 'fileUploadRequest' in data['data']:
            return data['data']['fileUploadRequest']

        return None
    except Exception as e:
        logger.error(f"Error getting file upload request: {str(e)}")
        return None

async def upload_file(client: httpx.AsyncClient, upload_url: str, file_path: str) -> bool:
    """
    Upload a file.

    Args:
        client (httpx.AsyncClient): The HTTP client to use for the request.
        upload_url (str): URL to upload the file to.
        file_path (str): Path to the file to upload.

    Returns:
        bool: True if the upload was successful, False otherwise.
    """
    try:
        async with aiofiles.open(file_path, 'rb') as file:
            file_data = await file.read()

        response = await client.put(upload_url, content=file_data, headers={"Content-Type": "audio/mpeg"})
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return False

async def create_library_track(client: httpx.AsyncClient, upload_id: str, title: str) -> str | None:
    """
    Create a library track.

    Args:
        client (httpx.AsyncClient): The HTTP client to use for the request.
        upload_id (str): ID of the uploaded file.
        title (str): Title of the track.

    Returns:
        str: ID of the created library track.
    """
    url = 'https://api.cyanite.ai/graphql'
    headers = {"Authorization": CYANITE_ACCESS_TOKEN}
    query = """mutation LibraryTrackCreateMutation($input: LibraryTrackCreateInput!) {
        libraryTrackCreate(input: $input) {
            __typename
            ... on LibraryTrackCreateSuccess {
                createdLibraryTrack {
                    id
                }
            }
            ... on LibraryTrackCreateError {
                code
                message
            }
        }
    }"""

    variables = {
        "input": {
            "uploadId": upload_id,
            "title": title
        }
    }

    data = {
        "query": query,
        "variables": variables
    }

    try:
        response = await client.post(url, json=data, headers=headers)
        if response.status_code != 200:
            return None

        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return None

        if data and 'data' in data and 'libraryTrackCreate' in data['data']:
            result_data = data['data']['libraryTrackCreate']
            if 'createdLibraryTrack' in result_data:
                created_track_id = result_data['createdLibraryTrack']['id']
                return created_track_id
            elif 'code' in result_data and 'message' in result_data:
                logger.error(f"Library Track creation failed: {result_data['code']}, {result_data['message']}")

        return None
    except Exception as e:
        logger.error(f"Error creating library track: {str(e)}")
        return None

async def enqueue_library_track_analysis(client: httpx.AsyncClient, library_track_id: str) -> None:
    """
    Enqueue library track analysis.

    Args:
        client (httpx.AsyncClient): The HTTP client to use for the request.
        library_track_id (str): ID of the library track.
    """
    url = 'https://api.cyanite.ai/graphql'
    headers = {"Authorization": CYANITE_ACCESS_TOKEN}
    query = """mutation LibraryTrackEnqueueMutation($input: LibraryTrackEnqueueInput!) {
        libraryTrackEnqueue(input: $input) {
            __typename
            ... on LibraryTrackEnqueueSuccess {
                enqueuedLibraryTrack {
                    id
                    audioAnalysisV6 {
                        __typename
                    }
                }
            }
            ... on LibraryTrackEnqueueError {
                code
                message
            }
        }
    }"""

    variables = {
        "input": {
            "libraryTrackId": library_track_id
        }
    }

    data = {
        "query": query,
        "variables": variables
    }

    try:
        response = await client.post(url, json=data, headers=headers)
        if response.status_code != 200:
            return None

        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return None

        if data and 'data' in data and 'libraryTrackEnqueue' in data['data']:
            result_data = data['data']['libraryTrackEnqueue']
            if 'enqueuedLibraryTrack' in result_data:
                enqueued_track_data = result_data['enqueuedLibraryTrack']
                analysis_type = enqueued_track_data.get('audioAnalysisV6', {}).get('__typename', None)
                if analysis_type:
                    logger.info(
                        f"Analysis enqueued successfully for Library Track ID {library_track_id} with analysis type: {analysis_type}")
                else:
                    logger.info(f"Analysis enqueued successfully for Library Track ID {library_track_id}")
            elif 'code' in result_data and 'message' in result_data:
                logger.error(f"Analysis enqueue failed: {result_data['code']}, {result_data['message']}")

        return None
    except Exception as e:
        logger.error(f"Error enqueuing library track analysis: {str(e)}")
        return None

async def search_spotify_music(client: httpx.AsyncClient, spotify_track_id: str) -> list:
    """
    Search for Spotify music.

    Args:
        client (httpx.AsyncClient): The HTTP client to use for the request.
        spotify_track_id (str): ID of the Spotify track.

    Returns:
        list: List of similar tracks.
    """
    url = 'https://api.cyanite.ai/graphql'
    headers = {"Authorization": CYANITE_ACCESS_TOKEN}
    query = """query SimilarTracksQuery($trackId: ID!) {
        spotifyTrack(id: $trackId) {
            __typename
            ... on Error {
                message
            }
            ... on Track {
                id
                similarTracks(target: { library: {} }) {
                    __typename
                    ... on SimilarTracksError {
                        code
                        message
                    }
                    ... on SimilarTracksConnection {
                        edges {
                            node {
                                id
                                title
                            }
                        }
                    }
                }
            }
        }
    }"""

    variables = {
        "trackId": spotify_track_id
    }

    data = {
        "query": query,
        "variables": variables
    }

    try:
        response = await client.post(url, json=data, headers=headers)
        if response.status_code != 200:
            return []

        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return []

        similar_tracks = []
        if data and 'data' in data and 'spotifyTrack' in data['data']:
            similar_tracks_data = data['data']['spotifyTrack']['similarTracks']['edges']
            for track_data in similar_tracks_data:
                similar_tracks.append(track_data['node'])
            return similar_tracks

        return []
    except Exception as e:
        logger.error(f"Error searching Spotify music: {str(e)}")
        return []

async def delete_library_tracks(client: httpx.AsyncClient, library_track_ids: list) -> bool:
    """
    Delete library tracks.

    Args:
        client (httpx.AsyncClient): The HTTP client to use for the request.
        library_track_ids (list): List of library track IDs to delete.

    Returns:
        bool: True if deletion was successful, False otherwise.
    """
    # print("Deleting library tracks", library_track_ids)
    url = 'https://api.cyanite.ai/graphql'
    headers = {"Authorization": CYANITE_ACCESS_TOKEN}
    query = """mutation LibraryTracksDeleteMutation($input: LibraryTracksDeleteInput!) {
        libraryTracksDelete(input: $input) {
            __typename
            ... on LibraryTracksDeleteSuccess {
                __typename
            }
            ... on LibraryTracksDeleteError {
                code
                message
            }
        }
    }"""

    variables = {
        "input": {
            "libraryTrackIds": library_track_ids
        }
    }

    data = {
        "query": query,
        "variables": variables
    }

    try:
        response = await client.post(url, json=data, headers=headers)
        if response.status_code != 200:
            return False

        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return False

        if data and 'data' in data and 'libraryTracksDelete' in data['data']:
            result_data = data['data']['libraryTracksDelete']
            if 'code' in result_data and 'message' in result_data:
                logger.error(f"Library Tracks deletion failed: {result_data['code']}, {result_data['message']}")
                return False
            else:
                logger.info(f"Library Tracks [{library_track_ids}] deleted successfully.")
                return True

        return False
    except Exception as e:
        logger.exception(f"Error deleting library tracks: {str(e)}")
        return False


async def get_track_title(track_id: str) -> str|None:
    """
    Get the title of a track from Cyanite given a track ID.

    Args:
        track_id (str): Cyanite track ID.
    
    Returns:
        str|None: Title of the track. None if track not found or request failed.
    """
    url = 'https://api.cyanite.ai/graphql'
    headers = {"Authorization": CYANITE_ACCESS_TOKEN}
    query = """query LibraryTrackQuery($id: ID!) {
        libraryTrack(id: $id) {
            __typename
            ... on LibraryTrack {
                id
                title
            }
            ... on LibraryTrackNotFoundError {
                message
            }
        }
    }"""
    variables = {"id": track_id}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={'query': query, 'variables': variables}, headers=headers)
        response_data = response.json()
        track_data = response_data.get('data', {}).get('libraryTrack', {})

        if track_data.get('__typename') == 'LibraryTrack':
            return track_data.get('title')
        elif track_data.get('__typename') == 'LibraryTrackNotFoundError':
            logger.error(f"Track not found: {track_data.get('message')}")
        else:
            logger.error("Unexpected response format.")
    return None