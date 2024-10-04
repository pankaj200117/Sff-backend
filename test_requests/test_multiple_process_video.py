import requests
import concurrent.futures
import time

# Define the base URL and video UUIDs
base_url = 'http://127.0.0.1:5011/process_video?video_uuid='
# base_url = 'https://apibeta.sushiandfrenchfries.com/process_video?video_uuid='
# base_url = 'https://api.sushiandfrenchfries.com/process_video?video_uuid='
video_uuids = [
{'uuid': '0d41b41e-1064-4714-b5c3-ef321e211296'},
{'uuid': 'cab0bfb6-8950-4e80-907b-457879240ac2'}
]


# Function to send a single request
def send_request(video_uuid):
    url = base_url + video_uuid["uuid"]
    start = time.time()
    response = requests.post(url)
    print(f"Sent request for {video_uuid}. Status code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response JSON for {video_uuid}: {response.json()}")
    else:
        print(f"Error response for {video_uuid}: {response.text}")
    print(f"Time taken for {video_uuid}: {time.time() - start:.2f} seconds\n")


# Use ThreadPoolExecutor to send requests concurrently
with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(send_request, video_uuids)
