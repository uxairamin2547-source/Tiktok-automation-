import yt_dlp
import os
import random
from moviepy.editor import VideoFileClip
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================
# 1. SETTINGS & USERS
# ==========================================
TARGET_USERNAMES = [
    ".smith58",
    "bullymovie1995",
    "ig.theshy6",
    "lee.movie.10",
    "lee.movie"
]

# Description mein yeh tags lagenge
DESCRIPTION_TEXT = """
Enjoy this viral video! 
Like and Subscribe for more daily shorts.

#shorts #viral #funny #tiktok #trending
"""

# ==========================================
# 2. YOUTUBE UPLOAD FUNCTION
# ==========================================
def upload_to_youtube(filename, title):
    print(f"🚀 Uploading to YouTube: {title}")
    
    try:
        # Token se login karna
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/youtube.upload'])
        youtube = build('youtube', 'v3', credentials=creds)

        request_body = {
            'snippet': {
                'title': title,
                'description': DESCRIPTION_TEXT,
                'tags': ['shorts', 'viral', 'funny', 'tiktok'],
                'categoryId': '24' # Entertainment Category
            },
            'status': {
                'privacyStatus': 'public', # 'private' kar sakte ho agar test karna ho
                'selfDeclaredMadeForKids': False
            }
        }

        media = MediaFileUpload(filename, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        )
        
        response = request.execute()
        print(f"✅ UPLOAD SUCCESS! Video ID: {response['id']}")
        return True

    except Exception as e:
        print(f"❌ Upload Error: {e}")
        return False

# ==========================================
# 3. DOWNLOAD & PROCESS ENGINE
# ==========================================
def process_user(username):
    # --- A. DOWNLOAD ---
    raw_filename = f"{username}.mp4"
    final_filename = f"final_{username}.mp4"
    
    # Safayi (Purani files hatao)
    if os.path.exists(raw_filename): os.remove(raw_filename)
    if os.path.exists(final_filename): os.remove(final_filename)

    print(f"\n🔍 Checking User: {username}")
    
    ydl_opts = {
        'outtmpl': raw_filename,
        'format': 'best',
        'quiet': True,
        'playlist_items': '1', # Latest 1 video
        'ignoreerrors': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.tiktok.com/@{username}"])
    except:
        print(f"⚠️ Skip: Could not download {username}")
        return

    if not os.path.exists(raw_filename):
        print(f"⚠️ No video found for {username}")
        return

    # --- B. EDIT (CROP) ---
    print(f"✂️ Processing: {raw_filename}")
    try:
        clip = VideoFileClip(raw_filename)
        w, h = clip.size
        
        # Crop logic (9:16 Ratio)
        if (w / h) > (9 / 16):
            new_width = h * (9 / 16)
            x_center = w / 2
            clip = clip.crop(x1=x_center - new_width/2, x2=x_center + new_width/2, width=new_width, height=h)
        
        clip.write_videofile(final_filename, codec="libx264", audio_codec="aac", logger=None)
        clip.close()
        os.remove(raw_filename) # Raw file delete
    except Exception as e:
        print(f"❌ Edit Error: {e}")
        return

    # --- C. UPLOAD ---
    # Title banate hain (Username + Random Emoji)
    emojis = ["🔥", "😂", "😱", "❤️", "🚀"]
    video_title = f"Amazing Video by {username} {random.choice(emojis)} #shorts"
    
    if os.path.exists(final_filename):
        success = upload_to_youtube(final_filename, video_title)
        
        if success:
            print("🗑️ Cleaning up...")
            os.remove(final_filename)
    
if __name__ == "__main__":
    print("🤖 BOT STARTED...")
    for user in TARGET_USERNAMES:
        process_user(user)
    print("🏁 ALL DONE.")
