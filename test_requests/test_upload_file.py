import requests

url = 'http://127.0.0.1:5011/upload_video'
# url = 'https://apibeta.sushiandfrenchfries.com/upload_video'
# url = "https://api.sushiandfrenchfries.com//upload_video"
for i in range(2):
    # files = {'file': open(f'data/not_uploaded_videos/{2 + i%2}.mp4', 'rb')}
    files = {'file': open(f'data/not_uploaded_videos/with_speech.mp4', 'rb')}
    response = requests.post(url, files=files)
    print(response.json())