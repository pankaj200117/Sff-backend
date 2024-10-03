import requests
import time
import concurrent.futures

url = 'http://127.0.0.1:5011/generate_audio'
# url = 'https://apibeta.sushiandfrenchfries.com/generate_audio'
# url = "https://api.sushiandfrenchfries.com//generate_audio"

keywords = {'guitar': 1.0, 'nostalgic': 1.0, 'hopeful': 8.0, 'whimsical': 7.0, 'transformational': 1.0,
            'uplifting': 1., 'playful': 1.0, 'warm': 1.0, 'humorous': 1.0, 'inviting': 1.0, 'cheerful': 1.0,
            'light-hearted': 1.0, 'celebratory': 1.0, 'curious': 1.0, 
            "Mythical creature's journey from icy isolation to urban celebration": 1.0}

response = requests.post(url, json=keywords)
print(response.json())