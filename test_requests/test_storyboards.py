import requests
import time
import concurrent.futures

# url = 'http://127.0.0.1:5011/analyze_storyboard'
url = 'https://apibeta.sushiandfrenchfries.com/analyze_storyboard'
# url = "https://api.sushiandfrenchfries.com//analyze_storyboard"
pdf_files = [
    'data/storyboards/2Phones_StoryBoards_Lyrics.pdf',
    'data/storyboards/784_safeway_boards.pdf'
]


# Function to send a single request
def send_request(file_path):
    start = time.time()
    files = {'file': open(file_path, 'rb')}
    response = requests.post(url, files=files)
    if response.status_code == 200:
        print(f"Response JSON for {file_path}: {response.json()}")
    else:
        print(f"Error response for {file_path}: {response.text}")
    print(f"Time taken for {file_path}: {time.time() - start:.2f} seconds\n")


# Use ThreadPoolExecutor to send requests concurrently
with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(send_request, pdf_files)