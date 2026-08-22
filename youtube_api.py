# youtube_api.py
import requests
import re
import logging
from config import config
from utils import format_file_size

logger = logging.getLogger(__name__)

def get_video_metadata(video_id):
    """Get video metadata using YouTube oEmbed API"""
    try:
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        resp = requests.get(oembed_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        return {
            "success": True,
            "videoId": video_id,
            "title": data.get("title", "Unknown Title"),
            "author": data.get("author_name", "Unknown Author"),
            "author_url": data.get("author_url", ""),
            "thumbnail": data.get("thumbnail_url", ""),
            "thumbnail_width": data.get("thumbnail_width", 0),
            "thumbnail_height": data.get("thumbnail_height", 0),
            "type": data.get("type", "video"),
            "provider": data.get("provider_name", "YouTube"),
            "embed_url": f"https://www.youtube.com/embed/{video_id}"
        }
    except Exception as e:
        logger.error(f"Error fetching metadata: {str(e)}")
        return {"success": False, "error": str(e)}

def get_conversion_key(video_id):
    """Get the authentication key for conversion"""
    try:
        resp = requests.get(
            f"{config.BASE_URL}/sanity/key", 
            params={"id": video_id}, 
            headers=config.HEADERS,
            timeout=30
        )
        resp.raise_for_status()
        return resp.json().get("key")
    except Exception as e:
        return {"error": str(e)}

def convert_video(video_id, quality="720", format="mp4"):
    """Convert the video and get download URL"""
    key_result = get_conversion_key(video_id)
    if isinstance(key_result, dict) and "error" in key_result:
        return key_result
    
    data = {
        "link": f"https://youtu.be/{video_id}",
        "format": format,
        "audioBitrate": "128" if format == "mp3" else "128",
        "videoQuality": quality,
        "filenameStyle": "pretty",
        "vCodec": "h264"
    }
    
    headers = config.HEADERS.copy()
    headers["key"] = key_result
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    
    try:
        resp = requests.post(
            f"{config.BASE_URL}/converter", 
            data=data, 
            headers=headers,
            timeout=config.REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        result = resp.json()
        
        return {
            "success": True,
            "downloadUrl": result.get("url"),
            "filename": result.get("filename", f"youtube_{video_id}.{format}"),
            "status": result.get("status", "unknown")
        }
    except Exception as e:
        return {"error": str(e)}

def get_file_size_with_stream(download_url):
    """Get file size using range request"""
    try:
        headers = config.HEADERS.copy()
        headers['Range'] = 'bytes=0-1023'
        
        resp = requests.get(
            download_url,
            headers=headers,
            stream=True,
            timeout=15,
            allow_redirects=True
        )
        
        content_range = resp.headers.get('content-range')
        if content_range:
            match = re.search(r'/(\d+)$', content_range)
            if match:
                size = int(match.group(1))
                return {"success": True, "size": size, "sizeReadable": format_file_size(size)}
        
        content_length = resp.headers.get('content-length')
        if content_length:
            size = int(content_length)
            if size > 0:
                return {"success": True, "size": size, "sizeReadable": format_file_size(size)}
        
        return {"success": False, "error": "Could not determine file size"}
    except Exception as e:
        return {"success": False, "error": str(e)}