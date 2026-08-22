# playlist_handler.py
import requests
import re
import logging
from utils import extract_video_id, extract_playlist_id
from youtube_api import get_video_metadata

logger = logging.getLogger(__name__)

def extract_videos_from_playlist_url(url):
    """Extract all video IDs from a YouTube playlist URL"""
    playlist_id = extract_playlist_id(url)
    if not playlist_id:
        return {"success": False, "error": "Invalid playlist URL"}
    
    playlist_title = "Unknown Playlist"
    
    # Try to scrape video IDs from the playlist page
    try:
        video_ids = []
        playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        resp = requests.get(playlist_url, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            # Try to get playlist title
            title_match = re.search(r'"title":"([^"]+)"', resp.text)
            if title_match:
                playlist_title = title_match.group(1)
            
            # Extract video IDs from the page
            pattern = r'"videoId":"([a-zA-Z0-9_-]{11})"'
            matches = re.findall(pattern, resp.text)
            
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
    
    return {
        "success": False,
        "playlistId": playlist_id,
        "playlistTitle": playlist_title,
        "error": "Could not extract videos from playlist. Please provide videoIds manually.",
        "videos": [],
        "method": "failed"
    }

def get_playlist_info(url):
    """Get playlist information including title"""
    playlist_id = extract_playlist_id(url)
    if not playlist_id:
        return {"success": False, "error": "Could not extract playlist ID from URL"}
    
    try:
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
    """Get metadata for multiple videos"""
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
