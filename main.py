import yt_dlp
import os
import time
from moviepy.editor import VideoFileClip
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================
# TARGET USERS LIST
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
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": ["https://www.googleapis.com/auth/youtube.upload"],
        "expiry": "2030-01-01T00:00:00Z" 
    }
    
    creds = google.oauth2.credentials.Credentials.from_authorized_user_info(creds_data)
    return build("youtube", "v3", credentials=creds)

# === HISTORY SYSTEM ===
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return f.read().splitlines()

def save_history(video_id):
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{video_id}\n")

def upload_to_youtube(filename, title, original_url):
    youtube = get_youtube_service()
    if not youtube: return False

    print(f"🚀 Uploading as PRIVATE: {title}")
    
    body = {
        "snippet": {
            "title": title[:99],
            "description": f"{title}\n\nOriginal: {original_url}\n#shorts #viral #trending",
            "tags": ["shorts", "viral", "tiktok", "funny"],
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
        print(f"✅ UPLOAD SUCCESS! Video ID: {response['id']}")
        return True 
    except Exception as e:
        print(f"❌ Upload Failed: {e}")
        return False

def process_videos(username):
    print(f"🔍 Checking User: {username}...")
    history = load_history()
    
    # === YAHAN CHANGE KIYA HAI (10 -> 50) ===
    # Ab ye pichli 50 videos scan karega best video dhoondne ke liye
    ydl_opts_check = {
        'quiet': True,
        'playlist_items': '1:50', 
        'ignoreerrors': True
    }
    
    user_url = f"https://www.tiktok.com/@{username}"
    target_video_url = None
    target_video_id = None
    video_title = "Amazing Short"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts_check) as ydl:
            info = ydl.extract_info(user_url, download=False)
            if 'entries' not in info: return
            
            # === SMART SELECTION LOOP ===
            for video in info['entries']:
                if not video: continue
                
                v_id = video.get('id')
                duration = video.get('duration', 0)
                
                # Check 1: History
                if v_id in history:
                    # Skip print hata diya taaki logs saaf rahein
                    continue
                
                # Check 2: Duration (3 Min Limit)
                if duration > 180:
                    continue
                
                # AGAR YAHAN PAHUCHE, TO VIDEO MIL GAYI
                print(f"✅ Found Fresh Content: {v_id} ({duration}s)")
                target_video_url = video.get('webpage_url')
                target_video_id = v_id
                video_title = video.get('title', "Trending TikTok")
                break 
            
    except Exception as e:
        print(f"❌ Error checking {username}: {e}")
        return

    if not target_video_url:
        print(f"😴 No new valid videos found for {username} in last 50 uploads.")
        return

    # === DOWNLOAD ===
    filename = f"{username}.mp4"
    if os.path.exists(filename): os.remove(filename)

    ydl_opts_download = {
        'outtmpl': filename,
        'format': 'best',
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
        ydl.download([target_video_url])

    if not os.path.exists(filename): return

    # === EDITING ===
    final_filename = f"final_{username}.mp4"
    try:
        clip = VideoFileClip(filename)
        w, h = clip.size
        
        if w/h > 9/16:
            clip = clip.crop(x1=w/2-(h*9/16)/2, width=h*9/16, height=h)
        
        clip.write_videofile(final_filename, codec="libx264", audio_codec="aac", verbose=False, logger=None)
        clip.close()
        os.remove(filename) 
    except Exception as e:
        print(f"❌ Edit Error: {e}")
        return

    # === UPLOAD & SAVE ===
    success = upload_to_youtube(final_filename, video_title, target_video_url)
    
    if success and target_video_id:
        save_history(target_video_id)
        print(f"📝 Added to History: {target_video_id}")
