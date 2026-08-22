# api/index.py
import os
import sys
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from flask_cors import CORS
from config import config
from auth import require_api_key
from utils import extract_video_id, detect_content_type
from youtube_api import get_video_metadata, convert_video, get_file_size_with_stream
from playlist_handler import get_playlist_info, extract_videos_from_playlist_url, get_videos_with_metadata

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# ============ API ENDPOINTS ============

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "name": "YouTube Downloader API",
        "version": "2.0.0",
        "status": "operational",
        "deployed": "Vercel",
        "endpoints": {
            "GET /": "API information",
            "POST /api/detect": "Detect content type",
            "POST /api/metadata": "Get video metadata",
            "POST /api/download": "Get download URL with file size",
            "POST /api/playlist/extract": "Extract videos from playlist",
            "POST /api/playlist/download": "Download selected videos"
        },
        "authentication": {
            "header": config.API_KEY_NAME,
            "example": f"{config.API_KEY_NAME}: your_api_key_here"
        }
    })

@app.route('/api/detect', methods=['POST'])
@require_api_key
def detect():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'url' parameter",
                "code": "MISSING_PARAMETER"
            }), 400
        
        url = data['url'].strip()
        result = detect_content_type(url)
        
        if result['type'] == 'playlist':
            playlist_info = get_playlist_info(url)
            if playlist_info:
                result.update(playlist_info)
        
        return jsonify({
            "success": True,
            "detected": result
        })
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "code": "INTERNAL_ERROR"
        }), 500

@app.route('/api/metadata', methods=['POST'])
@require_api_key
def get_metadata():
    try:
        data = request.get_json()
        if not data or 'videoId' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'videoId' parameter",
                "code": "MISSING_PARAMETER"
            }), 400
        
        video_id = extract_video_id(data['videoId'])
        if not video_id:
            return jsonify({
                "success": False,
                "error": "Invalid YouTube URL or Video ID",
                "code": "INVALID_VIDEO_ID"
            }), 400
        
        metadata = get_video_metadata(video_id)
        if not metadata.get('success'):
            return jsonify({
                "success": False,
                "error": metadata.get('error', 'Failed to fetch metadata'),
                "code": "METADATA_FETCH_FAILED"
            }), 404
        
        return jsonify(metadata)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "code": "INTERNAL_ERROR"
        }), 500

@app.route('/api/download', methods=['POST'])
@require_api_key
def download():
    try:
        data = request.get_json()
        if not data or 'videoId' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'videoId' parameter",
                "code": "MISSING_PARAMETER"
            }), 400
        
        video_id = extract_video_id(data['videoId'])
        if not video_id:
            return jsonify({
                "success": False,
                "error": "Invalid YouTube URL or Video ID",
                "code": "INVALID_VIDEO_ID"
            }), 400
        
        quality = data.get('quality', '720')
        format_type = data.get('format', 'mp4')
        
        metadata = get_video_metadata(video_id)
        if not metadata.get('success'):
            return jsonify({
                "success": False,
                "error": "Video not found",
                "code": "VIDEO_NOT_FOUND"
            }), 404
        
        result = convert_video(video_id, quality, format_type)
        if 'error' in result:
            return jsonify({
                "success": False,
                "error": result['error'],
                "code": "CONVERSION_FAILED"
            }), 500
        
        file_size_info = get_file_size_with_stream(result['downloadUrl'])
        
        return jsonify({
            "success": True,
            "videoId": video_id,
            "title": metadata.get('title'),
            "author": metadata.get('author'),
            "thumbnail": metadata.get('thumbnail'),
            "quality": quality,
            "format": format_type,
            "filename": result.get('filename'),
            "downloadUrl": result.get('downloadUrl'),
            "fileSize": file_size_info.get('size'),
            "fileSizeReadable": file_size_info.get('sizeReadable', 'Unknown')
        })
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "code": "INTERNAL_ERROR"
        }), 500

