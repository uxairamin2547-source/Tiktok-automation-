import yt_dlp
import os

# ==========================================
# TUMHARI USER LIST
# ==========================================
TARGET_USERNAMES = [
    ".smith58",
    "bullymovie1995",
    "ig.theshy6",
    "lee.movie.10",
    "lee.movie"
]
# ==========================================

def download_user_latest_video(username):
    # TikTok URL pattern
    user_url = f"https://www.tiktok.com/@{username}"
    print(f"🔍 Checking latest video for: {username}")
    
    ydl_opts = {
        # File ka naam: username.mp4
        'outtmpl': f'{username}.mp4', 
        'format': 'best',
        'quiet': False,
        'playlist_items': '1',  # Sirf 1 latest video
        'ignoreerrors': True    # Agar koi user block ho to error na aaye
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([user_url])
        print(f"✅ Download Process complete for {username}")
        
        # Check karte hain file aayi ya nahi
        if os.path.exists(f"{username}.mp4"):
            size = os.path.getsize(f"{username}.mp4")
            print(f"📁 File saved: {username}.mp4 (Size: {size} bytes)")
        else:
            print(f"⚠️ {username} ki video shayad download nahi hui.")
            
    except Exception as e:
        print(f"❌ Error with {username}: {e}")

if __name__ == "__main__":
    print("🚀 Bot shuru ho raha hai...")
    for user in TARGET_USERNAMES:
        download_user_latest_video(user)
    print("🏁 Sabhi users check ho gaye.")
