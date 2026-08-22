# utils.py
import re

def extract_video_id(url_or_id):
    """
    Extract YouTube video ID from URL or return as-is
    Supports: youtube.com/watch?v=, youtu.be/, youtube.com/shorts/
    """
    if not url_or_id:
        return None
    
    # If it's already just the ID (11 characters)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    
    # Try to extract from URL
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None

def extract_playlist_id(url):
    """
    Extract YouTube playlist ID from URL
    Supports: youtube.com/playlist?list=, &list= in any URL
    """
    if not url:
        return None
    
    # Check for list parameter in URL
    match = re.search(r'[&?]list=([a-zA-Z0-9_-]+)', url)
    if match:
        playlist_id = match.group(1)
        # Valid playlist IDs usually start with PL, OL, RD, UU, FL, LL
        if playlist_id.startswith(('PL', 'OL', 'RD', 'UU', 'FL', 'LL')):
            return playlist_id
    
    # Check if the entire input is a playlist ID
    if re.match(r'^(PL|OL|RD|UU|FL|LL)[a-zA-Z0-9_-]+$', url):
        return url
    
    return None

def detect_content_type(input_value):
    """
    Detect what type of YouTube content the input is
    Returns: {
        'type': 'video' | 'playlist' | 'short' | 'unknown',
        'videoId': str or None,
        'playlistId': str or None,
        'isPlaylist': bool
    }
    """
    if not input_value:
        return {'type': 'unknown', 'isPlaylist': False}
    
    # Check for shorts
    if 'shorts/' in input_value:
        video_id = extract_video_id(input_value)
        if video_id:
            return {
                'type': 'short',
                'videoId': video_id,
                'playlistId': None,
                'isPlaylist': False,
                'message': f'Detected YouTube Short: {video_id}'
            }
    
    # Check for playlist
    playlist_id = extract_playlist_id(input_value)
    if playlist_id:
        # Check if it also has a video ID (video within playlist)
        video_id = extract_video_id(input_value)
        return {
            'type': 'playlist',
            'videoId': video_id,
            'playlistId': playlist_id,
            'isPlaylist': True,
            'message': f'Detected Playlist: {playlist_id}',
            'hasVideo': video_id is not None,
            'videoIdInPlaylist': video_id
        }
    
    # Check for video
    video_id = extract_video_id(input_value)
    if video_id:
        return {
            'type': 'video',
            'videoId': video_id,
            'playlistId': None,
            'isPlaylist': False,
            'message': f'Detected Video: {video_id}'
        }
    
    return {
        'type': 'unknown',
        'videoId': None,
        'playlistId': None,
        'isPlaylist': False,
        'message': 'Could not detect YouTube content'
    }

def format_file_size(bytes):
    """Format file size in human readable format"""
    if not bytes:
        return "Unknown"
    try:
        bytes = int(bytes)
        if bytes == 0:
            return "0 B"
        k = 1024
        sizes = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        while bytes >= k and i < len(sizes) - 1:
            bytes /= k
            i += 1
        return f"{bytes:.2f} {sizes[i]}"
    except:
        return "Unknown"