import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import re
import requests
import os
from dotenv import load_dotenv


load_dotenv()

API_TOKEN = os.getenv("HUGGINGFACE_API_KEY")                                              ## LOADS API KEY FROM .env FILE.                
API_URL = "https://api-inference.huggingface.co/models/sshleifer/distilbart-cnn-12-6"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}               ##Adds your API key into the Authorization header for authenticated access.
print("API loaded:", API_TOKEN[:10])                 ## CHECKING WHEATHER API KEY IS LOADED OR NOT.

def video_id(url):
    if "v=" in url:                                                 ### THIS FUNCTION TAKES VIDEO ID FROM SHORT YOUTUBE URL.
        return url.split("v=")[1].split("&")[0]                     ### i.e in youtube link like https://www.youtube.com/watch?v=abc123 → "abc123"      
    elif "youtu.be/" in url:                                        ##  IT TAKES URL AFTER "v="
        return url.split("youtu.be/")[1].split("?")[0]              
    else:
        return None

def get_text(vid_url):    
    vid_id = video_id(vid_url)
    if not vid_id:
        return "INVALID URL"
    try:
        transcript = YouTubeTranscriptApi.get_transcript(vid_id)            ##Uses YouTubeTranscriptApi to fetch subtitles for the video.
        full_text  = " ".join([entry['text']for entry in transcript])       ## joins small subtitles into single string.
        return full_text
    except Exception as e:
        return f"Error: {e}"
   

def clean_transcript(text):                             ###cleans the fetched text.
    if not text or "Error" in text:                     
        return text 
    
    cleaned = re.sub(r"\[.*?\]","",text)             ##Removes tags like [music] , which are inside "[]" etc...

    cleaned = re.sub(r"\s+", " ", cleaned)            ##Multiple spaces and Line breaks are replaced with single spaces.
 
    cleaned = re.sub(r"[^\w\s.,!?\'\"]+","",cleaned)   ##Removes Special characters,symbols except Punctuation.

    return cleaned



def LLM_api(text):
    if not API_TOKEN:
        return "API key not found in env.file"
    try:
        if len(text) > 800:
            text = text[:800]                                       #### Limits input text to 800 characters for safety.

        response = requests.post(API_URL, headers=HEADERS, json={"inputs": text}, timeout=20)    ## Makes a POST request to the Hugging Face model API.

        # Check for non-200 status code
        if response.status_code != 200:
            return f"API returned error code {response.status_code}: {response.text}"

        result = response.json()

        if isinstance(result, list) and "summary_text" in result[0]:
            return result[0]["summary_text"]                          ## Checks if the response is a list, and the first item has summary_text       
                                                                      ## If yes, it returns the summary.

        elif "error" in result:
            return f"Hugging Face API error: {result['error']}"
        else:
            return " error in response."
        
    except Exception as e:
        return f"Exception: {e}"

                                                                ### Arranging background to app using CSS.
page_bg_img = '''                      
<style>
[data-testid="stAppViewContainer"] {
    background-image: url("https://images.unsplash.com/photo-1521747116042-5a810fda9664");
    background-size: cover;
    background-repeat: no-repeat;               
    background-attachment: fixed;
}
</style>
'''
st.set_page_config(page_title="YouTube Summarizer", layout="wide")      ##Sets the app title and page layout to full width.

st.markdown(page_bg_img, unsafe_allow_html=True)


st.title("Youtube-video-Summarizer") 


vid_url=st.text_input("Enter Youtube video URL")   


if vid_url:
    col1, col2 = st.columns([1, 1])    ###adjust width ratio . half space for youtube video and another half is for text.

    with col1:
        st.video(vid_url)                   ## YOUTUBE VIDEO 

    with col2:
        with st.spinner("Getting Transcript..."):
            transcript = get_text(vid_url)
        st.success("completed")
        st.text_area("TEXT:",transcript,height = 300)           ### DISPLAYS TEXT FETCHED FROM SUBTITLES.

if vid_url:
    with st.spinner("Getting Transcript..."):
        transcript = get_text(vid_url)
        clean_text = clean_transcript(transcript)           
    if st.button("Summarize"):                                      ## summarize button.
        with st.spinner("Calling LLM API..."):
            summary = LLM_api(clean_text)
        st.success("Summary ready!")                        ### displays summary.
        st.text_area("Summary", summary, height=400)
        st.download_button("Download txt", summary, file_name="summary.txt")                    ### download buttons txt and pdf.
        






















