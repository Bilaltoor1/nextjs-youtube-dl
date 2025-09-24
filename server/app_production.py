#!/usr/bin/env python3
"""
Production-ready signature-based YouTube converter API
Implements competitor-style request signing and advanced evasion
"""

import os
import json
import tempfile
import subprocess
import hashlib
import hmac
import base64
import time
import random
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",
    "https://yttmp3.com",
    "https://www.yttmp3.com"
])

# Configuration
TEMP_DIR = tempfile.mkdtemp(prefix="yttmp3_")
MAX_FILESIZE = 500 * 1024 * 1024  # 500MB
COOKIES_FILE = Path(__file__).parent.parent / "cookies.txt"
SECRET_KEY = os.environ.get('YTTMP3_SECRET', 'yttmp3_production_key_2024')

# Rate limiting
from collections import defaultdict
request_counts = defaultdict(list)
RATE_LIMIT = 15  # requests per minute per IP
RATE_WINDOW = 60  # seconds

def rate_limit(f):
    """Rate limiting decorator"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        current_time = time.time()
        
        # Clean old requests
        request_counts[client_ip] = [
            req_time for req_time in request_counts[client_ip]
            if current_time - req_time < RATE_WINDOW
        ]
        
        # Check rate limit
        if len(request_counts[client_ip]) >= RATE_LIMIT:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({
                'error': 'Too many requests. Please wait a moment and try again.',
                'retry_after': 60
            }), 429
        
        # Add current request
        request_counts[client_ip].append(current_time)
        
        # Add random delay
        time.sleep(random.uniform(0.1, 0.3))
        
        return f(*args, **kwargs)
    return decorated_function

class SignatureManager:
    """Manages request signatures like competitor"""
    
    def __init__(self, secret_key):
        self.secret_key = secret_key.encode()
    
    def generate_signature(self, video_id, format_type="mp3", timestamp=None):
        """Generate encrypted signature"""
        if timestamp is None:
            timestamp = time.time()
        
        random_val = random.random()
        
        # Create signature string (similar to competitor)
        sig_data = f"{video_id}|{format_type}|{timestamp}|{random_val}"
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.secret_key,
            sig_data.encode(),
            hashlib.sha256
        ).digest()
        
        # Base64 encode like competitor
        encoded_sig = base64.b64encode(signature).decode()
        
        return {
            'sig': encoded_sig,
            'v': video_id,
            'f': format_type,
            't': timestamp,
            '_': random_val
        }
    
    def verify_signature(self, sig_data):
        """Verify signature"""
        try:
            sig_string = f"{sig_data['v']}|{sig_data['f']}|{sig_data['t']}|{sig_data['_']}"
            expected_sig = hmac.new(
                self.secret_key,
                sig_string.encode(),
                hashlib.sha256
            ).digest()
            expected_encoded = base64.b64encode(expected_sig).decode()
            return hmac.compare_digest(sig_data['sig'], expected_encoded)
        except:
            return False

# Global signature manager
sig_manager = SignatureManager(SECRET_KEY)

def extract_video_id(url):
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

def run_ytdlp_with_signature(video_id, action="info", output_path=None):
    """Run yt-dlp with signature-based configuration"""
    
    # Generate signature for this request
    sig_data = sig_manager.generate_signature(video_id)
    
    # Advanced yt-dlp command with multiple fallbacks
    cmd_base = [
        'yt-dlp',
        '--quiet',
        '--no-warnings',
        '--extract-flat' if action == 'info' else '--no-extract-flat',
        '--user-agent', 'Mozilla/5.0 (Android 11; Mobile; rv:94.0) Gecko/94.0 Firefox/94.0',
        '--referer', 'https://www.youtube.com/',
    ]
    
    # Add cookies if available
    if COOKIES_FILE.exists() and COOKIES_FILE.stat().st_size > 100:
        cmd_base.extend(['--cookies', str(COOKIES_FILE)])
    
    # Configure for different actions
    if action == "info":
        cmd_base.extend([
            '--dump-json',
            '--no-download',
        ])
        url = f"https://www.youtube.com/watch?v={video_id}"
        cmd = cmd_base + [url]
    
    elif action == "download":
        cmd_base.extend([
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '320K',
            '--output', output_path,
            '--format', 'bestaudio[ext=m4a]/bestaudio/best',
        ])
        url = f"https://www.youtube.com/watch?v={video_id}"
        cmd = cmd_base + [url]
    
    else:
        raise ValueError(f"Invalid action: {action}")
    
    logger.info(f"Running yt-dlp with signature {sig_data['sig'][:20]}... for video {video_id}")
    
    # Add random delay
    time.sleep(random.uniform(0.2, 0.8))
    
    try:
        # Run command with timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=TEMP_DIR
        )
        
        if result.returncode != 0:
            logger.error(f"yt-dlp failed: {result.stderr}")
            raise Exception(f"yt-dlp error: {result.stderr}")
        
        return result.stdout, sig_data
    
    except subprocess.TimeoutExpired:
        raise Exception("Request timeout - video may be too long or unavailable")
    except Exception as e:
        raise Exception(f"Extraction failed: {str(e)}")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'YTTMP3 Production API'
    })

@app.route('/api/v1/convert', methods=['GET', 'POST'])
@rate_limit
def convert_with_signature():
    """Main conversion endpoint like competitor (with signature)"""
    try:
        # Get parameters (like competitor's URL structure)
        if request.method == 'GET':
            sig = request.args.get('sig')
            video_id = request.args.get('v')
            format_type = request.args.get('f', 'mp3')
            timestamp = request.args.get('t')
            random_val = request.args.get('_')
        else:
            data = request.get_json()
            sig = data.get('sig')
            video_id = data.get('v')
            format_type = data.get('f', 'mp3')
            timestamp = data.get('t')
            random_val = data.get('_')
        
        if not all([sig, video_id, timestamp, random_val]):
            return jsonify({'error': 'Missing required signature parameters'}), 400
        
        # Verify signature
        sig_data = {
            'sig': sig,
            'v': video_id,
            'f': format_type,
            't': float(timestamp),
            '_': float(random_val)
        }
        
        if not sig_manager.verify_signature(sig_data):
            return jsonify({'error': 'Invalid signature'}), 403
        
        # Check signature age (prevent replay attacks)
        if time.time() - float(timestamp) > 300:  # 5 minutes
            return jsonify({'error': 'Signature expired'}), 403
        
        logger.info(f"Converting video {video_id} with valid signature")
        
        # Generate safe filename
        safe_title = f"yttmp3_{video_id}"
        output_pattern = os.path.join(TEMP_DIR, f"{safe_title}.%(ext)s")
        
        # Download and convert
        output, sig_info = run_ytdlp_with_signature(video_id, "download", output_pattern)
        
        # Find the converted file
        mp3_file = None
        for file in os.listdir(TEMP_DIR):
            if file.startswith(safe_title) and file.endswith('.mp3'):
                mp3_file = os.path.join(TEMP_DIR, file)
                break
        
        if not mp3_file or not os.path.exists(mp3_file):
            return jsonify({'error': 'Conversion failed'}), 500
        
        # Check file size
        file_size = os.path.getsize(mp3_file)
        if file_size > MAX_FILESIZE:
            os.remove(mp3_file)
            return jsonify({'error': 'File too large'}), 413
        
        logger.info(f"Successfully converted {video_id} to MP3 ({file_size} bytes)")
        
        # Return file
        return send_file(
            mp3_file,
            as_attachment=True,
            download_name=f"{video_id}.mp3",
            mimetype='audio/mpeg'
        )
    
    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/video-info', methods=['POST'])
@rate_limit
def get_video_info():
    """Get video info (generates signature internally)"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url'].strip()
        video_id = extract_video_id(url)
        
        logger.info(f"Getting info for video: {video_id}")
        
        # Get video info with signature
        output, sig_data = run_ytdlp_with_signature(video_id, "info")
        
        # Parse JSON output
        info = json.loads(output)
        
        # Format response
        duration = info.get('duration', 0)
        if duration:
            minutes, seconds = divmod(duration, 60)
            duration_str = f"{int(minutes)}:{int(seconds):02d}"
        else:
            duration_str = "Unknown"
        
        thumbnails = info.get('thumbnails', [])
        thumbnail_url = thumbnails[-1].get('url', '') if thumbnails else ''
        
        video_info = {
            'videoId': video_id,
            'title': info.get('title', 'Unknown Title'),
            'duration': duration_str,
            'thumbnail': thumbnail_url,
            'channel': info.get('uploader', 'Unknown Channel'),
            'viewCount': info.get('view_count', 0),
            'signature': sig_data  # Include signature for next request
        }
        
        return jsonify(video_info)
    
    except Exception as e:
        logger.error(f"Video info error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
@rate_limit
def download_video():
    """Download video using signature from video-info"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url'].strip()
        title = data.get('title', 'audio')
        sig_data = data.get('signature')
        
        # If signature provided, use it; otherwise generate new one
        if sig_data and sig_manager.verify_signature(sig_data):
            video_id = sig_data['v']
        else:
            video_id = extract_video_id(url)
            sig_data = sig_manager.generate_signature(video_id)
        
        logger.info(f"Downloading video: {video_id}")
        
        # Clean filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title[:50] if safe_title else f"yttmp3_{video_id}"
        
        output_pattern = os.path.join(TEMP_DIR, f"{safe_title}.%(ext)s")
        
        # Download with signature
        output, sig_info = run_ytdlp_with_signature(video_id, "download", output_pattern)
        
        # Find converted file
        mp3_file = None
        for file in os.listdir(TEMP_DIR):
            if file.startswith(safe_title) and file.endswith('.mp3'):
                mp3_file = os.path.join(TEMP_DIR, file)
                break
        
        if not mp3_file or not os.path.exists(mp3_file):
            return jsonify({'error': 'Conversion failed'}), 500
        
        file_size = os.path.getsize(mp3_file)
        if file_size > MAX_FILESIZE:
            os.remove(mp3_file)
            return jsonify({'error': 'File too large'}), 413
        
        logger.info(f"Download complete: {safe_title}.mp3 ({file_size} bytes)")
        
        return send_file(
            mp3_file,
            as_attachment=True,
            download_name=f"{safe_title}.mp3",
            mimetype='audio/mpeg'
        )
    
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Ensure temp directory exists
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Check yt-dlp installation
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
        logger.info("yt-dlp is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("yt-dlp not found! Please install: pip install yt-dlp")
    
    # Check cookies
    if COOKIES_FILE.exists():
        logger.info(f"Using cookies file: {COOKIES_FILE}")
    else:
        logger.warning("No cookies file found - some videos may not work")
    
    # Run Flask app
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting YTTMP3 Production API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)