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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        resp = requests.get(oembed_url, headers=headers, timeout=10)
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
        url = f"{config.BASE_URL}/sanity/key"
        params = {"id": video_id}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,en-GB;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Origin': 'https://cnv.cx',
            'Referer': 'https://cnv.cx/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-GPC': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'DNT': '1',
        }
        logger.info(f"Requesting key for video: {video_id}")
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json().get("key")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            return get_conversion_key_alternative(video_id)
        return {"error": f"HTTP Error: {e}"}
    except Exception as e:
        return {"error": str(e)}

def get_conversion_key_alternative(video_id):
    """Alternative method to get conversion key with different headers"""
    try:
        url = f"{config.BASE_URL}/sanity/key"
        params = {"id": video_id}
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://cnv.cx',
            'Referer': 'https://cnv.cx/',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
        }
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json().get("key")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            return {"error": "Access blocked. The service is currently unavailable from this location."}
        return {"error": f"HTTP Error: {e}"}
    except Exception as e:
        return {"error": str(e)}

def convert_video(video_id, quality="720", format_type="mp4"):
    """Convert the video and get download URL"""
    key_result = get_conversion_key(video_id)
    if isinstance(key_result, dict) and "error" in key_result:
        key_result = get_conversion_key_alternative(video_id)
        if isinstance(key_result, dict) and "error" in key_result:
            return key_result
    
    key = key_result
    data = {
        "link": f"https://youtu.be/{video_id}",
        "format": format_type,
        "audioBitrate": "128" if format_type == "mp3" else "128",
        "videoQuality": quality,
        "filenameStyle": "pretty",
        "vCodec": "h264"
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9,en-GB;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://cnv.cx',
        'Referer': 'https://cnv.cx/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-GPC': '1',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'DNT': '1',
        'key': key
    }
    try:
        resp = requests.post(f"{config.BASE_URL}/converter", data=data, headers=headers, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        result = resp.json()
        return {
            "success": True,
            "downloadUrl": result.get("url"),
            "filename": result.get("filename", f"youtube_{video_id}.{format_type}"),
            "status": result.get("status", "unknown")
        }
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            return {"error": "Access blocked. The conversion service is currently unavailable from this location."}
        return {"error": f"HTTP Error: {e}"}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Conversion taking too long."}
    except Exception as e:
        return {"error": str(e)}

def get_file_size_with_stream(download_url):
    """Get file size using range request"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Range': 'bytes=0-1023'
        }
        resp = requests.get(download_url, headers=headers, stream=True, timeout=15, allow_redirects=True)
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
