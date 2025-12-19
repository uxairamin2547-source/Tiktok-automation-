import yt_dlp
import os
from moviepy.editor import VideoFileClip

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

def download_and_process(username):
    # 1. DOWNLOAD PART
    print(f"🎬 Downloading video for: {username}...")
    
    filename = f"{username}.mp4"
    # Purani file ho to hata do
    if os.path.exists(filename):
        os.remove(filename)

    ydl_opts = {
        'outtmpl': filename,
        'format': 'best',
        'quiet': False,
        'playlist_items': '1',
        'ignoreerrors': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.tiktok.com/@{username}"])
    except Exception as e:
        print(f"❌ Error downloading {username}: {e}")
        return

    # Check agar file aayi
    if not os.path.exists(filename):
        print(f"⚠️ Video nahi mili: {username}")
        return

    # 2. EDITING PART (Processing)
    print(f"✂️ Processing (Checking Ratio): {filename}")
    
    try:
        clip = VideoFileClip(filename)
        w, h = clip.size
        target_ratio = 9 / 16
        current_ratio = w / h

        # Agar video perfect vertical nahi hai, to usko crop karo
        if current_ratio > target_ratio:
            # Video zyada chaudi (wide) hai, sides se kaat do
            new_width = h * target_ratio
            x_center = w / 2
            x1 = x_center - (new_width / 2)
            x2 = x_center + (new_width / 2)
            clip = clip.crop(x1=x1, y1=0, x2=x2, y2=h)
        
        # Final file ka naam 'final_' se shuru hoga
        final_filename = f"final_{username}.mp4"
        clip.write_videofile(final_filename, codec="libx264", audio_codec="aac")
        
        print(f"✅ READY TO UPLOAD: {final_filename}")
        
        # Original file delete kar do space bachane ke liye
        clip.close()
        os.remove(filename)
        
    except Exception as e:
        print(f"❌ Error editing {username}: {e}")

if __name__ == "__main__":
    print("🚀 Bot Started: Downloading & Editing...")
    for user in TARGET_USERNAMES:
        download_and_process(user)
    print("🏁 All Tasks Done.")
