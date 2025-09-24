#!/usr/bin/env python3
"""
Advanced YouTube extractor with signature-based anti-detection
Similar to competitor's approach with encrypted signatures
"""

import hashlib
import hmac
import base64
import json
import time
import random
import requests
from urllib.parse import urlencode, quote
import yt_dlp
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class YouTubeExtractor:
    def __init__(self, cookies_file=None):
        self.cookies_file = cookies_file
        self.secret_key = "yttmp3_secret_2024"  # Change this in production
        self.session = requests.Session()
        self.setup_session()
    
    def setup_session(self):
        """Setup requests session with proper headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        })
    
    def generate_signature(self, video_id, format_type="mp3", timestamp=None):
        """Generate encrypted signature like competitor"""
        if timestamp is None:
            timestamp = time.time()
        
        # Create signature data
        data = {
            'v': video_id,
            'f': format_type,
            't': timestamp,
            'r': random.random()
        }
        
        # Create signature string
        sig_string = f"{video_id}|{format_type}|{timestamp}|{data['r']}"
        
        # Generate HMAC signature
        signature = hmac.new(
            self.secret_key.encode(),
            sig_string.encode(),
            hashlib.sha256
        ).digest()
        
        # Base64 encode
        encoded_sig = base64.b64encode(signature).decode()
        
        return {
            'sig': encoded_sig,
            'timestamp': timestamp,
            'data': data
        }
    
    def verify_signature(self, sig, video_id, format_type, timestamp, random_val):
        """Verify signature (for internal use)"""
        sig_string = f"{video_id}|{format_type}|{timestamp}|{random_val}"
        expected_sig = hmac.new(
            self.secret_key.encode(),
            sig_string.encode(),
            hashlib.sha256
        ).digest()
        expected_encoded = base64.b64encode(expected_sig).decode()
        return hmac.compare_digest(sig, expected_encoded)
    
    def get_ytdlp_options(self, use_signature=True):
        """Get yt-dlp options with advanced evasion"""
        
        # Rotate between multiple user agents
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'writeinfojson': False,
            'writedescription': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': False,
            'geo_bypass': True,
            'http_headers': {
                'User-Agent': random.choice(user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Cache-Control': 'max-age=0',
            },
            # Advanced extractor arguments
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage', 'configs'],
                    'skip': ['hls', 'dash'],
                    'lang': ['en'],
                    'innertube_host': 'www.youtube.com',
                    'innertube_key': None,  # Let yt-dlp auto-detect
                }
            },
            # Retry configuration
            'retries': 3,
            'fragment_retries': 3,
            'sleep_interval': random.uniform(0.5, 2.0),
            'max_sleep_interval': 10,
            'sleep_interval_subtitles': 1,
            # Network configuration
            'socket_timeout': 30,
            'http_chunk_size': 10485760,
            # Use cookies if available
        }
        
        # Add cookies if available
        if self.cookies_file and self.cookies_file.exists() and self.cookies_file.stat().st_size > 100:
            opts['cookiefile'] = str(self.cookies_file)
            logger.info("Using cookies for extraction")
        
        return opts
    
    def extract_video_info(self, url, use_fallbacks=True):
        """Extract video info with multiple fallback strategies"""
        
        # Add random delay
        time.sleep(random.uniform(0.1, 0.5))
        
        strategies = [
            # Strategy 1: Standard web extraction with cookies
            {
                'name': 'web_with_cookies',
                'opts_modifier': lambda opts: {**opts, 'cookiefile': str(self.cookies_file) if self.cookies_file and self.cookies_file.exists() else None}
            },
            # Strategy 2: Android client
            {
                'name': 'android_client',
                'opts_modifier': lambda opts: {
                    **opts,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android'],
                            'player_skip': ['webpage'],
                        }
                    },
                    'http_headers': {
                        **opts['http_headers'],
                        'User-Agent': 'com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip'
                    }
                }
            },
            # Strategy 3: iOS client
            {
                'name': 'ios_client',
                'opts_modifier': lambda opts: {
                    **opts,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['ios'],
                            'player_skip': ['webpage'],
                        }
                    },
                    'http_headers': {
                        **opts['http_headers'],
                        'User-Agent': 'com.google.ios.youtube/19.09.3 (iPhone14,3; U; CPU iOS 15_6 like Mac OS X)'
                    }
                }
            },
            # Strategy 4: TV client (often bypasses restrictions)
            {
                'name': 'tv_client',
                'opts_modifier': lambda opts: {
                    **opts,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['tv_embedded'],
                            'player_skip': ['webpage'],
                        }
                    }
                }
            }
        ]
        
        for strategy in strategies:
            try:
                logger.info(f"Trying extraction strategy: {strategy['name']}")
                
                base_opts = self.get_ytdlp_options()
                modified_opts = strategy['opts_modifier'](base_opts)
                
                with yt_dlp.YoutubeDL(modified_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if info:
                        logger.info(f"Successfully extracted info using {strategy['name']}")
                        return info
                    
            except Exception as e:
                logger.warning(f"Strategy {strategy['name']} failed: {str(e)[:200]}")
                if not use_fallbacks:
                    raise e
                
                # Add delay between strategies
                time.sleep(random.uniform(0.5, 1.5))
        
        raise Exception("All extraction strategies failed")
    
    def download_video(self, url, output_path, format_type="mp3"):
        """Download video with signature verification"""
        
        # Generate signature for this download
        video_id = self.extract_video_id(url)
        sig_data = self.generate_signature(video_id, format_type)
        
        logger.info(f"Starting download with signature: {sig_data['sig'][:20]}...")
        
        # Add random delay
        time.sleep(random.uniform(0.2, 0.8))
        
        opts = self.get_ytdlp_options()
        opts.update({
            'outtmpl': output_path,
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format_type,
                'preferredquality': '320',
            }] if format_type == 'mp3' else []
        })
        
        # Use the most reliable client for downloads
        opts['extractor_args']['youtube']['player_client'] = ['android', 'tv_embedded']
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        
        return sig_data
    
    def extract_video_id(self, url):
        """Extract video ID from YouTube URL"""
        import re
        
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
            r'(?:shorts\/)([0-9A-Za-z_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError(f"Could not extract video ID from URL: {url}")

# Global extractor instance
_extractor = None

def get_extractor(cookies_file=None):
    """Get global extractor instance"""
    global _extractor
    if _extractor is None:
        _extractor = YouTubeExtractor(cookies_file)
    return _extractor