from pytubefix import YouTube

link = input("Enter the link of any YouTube video: ")
yt = YouTube(link, use_oauth=True)
print("Vido Title:", yt.title)
print("Setup finished successfully!")