@app.route('/api/playlist/extract', methods=['POST'])
@require_api_key
def playlist_extract():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'url' parameter",
                "code": "MISSING_PARAMETER"
            }), 400
        
        url = data['url']
        result = extract_videos_from_playlist_url(url)
        
        if not result.get('success'):
            playlist_id = extract_playlist_id(url)
            return jsonify({
                "success": False,
                "error": result.get('error', 'Could not extract videos from playlist'),
                "playlistId": playlist_id,
                "playlistTitle": result.get('playlistTitle', 'Unknown Playlist'),
                "code": "EXTRACTION_FAILED",
                "hint": "Please use /api/playlist/download with videoIds array"
            }), 400
        
        video_ids = result.get('videos', [])
        videos_with_metadata = get_videos_with_metadata(video_ids)
        
        return jsonify({
            "success": True,
            "playlistId": result.get('playlistId'),
            "playlistTitle": result.get('playlistTitle'),
            "totalVideos": result.get('totalVideos', len(video_ids)),
            "method": result.get('method', 'unknown'),
            "videos": videos_with_metadata.get('videos', []),
            "failedList": videos_with_metadata.get('failedList', []),
            "message": f"Found {len(videos_with_metadata.get('videos', []))} videos in playlist"
        })
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "code": "INTERNAL_ERROR"
        }), 500

@app.route('/api/playlist/download', methods=['POST'])
@require_api_key
def playlist_download():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Missing request body",
                "code": "MISSING_BODY"
            }), 400
        
        playlist_id = data.get('playlistId')
        video_ids = data.get('videoIds', [])
        quality = data.get('quality', '720')
        format_type = data.get('format', 'mp4')
        
        if not playlist_id:
            return jsonify({
                "success": False,
                "error": "Missing 'playlistId' parameter",
                "code": "MISSING_PLAYLIST_ID"
            }), 400
        
        if not video_ids:
            return jsonify({
                "success": False,
                "error": "Please provide 'videoIds' array to download",
                "playlistId": playlist_id,
                "code": "MISSING_VIDEO_IDS"
            }), 400
        
        if len(video_ids) > 50:
            return jsonify({
                "success": False,
                "error": "Maximum 50 videos per playlist request",
                "code": "PLAYLIST_TOO_LARGE"
            }), 400
        
        playlist_info = get_playlist_info(f"https://www.youtube.com/playlist?list={playlist_id}")
        
        results = []
        failed = []
        
        for idx, video_id in enumerate(video_ids):
            metadata = get_video_metadata(video_id)
            if not metadata.get('success'):
                failed.append({
                    "videoId": video_id,
                    "title": f"Video {idx + 1}",
                    "error": metadata.get('error', 'Video not found'),
                    "code": "VIDEO_NOT_FOUND"
                })
                continue
            
            result = convert_video(video_id, quality, format_type)
            if 'error' in result:
                failed.append({
                    "videoId": video_id,
                    "title": metadata.get('title', f"Video {idx + 1}"),
                    "error": result['error'],
                    "code": "CONVERSION_FAILED"
                })
                continue
            
            file_size_info = get_file_size_with_stream(result['downloadUrl'])
            
            results.append({
                "index": idx + 1,
                "videoId": video_id,
                "title": metadata.get('title'),
                "author": metadata.get('author', 'Unknown'),
                "thumbnail": metadata.get('thumbnail', ''),
                "filename": result.get('filename'),
                "downloadUrl": result.get('downloadUrl'),
                "fileSize": file_size_info.get('size'),
                "fileSizeReadable": file_size_info.get('sizeReadable', 'Unknown'),
                "quality": quality,
                "format": format_type
            })
        
        return jsonify({
            "success": len(results) > 0,
            "playlistId": playlist_id,
            "playlistTitle": playlist_info.get('playlistTitle', 'Unknown Playlist'),
            "total": len(video_ids),
            "succeeded": len(results),
            "failed": len(failed),
            "quality": quality,
            "format": format_type,
            "results": results,
            "failedList": failed
        })
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "code": "INTERNAL_ERROR"
        }), 500

# Vercel handler
app.debug = False

# This is the entry point for Vercel
def handler(request, context):
    return app(request.environ, context.start_response)

# For local testing
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
