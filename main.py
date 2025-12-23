import yt_dlp
import os
import time
import google.generativeai as genai
# 👇 UPDATE: Added modules for Black Background Logic
from moviepy.editor import VideoFileClip, CompositeVideoClip, ColorClip
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
    "yfuuet5",
    "oioi.movie1",
    "loong.movie",
    "milesmovies1",
    "aire.movie",
    "rushbolt42",
    "shadownarrator13",
    "lixchangysong",
    "hoang.ae",
    "1eesten",
    "eiei.edit"
]
# ==========================================

HISTORY_FILE = "download_history.txt"
INDEX_FILE = "user_index.txt"

# 👇 STATIC BLOCKS
COPYRIGHT_DISCLAIMER = """Disclaimer: Any footage in this video has only been used to communicate a message (understandable) to audience. According to my knowledge, it’s a fair use under reviews and commentary section. We don't plan to violate anyone's right. Thanks."""

VIRAL_TAGS_BLOCK = """🔥Tags 
Movie Recap Shorts, Film Recap Shorts, Movie Explained Shorts, Story Recap Shorts, Cinema Shorts, Viral Movie Clips, Movie Reels, Film Reels, Short Film Clips, Movie Recap, Movie Explained, Ending Explained, Best Movie Scenes, Hidden Details, Full Movie Summary, Plot Twist, Film Analysis, Story Recapped, Cinema History, Blockbuster Movie Review, Hollywood Action Movies, Best Sci-Fi Movies, Thriller Movie Explanation, Horror Movie Recap, Mystery Movie Summary, Suspense Films, Underrated Movies, Movie Commentary, Film Theory, Character Analysis, Director's Cut, Behind The Scenes, Movie Mistakes, Film Easter Eggs, Best Netflix Movies, New Movie Recommendation, Must Watch Movies 2025.

#MovieRecap #MovieExplained #EndingExplained #moviereview #movie #movieclips #film #movieexplained  #moviescenes"""

# 👇 HIDDEN TAGS
VIDEO_TAGS = [
    "Movie Recaps", "Movie Explained", "Film Recap", "Story Recapped", "FixClipss", "Fresh2Movies", "MovieFocus", "MartianMeloDrama", "ZaynMovies", 
    "movies", "film", "cinema", "viral", "shorts", "blockbuster", "hollywood", 
    "action", "thriller", "horror", "sci-fi", "mystery", "suspense", "drama", 
    "adventure", "fantasy", "animation", "review", "analysis", "top 10", 
    "best movies", "film commentary", "movie summary", "cinema hall", "ending explained", "movie recap shorts"
]

# 1. SETUP
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

# 2. PATTERN
def get_current_user_index():
    if not os.path.exists(INDEX_FILE): return 0
    try:
        with open(INDEX_FILE, "r") as f:
            idx = int(f.read().strip())
            return idx if idx < len(TARGET_USERNAMES) else 0
    except: return 0

def save_next_user_index(current_idx):
    next_idx = (current_idx + 1) % len(TARGET_USERNAMES)
    with open(INDEX_FILE, "w") as f:
        f.write(str(next_idx))
    print(f"💾 Next turn saved for User #{next_idx}")

# 3. AI & PROCESS
def generate_viral_metadata(video_path, original_title):
    fallback_title = f"{original_title} #shorts #viral"
    fallback_desc = f"{original_title}\n\n{COPYRIGHT_DISCLAIMER}\n\n{VIRAL_TAGS_BLOCK}"

    if not configure_ai(): return fallback_title, fallback_desc

    print("🧠 AI is watching video...")
    try:
        video_file = genai.upload_file(video_path)
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED": raise Exception("Failed")

        active_model = None
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods and ('flash' in m.name or 'pro' in m.name):
                    active_model = genai.GenerativeModel(m.name)
                    break
        except: pass
        if not active_model: active_model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = """
        ACT AS: YouTube Shorts growth expert specializing in movie recap and cinematic clip content.

WATCH the given short video carefully and fully understand the story moment, emotional hook, and curiosity gap.

TASK:
Generate ONLY ONE viral title, ONE related emoji, ONE optimized description, and ONE relevant hashtag.

RULES FOR TITLE:
- Write ONE title only
- Under 60 characters
- Natural, human-written
- Curiosity-driven but NOT exaggerated
- No spoilers
- No emojis inside the title text
- No ALL CAPS
- Avoid words like “shocking”, “unbelievable”

RULES FOR EMOJI:
- Provide EXACTLY ONE emoji
- Emoji must match the title’s emotion or theme
- Do NOT include text with the emoji

RULES FOR DESCRIPTION:
- Write ONE short description (3–4 lines max)
- First line must hook the viewer
- Briefly explain the situation without revealing the ending
- Naturally include SEO keywords:
  movie recap, film recap, movie explained, story recap
- No keyword stuffing
- No hashtags inside description
- Do NOT repeat the title
- End with soft curiosity (example: “Watch till the end.”)

RULES FOR HASHTAG:
- Provide EXACTLY ONE hashtag
- Hashtag must be relevant to the video topic
- Do NOT include multiple hashtags

OUTPUT FORMAT (STRICT – FOLLOW EXACTLY):

TITLE: <one title>
EMOJI: <one emoji>
SUMMARY: <one description>
HASHTAG: <one hashtag>
        """
        response = active_model.generate_content([video_file, prompt])
        text = response.text
        
        ai_title_raw = original_title
        ai_summary = original_title
        
        for line in text.split('\n'):
            if "TITLE:" in line: ai_title_raw = line.replace("TITLE:", "").replace("*", "").replace('"', '').strip()
            if "SUMMARY:" in line: ai_summary = line.replace("SUMMARY:", "").replace("*", "").strip()
            
        final_title = f"{ai_title_raw} #shorts #viral"
        final_desc = f"{ai_summary}\n\n{COPYRIGHT_DISCLAIMER}\n\n{VIRAL_TAGS_BLOCK}"
            
        return final_title, final_desc
    except: return fallback_title, fallback_desc

