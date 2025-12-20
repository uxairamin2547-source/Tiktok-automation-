import yt_dlp
import os
import time
import google.generativeai as genai
from moviepy.editor import VideoFileClip
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==========================================
# 👇 FINAL USERNAME LIST (Updated)
# ==========================================
TARGET_USERNAMES = [
    ".smith58",
    "bullymovie1995",
    "ig.theshy6",
    "lee.movie.10",
    "lee.movie",
    "kyee_films",
    "billygardner",
    "utodio.hz",
    "yfuuet5"
]
# ==========================================

HISTORY_FILE = "download_history.txt"
INDEX_FILE = "user_index.txt"  # Ye file yaad rakhegi kiski baari hai

# 1. SETUP & AUTH
def configure_ai():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return False
    try:
        genai.configure(api_key=api_key)
        return True
    except: return False

def get_youtube_service():
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    refresh_token = os.environ.get("REFRESH_TOKEN")
    
    if not client_id or not client_secret or not refresh_token:
        print("❌ Error: Secrets missing.")
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

# 2. PATTERN MEMORY (Round Robin Logic)
def get_current_user_index():
    if not os.path.exists(INDEX_FILE): return 0
    try:
        with open(INDEX_FILE, "r") as f:
            idx = int(f.read().strip())
            # Agar index list se bada ho gaya, to wapas 0 par aajao
            return idx if idx < len(TARGET_USERNAMES) else 0
    except: return 0

def save_next_user_index(current_idx):
    # Agli baari agle bande ki (List khatam hui to wapas 0)
    next_idx = (current_idx + 1) % len(TARGET_USERNAMES)
    with open(INDEX_FILE, "w") as f:
        f.write(str(next_idx))
    print(f"💾 Pattern Updated: Next turn is User #{next_idx}")

# 3. SMART AI & CORE FUNCTIONS
def generate_viral_metadata(video_path, original_title):
    if not configure_ai(): return original_title, f"{original_title} #shorts"

    print("🧠 AI is watching video...")
    try:
        video_file = genai.upload_file(video_path)
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED": raise Exception("Failed")

        # Smart Model Detect (Jo available ho wahi uthayega)
        active_model = None
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods and ('flash' in m.name or 'pro' in m.name):
                    active_model = genai.GenerativeModel(m.name)
                    break
        except: pass
        if not active_model: active_model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = """
        ACT AS: Viral Shorts Expert.
        TASK: Create shocking title (Under 5 words) + description.
        OUTPUT:
        TITLE: [Title]
        DESC: [Desc]
        """
        response = active_model.generate_content([video_file, prompt])
        text = response.text
        
        ai_title = original_title
        ai_desc = f"{original_title} #shorts"
        
        for line in text.split('\n'):
            if "TITLE:" in line: ai_title = line.replace("TITLE:", "").replace("*", "").strip()
            if "DESC:" in line: ai_desc = line.replace("DESC:", "").replace("*", "").strip()
            
        return ai_title, ai_desc
    except: return original_title, f"{original_title} #shorts"

def load_history():
    if not os.path.exists(HISTORY_FILE): return []
    with open(HISTORY_FILE, "r") as f: return f.read().splitlines()

def save_history(video_id):
    with open(HISTORY_FILE, "a") as f: f.write(f"{video_id}\n")

def process_single_video(username):
    print(f"🔍 Checking turn for: {username}...")
    history = load_history()
    
    # Check last 5 videos
    ydl_opts = {'quiet': True, 'playlist_items': '1:5', 'ignoreerrors': True, 'noplaylist': True}
    target_video = None
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.tiktok.com/@{username}", download=False)
            if 'entries' not in info: return False
            
            for video in info['entries']:
                if not video: continue
                if video.get('id') in history: continue # Skip old videos
                if video.get('duration', 0) > 180: continue # Skip long videos
                
                print(f"✅ Found Fresh Video: {video['id']}")
                target_video = video
                break
    except: return False

    if not target_video: return False

    filename = f"temp_{username}.mp4"
    final_filename = f"final_{username}.mp4"
    
    try:
        # Download Best Quality
        with yt_dlp.YoutubeDL({'outtmpl': filename, 'quiet': True, 'format': 'bestvideo+bestaudio/best'}) as ydl:
            ydl.download([target_video['webpage_url']])
            
        # Ratio Fix (1080x1920 Full Screen)
        clip = VideoFileClip(filename)
        tgt_w, tgt_h = 1080, 1920
        ratio = clip.w / clip.h
        if ratio > tgt_w/tgt_h:
            clip = clip.resize(height=tgt_h)
            clip = clip.crop(x1=(clip.w/2 - tgt_w/2), width=tgt_w, height=tgt_h)
        else:
            clip = clip.resize(width=tgt_w)
            clip = clip.crop(y1=(clip.h/2 - tgt_h/2), width=tgt_w, height=tgt_h)
            
        clip.write_videofile(final_filename, codec="libx264", audio_codec="aac", fps=30, verbose=False, logger=None)
        clip.close()
        os.remove(filename)

        # Upload
        upload_service = get_youtube_service()
        if not upload_service: return False

        title, desc = generate_viral_metadata(final_filename, target_video.get('title', 'Shorts'))
        
        body = {
            "snippet": {"title": title[:99], "description": desc, "tags": ["shorts"], "tiktok", "viral"], "categoryId": "24"},
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}
        }
        media = MediaFileUpload(final_filename, chunksize=-1, resumable=True)
        req = upload_service.videos().insert(part="snippet,status", body=body, media_body=media)
        print(f"✅ UPLOAD SUCCESS! ID: {req.execute()['id']}")
        
        save_history(target_video['id'])
        os.remove(final_filename)
        return True 
            
    except Exception as e:
        print(f"Error: {e}")
        if os.path.exists(filename): os.remove(filename)
        return False

if __name__ == "__main__":
    start_index = get_current_user_index()
    print(f"🏁 Starting Check from User Index: {start_index}")
    
    # Loop wahan se shuru hoga jiski baari hai
    uploaded = False
    for i in range(len(TARGET_USERNAMES)):
        current_check_index = (start_index + i) % len(TARGET_USERNAMES)
        user = TARGET_USERNAMES[current_check_index]
        
        if process_single_video(user):
            print(f"🎉 Success! {user} ki video upload ho gayi.")
            save_next_user_index(current_check_index) # Agli baari agle ki
            uploaded = True
            break # 🛑 SIRF 1 VIDEO UPLOAD KARO AUR RUKO
        else:
            print(f"⚠️ {user} ke paas nayi video nahi mili, Next user check kar raha hoon...")
            
    if not uploaded:
        print("😴 Kisi bhi user ke paas nayi video nahi mili. Sone ja raha hoon.")
