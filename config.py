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
    
    # Headers
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Origin': 'https://frame.y2meta-uk.com',
        'Referer': 'https://frame.y2meta-uk.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-GPC': '1',
        'Connection': 'keep-alive'
    }

config = Config()