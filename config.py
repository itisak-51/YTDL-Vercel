import os
from dotenv import load_dotenv

# Load .env only if not in Vercel
if not os.getenv('VERCEL'):
    load_dotenv()

class Config:
    # API Configuration
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
    
    # Comprehensive Browser Headers
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,en-GB;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Sec-GPC': '1',
        'Cache-Control': 'max-age=0',
        'Pragma': 'no-cache',
        'Origin': 'https://frame.y2meta-uk.com',
        'Referer': 'https://frame.y2meta-uk.com',
        'DNT': '1',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
    }

config = Config()
