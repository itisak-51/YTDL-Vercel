# app.py - Render.com Entry Point
import os
import sys
import logging

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from config import config
from auth import require_api_key

from utils import (
    extract_video_id,
    extract_playlist_id,
    detect_content_type,
    format_file_size
)

from youtube_api import (
    get_video_metadata,
    convert_video,
    get_file_size_with_stream
)

from playlist_handler import (
    get_playlist_info,
    extract_videos_from_playlist_url,
    get_videos_with_metadata
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# ============ API ENDPOINTS ============

@app.route('/', methods=['GET'])
def home():
    """Home endpoint - API information"""
    return jsonify({
        "name": "YouTube Downloader API",
        "version": "2.0.0",
        "status": "operational",
        "deployed": "Render.com",
        "endpoints": {
            "GET /": "API information",
            "POST /api/detect": "Detect content type (video/playlist/short)",
            "POST /api/metadata": "Get video metadata",
            "POST /api/download": "Get download URL with file size",
            "POST /api/download/direct": "Direct file download",
            "POST /api/batch": "Batch download multiple videos",
            "POST /api/playlist/info": "Get playlist information",
            "POST /api/playlist/extract": "Extract videos from playlist",
            "POST /api/playlist/download": "Download playlist videos (with selection)",
            "POST /api/test-connection": "Test connection to conversion service"
        },
        "authentication": {
            "method": "API Key",
            "header": config.API_KEY_NAME,
            "example": f"{config.API_KEY_NAME}: your_api_key_here"
        }
    })

@app.route('/api/detect', methods=['POST'])
@require_api_key
def detect():
    """Detect what type of YouTube content the URL is"""
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
        logger.error(f"Error in /api/detect: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "code": "INTERNAL_ERROR"
        }), 500

@app.route('/api/metadata', methods=['POST'])
@require_api_key
def get_metadata():
    """Get video metadata ONLY - fast!"""
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
        logger.error(f"Error in /api/metadata: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "code": "INTERNAL_ERROR"
        }), 500

@app.route('/api/download', methods=['POST'])
@require_api_key
def download():
    """Get download URL with accurate file size"""
    try:
        data = request.get_json()
        if not data or 'videoId' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'videoId' parameter",
                "code": "MISSING_PARAMETER"
            }), 400
        
        input_value = data['videoId']
        
        # Check if it's a playlist
        playlist_id = extract_playlist_id(input_value)
        if playlist_id:
            return jsonify({
                "success": False,
                "error": "This is a playlist. Use /api/playlist endpoint.",
                "playlistId": playlist_id,
                "code": "IS_PLAYLIST",
                "hint": "POST /api/playlist with the playlist ID"
            }), 400
        
        video_id = extract_video_id(input_value)
        if not video_id:
            return jsonify({
                "success": False,
                "error": "Invalid YouTube URL or Video ID",
                "code": "INVALID_VIDEO_ID"
            }), 400
        
        quality = data.get('quality', '720')
        format_type = data.get('format', 'mp4')
        
        # Validate quality
        valid_qualities = ['144', '240', '360', '480', '720', '1080']
        if quality not in valid_qualities:
            return jsonify({
                "success": False,
                "error": f"Invalid quality. Must be one of: {', '.join(valid_qualities)}",
                "code": "INVALID_QUALITY"
            }), 400
        
        # Validate format
        valid_formats = ['mp4', 'mp3', 'webm', '3gp', 'm4a', 'flv']
        if format_type not in valid_formats:
            return jsonify({
                "success": False,
                "error": f"Invalid format. Must be one of: {', '.join(valid_formats)}",
                "code": "INVALID_FORMAT"
            }), 400
        
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
        
        if not result.get('downloadUrl'):
            return jsonify({
                "success": False,
                "error": "Failed to get download URL",
                "code": "NO_DOWNLOAD_URL"
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
            "fileSizeReadable": file_size_info.get('sizeReadable', 'Unknown'),
            "fileSizeDetected": file_size_info.get('success', False),
            "expires": "Link expires in a few minutes. Download immediately."
        })
    except Exception as e:
        logger.error(f"Error in /api/download: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "code": "INTERNAL_ERROR"
        }), 500

@app.route('/api/download/direct', methods=['POST'])
@require_api_key
def download_direct():
    """Stream the file directly - returns the actual file"""
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
        
        if not result.get('downloadUrl'):
            return jsonify({
                "success": False,
                "error": "Failed to get download URL",
                "code": "NO_DOWNLOAD_URL"
            }), 500
        
        try:
            import requests
            dl_resp = requests.get(
                result['downloadUrl'], 
                stream=True, 
                headers=config.HEADERS,
                timeout=120
            )
            dl_resp.raise_for_status()
            
            filename = result.get('filename', f'youtube_{video_id}.{format_type}')
            content_length = dl_resp.headers.get('content-length')
            
            def generate():
                for chunk in dl_resp.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            
            response = Response(
                stream_with_context(generate()),
                content_type='application/octet-stream'
            )
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            if content_length:
                response.headers['Content-Length'] = content_length
            
            return response
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Download failed: {str(e)}",
                "code": "DOWNLOAD_FAILED"
            }), 500
    except Exception as e:
        logger.error(f"Error in /api/download/direct: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "code": "INTERNAL_ERROR"
        }), 500

