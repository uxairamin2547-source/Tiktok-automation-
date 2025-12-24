import os
import google.oauth2.credentials
from googleapiclient.discovery import build
from collections import Counter

# 👇 TARGET CHANNELS (Sirf Handle likho)
TARGET_HANDLES = [
    "FixClipss",
    "Insane_Cinema",
    "Fresh2Movies",
    "MartianMeloDrama",
    "smith58",
    "bullymovie1995"
]

# 👇 Category ID Map
CATEGORY_MAP = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "20": "Gaming",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology"
}

def get_authenticated_service():
    # Aapke Existing Secrets yahan use honge
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    refresh_token = os.environ.get("REFRESH_TOKEN")
    
    if not client_id or not client_secret or not refresh_token:
        print("❌ Error: Secrets missing. Check GitHub Settings.")
        return None

    creds_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/youtube.readonly"], # Sirf dekhne ki permission
        "expiry": "2030-01-01T00:00:00Z" 
    }
    
    try:
        creds = google.oauth2.credentials.Credentials.from_authorized_user_info(creds_data)
        return build("youtube", "v3", credentials=creds)
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return None

def get_channel_details(youtube, handle):
    print(f"\n🕵️‍♂️ Jasoosi: @{handle} ...")
    
    try:
        # 1. Channel ID nikalo
        request = youtube.channels().list(
            part="contentDetails",
            forHandle=f"@{handle}"
        )
        response = request.execute()
        
        if not response['items']:
            print(f"❌ Channel nahi mila: {handle}")
            return

        uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # 2. Videos scan karo
        playlist_request = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=10 # Last 10 videos
        )
        playlist_response = playlist_request.execute()
        
        all_tags = []
        categories = []

        print(f"   ⏳ Scanning last {len(playlist_response['items'])} videos...")

        for item in playlist_response['items']:
            video_id = item['snippet']['resourceId']['videoId']

            # 3. Video details (Tags/Category)
            vid_req = youtube.videos().list(
                part="snippet",
                id=video_id
            )
            vid_resp = vid_req.execute()
            
            if vid_resp['items']:
                snippet = vid_resp['items'][0]['snippet']
                
                if 'tags' in snippet:
                    all_tags.extend(snippet['tags'])
                
                if 'categoryId' in snippet:
                    cat_name = CATEGORY_MAP.get(snippet['categoryId'], f"ID: {snippet['categoryId']}")
                    categories.append(cat_name)

        # --- REPORT ---
        print(f"✅ REPORT FOR: @{handle}")

        if categories:
            common_cat = Counter(categories).most_common(1)[0][0]
            print(f"   📂 Main Category: {common_cat}")
        else:
            print("   📂 Category: Not Found")

        if all_tags:
            print("   🏷️  TOP HIDDEN TAGS:")
            top_tags = Counter(all_tags).most_common(10)
            for tag, count in top_tags:
                print(f"      - {tag}")
        else:
            print("      (No hidden tags found)")
        
        print("-" * 40)

    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    youtube = get_authenticated_service()
    if youtube:
        print("🚀 STARTING SPY BOT (Using Your Secrets)...")
        for handle in TARGET_HANDLES:
            get_channel_details(youtube, handle)
        print("🏁 MISSION COMPLETE.")
