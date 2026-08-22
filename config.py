# config.py
import os
from dotenv import load_dotenv

# Load .env only if not in Vercel (Vercel uses environment variables directly)
if not os.getenv('VERCEL'):
    load_dotenv()

class Config:
    # API Configuration - Get from environment variables
    API_KEY = os.getenv('API_KEY', 'your_super_secret_api_key_here')
    API_KEY_NAME = os.getenv('API_KEY_NAME', 'X-API-Key')
    
    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # YouTube Downloader Configuration
    BASE_URL = os.getenv('BASE_URL', 'https://cnv.cx/v2')
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 90))
    RATE_LIMIT_DELAY = int(os.getenv('RATE_LIMIT_DELAY', 2))
    
    # ============ UPDATED: Comprehensive Browser Headers ============
    HEADERS = {
        # Standard Browser Headers
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,en-GB;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        
        # Security & Fetch Headers
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Sec-GPC': '1',
        
        # Cache & Performance
        'Cache-Control': 'max-age=0',
        'Pragma': 'no-cache',
        
        # Additional Headers for API Requests
        'Origin': 'https://cnv.cx',
        'Referer': 'https://cnv.cx/',
        'DNT': '1',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
    }
    
    # Headers specifically for JSON API calls
    JSON_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/json',
        'Origin': 'https://cnv.cx',
        'Referer': 'https://cnv.cx/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }

config = Config()