def load_history():
    if not os.path.exists(HISTORY_FILE): return []
    with open(HISTORY_FILE, "r") as f: return f.read().splitlines()

def save_history(video_id):
    with open(HISTORY_FILE, "a") as f: f.write(f"{video_id}\n")

def process_single_video(username):
    print(f"🔍 Checking turn for: {username}...")
    history = load_history()
    
    ydl_opts = {'quiet': True, 'playlist_items': '1:30', 'ignoreerrors': True, 'noplaylist': True}
    target_video = None
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.tiktok.com/@{username}", download=False)
            if 'entries' not in info: return False
            
            for video in info['entries']:
                if not video: continue
                if video.get('id') in history: continue
                if video.get('duration', 0) > 180: continue
                
                print(f"✅ Found Fresh Video: {video['id']}")
                target_video = video
                break
    except: return False

    if not target_video: return False

    filename = f"temp_{username}.mp4"
    final_filename = f"final_{username}.mp4"
    
    try:
        with yt_dlp.YoutubeDL({'outtmpl': filename, 'quiet': True, 'format': 'bestvideo+bestaudio/best'}) as ydl:
            ydl.download([target_video['webpage_url']])
            
        print("🎬 Editing Video (Fix Clips Style - No Crop)...")
        # 👇 NEW LOGIC: Use CompositeVideoClip to put video on Black Background
        clip = VideoFileClip(filename)
        if clip.audio:
            clip = clip.set_audio(clip.audio.volumex(1.0))
        
        # Target Dimensions
        target_width, target_height = 1080, 1920

        # Create Black Background
        background = ColorClip(size=(target_width, target_height), color=(0,0,0), duration=clip.duration)

        # Resize video to fit INSIDE 1080x1920 (Maintain Aspect Ratio)
        video_ratio = clip.w / clip.h
        target_ratio = target_width / target_height

        if video_ratio > target_ratio:
            # Video is wider than target slot -> Fit to Width (Black bars top/bottom)
            video_clip = clip.resize(width=target_width)
        else:
            # Video is taller/narrower -> Fit to Height (Black bars sides)
            video_clip = clip.resize(height=target_height)

        # Place resized video in CENTER of black background
        final_clip = CompositeVideoClip([background, video_clip.set_position("center")])
        final_clip = final_clip.set_audio(clip.audio) # Ensure audio is preserved
            
        final_clip.write_videofile(final_filename, codec="libx264", audio_codec="aac", fps=30, verbose=False, logger=None)
        
        final_clip.close()
        clip.close()
        os.remove(filename)

        upload_service = get_youtube_service()
        if not upload_service: return False

        title, desc = generate_viral_metadata(final_filename, target_video.get('title', 'Shorts'))
        
        print(f"🚀 Uploading PUBLIC: {title}")
        
        body = {
            "snippet": {
                "title": title[:99], 
                "description": desc, 
                "tags": VIDEO_TAGS,
                "categoryId": "24",
                "defaultLanguage": "en",       
                "defaultAudioLanguage": "en"   
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
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
    
    uploaded = False
    for i in range(len(TARGET_USERNAMES)):
        current_check_index = (start_index + i) % len(TARGET_USERNAMES)
        user = TARGET_USERNAMES[current_check_index]
        
        if process_single_video(user):
            print(f"🎉 Success! {user} ki video PUBLIC ho gayi.")
            save_next_user_index(current_check_index)
            uploaded = True
            break
        else:
            print(f"⚠️ {user} ke paas nayi video nahi mili, Next user...")
            
    if not uploaded:
        print("😴 Kisi bhi user ke paas nayi video nahi mili.")
