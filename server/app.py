#!/usr/bin/env python3
"""
YTTMP3.com Flask API Server
YouTube to MP3 converter backend using yt-dlp
"""

import os
import json
import tempfile
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",
    "http://localhost:3001", 
    "http://localhost:3002",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
    "https://yttmp3.com",
    "https://www.yttmp3.com"
])  # Enable CORS for Next.js frontend

# Configuration
TEMP_DIR = tempfile.mkdtemp(prefix="yttmp3_")
MAX_FILESIZE = 500 * 1024 * 1024  # 500MB
COOKIES_FILE = Path(__file__).parent.parent / "cookies.txt"

def get_ydl_opts(output_path=None, extract_flat=False, cookies_file=None):
    """Get yt-dlp options with proper headers and cookies"""
    
    opts = {
        'quiet': True,
        'no_warnings': False,  # Enable warnings for debugging
        'extract_flat': extract_flat,
        'writeinfojson': False,
        'writedescription': False,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'ignoreerrors': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Keep-Alive': '300',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        },
        # Additional options to bypass restrictions
        'extractor_args': {
            'youtube': {
                'skip': ['dash', 'hls'],  # Skip DASH and HLS to avoid some blocks
                'player_client': ['android', 'web'],  # Use multiple clients
                'player_skip': ['configs'],  # Skip config requests that might be blocked
            }
        },
        # Retry configuration
        'retries': 3,
        'sleep_interval': 1,
        'max_sleep_interval': 5,
        # Use different extraction methods
        'youtube_include_dash_manifest': False,
    }
    
    # Add cookies if available
    if cookies_file and cookies_file.exists() and cookies_file.stat().st_size > 100:
        try:
            opts['cookiefile'] = str(cookies_file)
            logger.info("Using cookies file for authentication")
        except Exception as e:
            logger.warning(f"Could not use cookies file: {e}")
    else:
        logger.info("No cookies file found, proceeding without authentication")
    
    # Add output template if specified
    if output_path:
        opts['outtmpl'] = output_path
        opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }]
    
    return opts

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'YTTMP3 Flask API'
    })

@app.route('/api/video-info', methods=['POST'])
def get_video_info():
    """Get YouTube video information"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url'].strip()
        if not url:
            return jsonify({'error': 'URL cannot be empty'}), 400
        
        logger.info(f"Fetching info for URL: {url}")
        
        # Try without cookies first (sometimes works better)
        ydl_opts_no_cookies = get_ydl_opts(extract_flat=False, cookies_file=None)
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts_no_cookies) as ydl:
                info = ydl.extract_info(url, download=False)
                logger.info("Successfully extracted info without cookies")
        except Exception as e1:
            logger.warning(f"Failed without cookies: {e1}")
            # Try with cookies as fallback
            try:
                ydl_opts_with_cookies = get_ydl_opts(extract_flat=False, cookies_file=COOKIES_FILE)
                with yt_dlp.YoutubeDL(ydl_opts_with_cookies) as ydl:
                    info = ydl.extract_info(url, download=False)
                    logger.info("Successfully extracted info with cookies")
            except Exception as e2:
                logger.error(f"Failed with cookies too: {e2}")
                # Try with different extractor args
                try:
                    ydl_opts_fallback = get_ydl_opts(extract_flat=False, cookies_file=None)
                    ydl_opts_fallback['extractor_args']['youtube']['player_client'] = ['android']
                    ydl_opts_fallback['http_headers']['User-Agent'] = 'com.google.android.youtube/17.36.4 (Linux; U; Android 12) gzip'
                    
                    with yt_dlp.YoutubeDL(ydl_opts_fallback) as ydl:
                        info = ydl.extract_info(url, download=False)
                        logger.info("Successfully extracted info with Android client")
                except Exception as e3:
                    logger.error(f"All methods failed: {e3}")
                    raise e3
        
        if not info:
            return jsonify({'error': 'Could not extract video information'}), 404
        
        # Format duration
        duration = info.get('duration', 0)
        if duration:
            minutes, seconds = divmod(duration, 60)
            duration_str = f"{int(minutes)}:{int(seconds):02d}"
        else:
            duration_str = "Unknown"
        
        # Extract thumbnails
        thumbnails = info.get('thumbnails', [])
        thumbnail_url = ''
        if thumbnails:
            # Get the highest quality thumbnail
            thumbnail_url = thumbnails[-1].get('url', '')
        
        video_info = {
            'videoId': info.get('id', ''),
            'title': info.get('title', 'Unknown Title'),
            'duration': duration_str,
            'thumbnail': thumbnail_url,
            'channel': info.get('uploader', 'Unknown Channel'),
            'viewCount': info.get('view_count', 0),
            'uploadDate': info.get('upload_date', ''),
            'description': info.get('description', '')[:200] + '...' if info.get('description') else ''
        }
        
        logger.info(f"Successfully extracted info for: {video_info['title']}")
        return jsonify(video_info)
    
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        logger.error(f"yt-dlp download error: {error_msg}")
        
        if 'age' in error_msg.lower() or 'sign in' in error_msg.lower():
            return jsonify({
                'error': 'Age-restricted content. Please ensure cookies are configured.'
            }), 403
        elif 'private' in error_msg.lower() or 'unavailable' in error_msg.lower():
            return jsonify({
                'error': 'Video is unavailable or private'
            }), 404
        else:
            return jsonify({
                'error': f'Failed to process video: {error_msg}'
            }), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in get_video_info: {str(e)}")
        return jsonify({
            'error': 'An unexpected error occurred. Please try again.'
        }), 500

@app.route('/api/download', methods=['POST'])
def download_video():
    """Download YouTube video as MP3"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url'].strip()
        title = data.get('title', 'audio')
        
        logger.info(f"Starting download for: {title}")
        
        # Clean filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title[:100]  # Limit length
        
        # Create temporary output file
        output_file = os.path.join(TEMP_DIR, f"{safe_title}.%(ext)s")
        
        # Get yt-dlp options for download
        ydl_opts = get_ydl_opts(output_path=output_file, cookies_file=COOKIES_FILE)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download and convert to MP3
            ydl.download([url])
            
            # Find the converted MP3 file
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
            
            logger.info(f"Successfully converted: {safe_title}.mp3 ({file_size} bytes)")
            
            # Send file and cleanup
            def remove_file(response):
                try:
                    os.remove(mp3_file)
                except:
                    pass
                return response
            
            return send_file(
                mp3_file,
                as_attachment=True,
                download_name=f"{safe_title}.mp3",
                mimetype='audio/mpeg'
            )
    
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({
            'error': f'Download failed: {str(e)}'
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in download_video: {str(e)}")
        return jsonify({
            'error': 'Download failed. Please try again.'
        }), 500

@app.route('/api/progress/<video_id>', methods=['GET'])
def get_progress(video_id):
    """Get download progress (placeholder for now)"""
    # This is a simple implementation
    # In production, you might want to use WebSockets or Server-Sent Events
    return jsonify({'progress': 100})

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Ensure temp directory exists
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Check if cookies file exists
    if COOKIES_FILE.exists():
        logger.info(f"Using cookies file: {COOKIES_FILE}")
    else:
        logger.warning(f"No cookies file found at: {COOKIES_FILE}")
        logger.warning("Some age-restricted videos may not work without cookies")
    
    # Run the Flask app
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting YTTMP3 Flask API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)