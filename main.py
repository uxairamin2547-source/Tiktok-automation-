import yt_dlp
import os
import time
import google.generativeai as genai
from moviepy.editor import VideoFileClip
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================
# 👇 USERNAME LIST
# ==========================================
TARGET_USERNAMES = [
    ".smith58",
    "bullymovie1995",
    "ig.theshy6",
    "lee.movie.10",
    "lee.movie"
]
# ==========================================

HISTORY_FILE = "download_history.txt"

# 1. SETUP & AUTH
def configure_ai():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ Gemini API Key nahi mili! Skipping AI.")
        return False
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"⚠️ AI Config Error: {e}")
        return False

def get_youtube_service():
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    refresh_token = os.environ.get("REFRESH_TOKEN")
    
    if not client_id or not client_secret or not refresh_token:
        print("❌ Error: GitHub Secrets missing.")
        return None

    creds_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/youtube.upload"],
        "expiry": "2030-01-01T00:00:00Z" 
    }
    
    creds = google.oauth2.credentials.Credentials.from_authorized_user_info(creds_data)
    return build("youtube", "v3", credentials=creds)

# 2. AI TITLE GENERATOR (SMART AUTO-DETECT)
def generate_viral_metadata(video_path, original_title):
    if not configure_ai():
        return original_title, f"Original: {original_title} #shorts"

    print("🧠 AI is watching video for Title...")
    
    try:
        # Upload video
        print("📤 Uploading to Gemini...")
        video_file = genai.upload_file(video_path)
        
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise Exception("Video processing failed")

        # 👇 SMART LOGIC: Find FIRST available model
        active_model = None
        print("🔍 Searching for available models...")
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    # Prefer Flash or Pro
                    if 'flash' in m.name or 'pro' in m.name:
                        active_model = genai.GenerativeModel(m.name)
                        print(f"✅ Found & Using: {m.name}")
                        break
        except Exception as e:
            print(f"⚠️ List Models failed: {e}")

        # Fallback if list fails
        if not active_model:
            print("⚠️ No model found in list, trying generic 'gemini-1.5-flash'...")
            active_model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = """
        ACT AS: A Viral YouTube Shorts Expert.
        TASK: Create a very short, shocking title and description.
        
        RULES FOR TITLE:
        1. UNDER 5 WORDS.
        2. Must be suspenseful or emotional.
        3. End with #shorts
        
        RULES FOR DESCRIPTION:
        1. 1-line summary.
        2. Add this Disclaimer:
        "Disclaimer: Any footage in this video has only been used to communicate a message (understandable) to audience. According to my knowledge, it’s a fair use under reviews and commentary section. We don't plan to violate anyone's right. Thanks."
        3. Add 10 viral tags.
        
        OUTPUT FORMAT:
        TITLE: [Your Title]
        DESC: [Your Description]
        """
        
        response = active_model.generate_content([video_file, prompt])
        text = response.text
        
        ai_title = original_title
        ai_desc = f"{original_title} #shorts"
        
        for line in text.split('\n'):
            if "TITLE:" in line:
                clean_title = line.replace("TITLE:", "").replace("*", "").replace('"', '').strip()
                if clean_title: ai_title = clean_title
            if "DESC:" in line:
                ai_desc = line.replace("DESC:", "").replace("*", "").strip()
        
        if "DESC:" in text and "TITLE:" not in ai_title:
             parts = text.split("DESC:")
             if len(parts) > 1: ai_desc = parts[1].strip()

        print(f"✨ AI Title: {ai_title}")
        return ai_title, ai_desc

    except Exception as e:
        print(f"⚠️ AI Error (Using Original): {e}")
        return original_title, f"{original_title} #shorts"

# 3. CORE FUNCTIONS
def load_history():
    if not os.path.exists(HISTORY_FILE): return []
    with open(HISTORY_FILE, "r") as f: return f.read().splitlines()

def save_history(video_id):
    with open(HISTORY_FILE, "a") as f: f.write(f"{video_id}\n")

def upload_to_youtube(filename, title, description):
    youtube = get_youtube_service()
    if not youtube: return False

    print(f"🚀 Uploading PRIVATE: {title}")
    
    body = {
        "snippet": {
            "title": title[:99], 
            "description": description,
            "tags": ["shorts", "viral", "movie"],
            "categoryId": "24"
        },
        "status": {
            "privacyStatus": "private", 
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(filename, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    
    try:
        response = request.execute()
        print(f"✅ UPLOAD SUCCESS! ID: {response['id']}")
        return True 
    except Exception as e:
        print(f"❌ Upload Failed: {e}")
        return False

def process_videos(username):
    print(f"🔍 Checking: {username}...")
    history = load_history()
    
    ydl_opts = {
        'quiet': True,
        'playlist_items': '1:10',
        'ignoreerrors': True,
        'noplaylist': True
    }
    
    target_video = None
    original_title = "Shorts"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.tiktok.com/@{username}", download=False)
            if 'entries' not in info: return
            
            for video in info['entries']:
                if not video: continue
                v_id = video.get('id')
                if v_id in history or video.get('duration', 0) > 180: continue
                
                print(f"✅ Found Fresh: {v_id}")
                target_video = video
                original_title = video.get('title', "Shorts")
                break
    except: return

    if not target_video: return

    filename = f"{username}.mp4"
    final_filename = f"final_{username}.mp4"
    
    ydl_download_opts = {
        'outtmpl': filename,
        'quiet': True,
        'format': 'bestvideo+bestaudio/best'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_download_opts) as ydl:
            ydl.download([target_video['webpage_url']])
            
        print("✂️ Fixing Ratio to 1080x1920 Full Screen...")
        clip = VideoFileClip(filename)
        
        target_w, target_h = 1080, 1920
        current_ratio = clip.w / clip.h
        target_ratio = target_w / target_h

        if current_ratio > target_ratio:
            clip = clip.resize(height=target_h)
            clip = clip.crop(x1=(clip.w/2 - target_w/2), width=target_w, height=target_h)
        else:
            clip = clip.resize(width=target_w)
            clip = clip.crop(y1=(clip.h/2 - target_h/2), width=target_w, height=target_h)
            
        clip.write_videofile(final_filename, codec="libx264", audio_codec="aac", fps=30, verbose=False, logger=None)
        clip.close()
        
        if os.path.exists(filename): os.remove(filename)
        
    except Exception as e:
        print(f"❌ Editing Error: {e}")
        if os.path.exists(filename): os.remove(filename)
        return

    title, desc = generate_viral_metadata(final_filename, original_title)
    if upload_to_youtube(final_filename, title, desc):
        save_history(target_video['id'])

if __name__ == "__main__":
    for user in TARGET_USERNAMES: process_videos(user)
