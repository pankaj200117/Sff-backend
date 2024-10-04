import requests
# ========== SEARCH FROM FILE ==========
# url = 'http://127.0.0.1:5011/search_similar_music?save_track=false&title=API Track'
# # url = 'https://apibeta.sushiandfrenchfries.com/search_similar_music?save_track=false&title=API Track'
# files = {'audio_file': open('../data/uploaded_audios/a67fe019-61b4-4823-bde7-e0ae2fba81e4.mp3', 'rb')}
# response = requests.post(url, files=files)
# =====================================


# ========== SEARCH FROM YOUTUBE ==========
yt_url = "https://www.youtube.com/watch?v=5URefVYaJrA"
url = f"http://127.0.0.1:5011/search_similar_music_yt/?yt_url={yt_url}&save_track=false&title=API Track"
response = requests.post(url)
# =========================================


# ========== SEARCH FROM KEYWORDS ==========
# url = "http://127.0.0.1:5011/search_music_weighted"
# params = {'whimsical': 1.0, 'playful': 1.0, 'humorous': 1.0,
#     'light-hearted': 1.0, 'amusing': 1.0, 'ironic': 1.0, 'quirky': 1.0}
# response = requests.post(url, json=params)
# ==========================================

# ========== SEARCH FROM TEXT ==========
# url = "http://127.0.0.1:5011/search_music_text/?text_input=energetic"
# response = requests.post(url)
# ======================================


print(response.json())