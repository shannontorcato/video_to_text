import requests
import streamlit as st
from configure import auth_key
import youtube_dl
import os

directory = "D:/programming/video_to_text"

files_in_directory = os.listdir(directory)
filtered_files = [file for file in files_in_directory if file.endswith(".mp3")]
for file in filtered_files:
	path_to_file = os.path.join(directory, file)
	os.remove(path_to_file)

if 'status' not in st.session_state:
    st.session_state['status'] = 'submitted'

ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'ffmpeg-location':'./',
    'outtmpl': "./%(id)s.%(ext)s",
}

transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
upload_endpoint = "https://api.assemblyai.com/v2/upload"

headers_auth_only = {'authorization': auth_key}
headers = {
    "authorization": auth_key,
    "content-type": "application/json"
}

CHUNK_SIZE = 5242880

@st.cache
def transcibe_from_link(link, categories):
    _id = link.strip()

    def get_vid(_id):
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(_id)
    
    meta = get_vid(_id)
    save_location = meta['id'] + ".mp3"

    print('Saved mp3 to', save_location)

    def read_file(filename):
        with open(filename, 'rb') as _file:
            while True:
                data = _file.read(CHUNK_SIZE)
                if not data:
                    break
                yield data
    
    upload_response = requests.post(
        upload_endpoint,
        headers=headers_auth_only, data=read_file(save_location)
    )

    audio_url = upload_response.json()['upload_url']
    print('Uploaded to', audio_url)

    transcript_request = {
        'audio_url': audio_url,
        'iab_categories': 'True' if categories else 'False',
    }


    transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers)

    transcript_id = transcript_response.json()['id']
    polling_endpoint = transcript_endpoint + "/" + transcript_id

    print("Transcribing at", polling_endpoint)
    return polling_endpoint

def get_status(polling_endpoint):
    polling_response = requests.get(polling_endpoint, headers=headers)
    st.session_state['status'] = polling_response.json()['status']

def refresh_state():
    st.session_state['status'] = 'submitted'

st.title("Transcribe YouTube Videos")


link = st.text_input("Enter YouTube URL Below", 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', on_change=refresh_state)
st.video(link)

st.text('The transcription is ' + st.session_state['status'])

polling_endpoint = transcibe_from_link(link, False)

st.button('Check Status', on_click=get_status, args=(polling_endpoint,))

transcript = ''
if st.session_state['status']=='completed':
    polling_response = requests.get(polling_endpoint, headers=headers)
    transcript = polling_response.json()['text']

st.markdown(transcript)

word = st.text_input("Enter word to count")
def get_word(word):
    num = 0
    res = transcript.lower()
    res = transcript.split()
    for i in range(len(res)):
        if word in res[i]:
            num+=1
    return num
transcript = polling_response.json()['text']
st.button('Count Word', on_click=get_word, args=(word,),key="first")
num = get_word(word)
st.markdown("There are "+str(num)+" instances of the word \""+word+" \"")