# YTTMP3.com - YouTube to MP3 Converter

A fast, secure, and production-ready YouTube to MP3 converter built with Next.js 15 and TailwindCSS v4.

## 🚀 Features

- **High-Quality Conversion**: Convert YouTube videos to MP3 with up to 320kbps quality
- **Bot Detection Avoidance**: Advanced headers and cookie management to prevent blocking
- **Production Ready**: Optimized for VPS deployment with proper security headers
- **Responsive Design**: Beautiful, mobile-first design with dark mode support
- **Fast & Secure**: No file storage on server, direct streaming download
- **SEO Optimized**: Comprehensive meta tags and structured data

## 🛠️ Technology Stack

- **Frontend**: Next.js 15 with App Router
- **Styling**: TailwindCSS v4
- **YouTube Processing**: @distube/ytdl-core with enhanced headers
- **Deployment**: Standalone output for VPS hosting

## 📋 Prerequisites

- Node.js 18+ 
- npm or yarn
- VPS server with sufficient bandwidth
- Domain name (yttmp3.com)

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd nextjs-youtube-dl
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure cookies (Important for Production)**
   - Edit `cookies.txt` file
   - Follow instructions in the file to add YouTube cookies
   - This prevents bot detection and login-related issues

4. **Development mode**
   ```bash
   npm run dev
   ```

5. **Production build**
   ```bash
   npm run build
   npm start
   ```

## 🍪 Cookie Configuration (Critical for Production)

yt-dlp requires the Netscape cookie file format for authenticated extraction (age-restricted/login-protected videos).

Recommended: use the "Get cookies.txt LOCALLY" extension. Export for `youtube.com` and paste into `cookies.txt` in the project root. The format should look like this (tab-separated):

```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	1767418737	__Secure-3PSID	<value>
.youtube.com	TRUE	/	TRUE	0	YSC	<value>
.youtube.com	TRUE	/	FALSE	0	PREF	f4=4010000&hl=en
... more lines ...
```

Notes:
- Place `cookies.txt` at the project root so the Flask server can read it at `server/../cookies.txt`.
- Set secure permissions in production: `chmod 600 cookies.txt` and keep it out of version control.
- Refresh cookies periodically to avoid expiry.
- Ensure `ffmpeg` is installed on the server: `sudo apt-get install -y ffmpeg`.

## 🏗️ Production Deployment

### Automated Deployment
```bash
chmod +x deploy.sh
./deploy.sh
```

### Manual Deployment (Next.js + Flask)
1. Build Next.js
   ```bash
   npm run build
   ```

2. Start processes with PM2 (Next.js and Flask via Gunicorn)
   ```bash
   npm install -g pm2
   # Next.js (port 3000)
   pm2 start npm --name "yttmp3-web" -- start
   
   # Flask API (port 5000)
   cd server
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt gunicorn
   # Run Flask with multiple workers
   pm2 start "venv/bin/gunicorn -w 2 -b 0.0.0.0:5000 app:app" --name "yttmp3-api"

   # Persist
   pm2 save
   pm2 startup
   ```

3. Configure Nginx (Reverse Proxy + API routing)
   ```nginx
   server {
     listen 80;
     server_name yttmp3.com www.yttmp3.com;
     return 301 https://$host$request_uri;
   }

   server {
     listen 443 ssl http2;
     server_name yttmp3.com www.yttmp3.com;

     ssl_certificate /etc/letsencrypt/live/yttmp3.com/fullchain.pem;
     ssl_certificate_key /etc/letsencrypt/live/yttmp3.com/privkey.pem;

     # Tight timeouts for long conversions
     client_max_body_size 100M;
     proxy_read_timeout 600s;
     proxy_connect_timeout 60s;
     proxy_send_timeout 600s;

     # Serve Next.js
     location / {
       proxy_pass http://127.0.0.1:3000;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection $connection_upgrade;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
     }

     # Proxy API to Flask
     location /api/ {
       proxy_pass http://127.0.0.1:5000/api/;
       proxy_http_version 1.1;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
     }
   }
   ```

4. **SSL Certificate with Let's Encrypt**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yttmp3.com -d www.yttmp3.com
   ```

## 🛡️ Security Features

- **Anti-Bot Headers**: Comprehensive user-agent and header spoofing
- **Cookie Management**: Automatic cookie handling for YouTube authentication
- **Content Security Policy**: Strict CSP headers for XSS prevention
- **Rate Limiting**: Built-in protection against abuse
- **No File Storage**: Direct streaming prevents server storage issues

## 📊 Performance Optimizations

- **Standalone Output**: Optimized for VPS deployment
- **Image Optimization**: WebP/AVIF support for thumbnails
- **Compression**: Gzip compression enabled
- **Caching**: Static asset caching with proper headers
- **Code Splitting**: Automatic code splitting by Next.js

## 🔍 SEO Configuration

The application includes comprehensive SEO optimization:
- Open Graph tags
- Twitter Card support
- Structured data
- Canonical URLs
- XML sitemap generation

## 🚨 Troubleshooting

### Common Issues

1. **"Sign in to confirm your age" error**
   - Configure `cookies.txt` with valid YouTube cookies
   - Ensure cookies are from a logged-in session

2. **"Video unavailable" error**
   - Video might be private or region-restricted
   - Check if the video URL is correct

3. **Download timeout**
   - Increase server timeout settings
   - Check server bandwidth and resources

4. **Bot detection**
   - Update cookies.txt regularly
   - Ensure user-agent headers are up to date

### Log Files
- Next.js logs: `~/.pm2/logs/yttmp3-web-out.log` and `yttmp3-web-error.log`
- Flask logs: `~/.pm2/logs/yttmp3-api-out.log` and `yttmp3-api-error.log`

## 📈 Monitoring

Recommended monitoring setup:
- **PM2 Monitoring**: Built-in process monitoring
- **Nginx Logs**: Access and error log analysis
- **Server Metrics**: CPU, Memory, Disk usage
- **Uptime Monitoring**: External uptime monitoring service

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Legal Notice

This tool is for educational and personal use only. Users are responsible for respecting YouTube's Terms of Service and applicable copyright laws. The developers are not responsible for any misuse of this software.

## 🆘 Support

For technical support or questions:
- Create an issue on GitHub
- Check the troubleshooting section above
- Review the cookies.txt configuration

---

**Built with ❤️ for the community**
