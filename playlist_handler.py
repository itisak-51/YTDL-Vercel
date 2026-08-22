# playlist_handler.py
import requests
import re
import logging
from utils import extract_video_id, extract_playlist_id, detect_content_type
from youtube_api import get_video_metadata

logger = logging.getLogger(__name__)

def get_playlist_videos_from_url(playlist_url):
    """
    Extract video IDs from a YouTube playlist URL
    Uses multiple methods to get videos
    """
    playlist_id = extract_playlist_id(playlist_url)
    if not playlist_id:
        return {
            "success": False,
            "error": "Could not extract playlist ID",
            "playlistId": None
        }
    
    # Try to get videos using YouTube's oEmbed (returns only first video)
    # For full playlist, we need to use YouTube Data API or scraping
    # This is a fallback method that returns the playlist info
    
    try:
        # Get playlist metadata
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/playlist?list={playlist_id}"
        resp = requests.get(oembed_url, timeout=10)
        playlist_title = "Unknown Playlist"
        if resp.status_code == 200:
            data = resp.json()
            playlist_title = data.get('title', 'Unknown Playlist')
    except:
        playlist_title = "Unknown Playlist"
    
    # Note: Full playlist extraction requires YouTube Data API v3
    # For now, we'll return the playlist info and let user provide video IDs
    return {
        "success": False,
        "playlistId": playlist_id,
        "playlistTitle": playlist_title,
        "error": "Full playlist extraction requires YouTube Data API. Please provide videoIds array.",
        "videos": [],
        "method": "requires_api"
    }

def extract_videos_from_playlist_url(url):
    """
    Extract all video IDs from a YouTube playlist URL
    This method uses a public playlist extractor
    """
    playlist_id = extract_playlist_id(url)
    if not playlist_id:
        return {"success": False, "error": "Invalid playlist URL"}
    
    # Method 1: Try using YouTube's oEmbed for playlist metadata
    try:
        # This only gives us the first video, not all
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/playlist?list={playlist_id}"
        resp = requests.get(oembed_url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            playlist_title = data.get('title', 'Unknown Playlist')
        else:
            playlist_title = 'Unknown Playlist'
    except:
        playlist_title = 'Unknown Playlist'
    
    # Method 2: Try to scrape video IDs from the playlist page
    # This is a fallback method
    try:
        video_ids = []
        playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36'
        }
        
        resp = requests.get(playlist_url, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            # Try to extract video IDs from the page
            # YouTube uses a specific pattern for video IDs
            pattern = r'"videoId":"([a-zA-Z0-9_-]{11})"'
            matches = re.findall(pattern, resp.text)
            
            # Remove duplicates
            seen = set()
            video_ids = []
            for vid in matches:
                if vid not in seen:
                    seen.add(vid)
                    video_ids.append(vid)
            
            if video_ids:
                return {
                    "success": True,
                    "playlistId": playlist_id,
                    "playlistTitle": playlist_title,
                    "totalVideos": len(video_ids),
                    "videos": video_ids,
                    "method": "scraped"
                }
    except Exception as e:
        logger.error(f"Error scraping playlist: {str(e)}")
    
    # Method 3: Use yt-dlp or other tools (not implemented here)
    # Return what we have
    return {
        "success": False,
        "playlistId": playlist_id,
        "playlistTitle": playlist_title,
        "error": "Could not extract videos from playlist. Please provide videoIds manually.",
        "videos": [],
        "method": "failed"
    }

def get_playlist_info(url):
    """
    Get playlist information including title and video count
    """
    playlist_id = extract_playlist_id(url)
    if not playlist_id:
        return {
            "success": False,
            "error": "Could not extract playlist ID from URL"
        }
    
    try:
        # Get playlist metadata
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/playlist?list={playlist_id}"
        resp = requests.get(oembed_url, timeout=10)
        playlist_title = "Unknown Playlist"
        if resp.status_code == 200:
            data = resp.json()
            playlist_title = data.get('title', 'Unknown Playlist')
    except:
        playlist_title = "Unknown Playlist"
    
    return {
        "success": True,
        "playlistId": playlist_id,
        "playlistTitle": playlist_title,
        "url": f"https://www.youtube.com/playlist?list={playlist_id}"
    }

def get_videos_with_metadata(video_ids):
    """
    Get metadata for multiple videos
    """
    results = []
    failed = []
    
    for idx, video_id in enumerate(video_ids):
        metadata = get_video_metadata(video_id)
        if metadata.get('success'):
            results.append({
                "index": idx + 1,
                "videoId": video_id,
                "title": metadata.get('title'),
                "author": metadata.get('author'),
                "thumbnail": metadata.get('thumbnail')
            })
        else:
            failed.append({
                "videoId": video_id,
                "error": metadata.get('error', 'Unknown error')
            })
    
    return {
        "success": True,
        "total": len(video_ids),
        "succeeded": len(results),
        "failed": len(failed),
        "videos": results,
        "failedList": failed
    }