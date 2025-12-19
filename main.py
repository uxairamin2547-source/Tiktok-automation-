import yt_dlp
import os

def download_tiktok_video(video_url):
    print(f"Attempting to download: {video_url}")
    
    # Settings: MP4 format mein download karega
    ydl_opts = {
        'outtmpl': 'downloaded_video.mp4',
        'format': 'best',
        'quiet': False
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        print("✅ Success! Video download ho gayi.")
        
        # Check karte hain file sach mein aayi ya nahi
        if os.path.exists('downloaded_video.mp4'):
            size = os.path.getsize('downloaded_video.mp4')
            print(f"File Size: {size} bytes")
        else:
            print("❌ Error: Download complete bola par file nahi mili.")
            
    except Exception as e:
        print(f"❌ Error aagaya: {e}")

if __name__ == "__main__":
    # Test ke liye ek viral video link
    test_url = "https://www.tiktok.com/@khaby.lame/video/7238806263529606427" 
    download_tiktok_video(test_url)