@app.route('/api/batch', methods=['POST'])
@require_api_key
def batch_download():
    """Batch download multiple videos"""
    try:
        data = request.get_json()
        if not data or 'videos' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'videos' array",
                "code": "MISSING_VIDEOS"
            }), 400
        
        videos = data.get('videos', [])
        if not videos:
            return jsonify({
                "success": False,
                "error": "Empty videos list",
                "code": "EMPTY_VIDEOS"
            }), 400
        
        if len(videos) > 50:
            return jsonify({
                "success": False,
                "error": "Maximum 50 videos per batch request",
                "code": "BATCH_TOO_LARGE"
            }), 400
        
        quality = data.get('quality', '720')
        format_type = data.get('format', 'mp4')
        
        results = []
        failed = []
        
        for idx, video in enumerate(videos):
            if isinstance(video, dict):
                video_id = extract_video_id(video.get('videoId', ''))
                title = video.get('title', f'Video {idx + 1}')
            else:
                video_id = extract_video_id(video)
                title = f'Video {idx + 1}'
            
            if not video_id:
                failed.append({
                    "videoId": video,
                    "title": title,
                    "error": "Invalid video ID",
                    "code": "INVALID_VIDEO_ID"
                })
                continue
            
            metadata = get_video_metadata(video_id)
            if not metadata.get('success'):
                failed.append({
                    "videoId": video_id,
                    "title": title,
                    "error": "Video not found",
                    "code": "VIDEO_NOT_FOUND"
                })
                continue
            
            result = convert_video(video_id, quality, format_type)
            if 'error' in result:
                failed.append({
                    "videoId": video_id,
                    "title": metadata.get('title', title),
                    "error": result['error'],
                    "code": "CONVERSION_FAILED"
                })
                continue
            
            file_size_info = get_file_size_with_stream(result['downloadUrl'])
            
            results.append({
                "index": idx + 1,
                "videoId": video_id,
                "title": metadata.get('title'),
                "author": metadata.get('author'),
                "filename": result.get('filename'),
                "downloadUrl": result.get('downloadUrl'),
                "fileSize": file_size_info.get('size'),
                "fileSizeReadable": file_size_info.get('sizeReadable', 'Unknown')
            })
        
        return jsonify({
            "success": len(results) > 0,
            "total": len(videos),
            "succeeded": len(results),
            "failed": len(failed),
            "results": results,
            "failedList": failed
        })
    except Exception as e:
        logger.error(f"Error in /api/batch: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "code": "INTERNAL_ERROR"
        }), 500

@app.route('/api/playlist/info', methods=['POST'])
@require_api_key
def playlist_info():
    """Get information about a playlist"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'url' parameter",
                "code": "MISSING_PARAMETER"
            }), 400
        
        url = data['url']
        info = get_playlist_info(url)
        
        if not info.get('success'):
            return jsonify({
                "success": False,
                "error": info.get('error', 'Failed to get playlist info'),
                "code": "PLAYLIST_INFO_FAILED"
            }), 404
        
        return jsonify(info)
        
    except Exception as e:
        logger.error(f"Error in /api/playlist/info: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "code": "INTERNAL_ERROR"
        }), 500

@app.route('/api/playlist/extract', methods=['POST'])
@require_api_key
def playlist_extract():
    """Extract all video IDs from a playlist"""
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
        logger.error(f"Error in /api/playlist/extract: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "code": "INTERNAL_ERROR"
        }), 500

@app.route('/api/playlist/download', methods=['POST'])
@require_api_key
def playlist_download():
    """Download selected videos from a playlist"""
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
        logger.error(f"Error in /api/playlist/download: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "code": "INTERNAL_ERROR"
        }), 500

@app.route('/api/test-connection', methods=['POST'])
@require_api_key
def test_connection():
    """Test the connection to the conversion service"""
    try:
        data = request.get_json()
        if not data or 'videoId' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'videoId' parameter",
                "code": "MISSING_PARAMETER"
            }), 400
        
        video_id = data['videoId']
        
        import requests
        url = f"{config.BASE_URL}/sanity/key"
        params = {"id": video_id}
        
        resp = requests.get(
            url,
            params=params,
            headers=config.HEADERS,
            timeout=30
        )
        
        return jsonify({
            "success": True,
            "status_code": resp.status_code,
            "response_headers": dict(resp.headers),
            "response_preview": resp.text[:500] if resp.text else "Empty",
            "message": "Connection test completed"
        })
        
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "code": "CONNECTION_TEST_FAILED"
        }), 500

# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "code": "NOT_FOUND"
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": "Method not allowed",
        "code": "METHOD_NOT_ALLOWED"
    }), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "code": "INTERNAL_ERROR"
    }), 500

# ============ MAIN ============

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
