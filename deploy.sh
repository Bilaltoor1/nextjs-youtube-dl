#!/bin/bash

# Production deployment script for YTTMP3.com
# Make this file executable: chmod +x deploy.sh

set -euo pipefail

echo "🚀 Starting deployment for YTTMP3.com..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

DOMAIN=${DOMAIN:-yttmp3.com}
EMAIL=${EMAIL:-admin@${DOMAIN}}

# Check if Node.js & npm are installed
if ! command -v node &> /dev/null; then
    print_status "Installing Node.js (using apt)..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi
if ! command -v npm &> /dev/null; then
    print_error "npm is not available after Node install. Aborting."
    exit 1
fi

# Install system dependencies
print_status "Installing system dependencies (nginx, ffmpeg, python3-venv)..."
sudo apt-get update -y
sudo apt-get install -y nginx ffmpeg python3-venv python3-pip

print_status "Installing Node dependencies..."
npm ci --omit=dev || npm install --production

# Check if cookies.txt exists and has content
if [ ! -f "cookies.txt" ] || [ ! -s "cookies.txt" ]; then
    print_warning "cookies.txt is missing or empty!"
    print_warning "For production use, you should add YouTube cookies to avoid bot detection."
    print_warning "See cookies.txt template for instructions."
else
    print_status "cookies.txt found and configured."
fi

print_status "Building Next.js application..."
npm run build

# Set production environment
export NODE_ENV=production

mkdir -p logs tmp server

# Set proper file permissions
chmod 600 cookies.txt 2>/dev/null || true
chmod 755 logs tmp

# Python/Flask backend setup
print_status "Setting up Python virtual environment for Flask API..."
cd server
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Ensure cookies.txt exists one level up
if [ ! -f "../cookies.txt" ] || [ ! -s "../cookies.txt" ]; then
    print_warning "cookies.txt is missing or empty at project root. Age-restricted videos may fail."
else
    chmod 600 ../cookies.txt || true
fi

# Start services with PM2
print_status "Starting services with PM2..."
deactivate || true
cd ..
npm i -g pm2 >/dev/null 2>&1 || true
pm2 start npm --name "yttmp3-web" -- start || pm2 restart yttmp3-web
pm2 start "server/venv/bin/gunicorn -w 2 -b 0.0.0.0:5000 app:app" --name "yttmp3-api" --cwd "$(pwd)/server" || pm2 restart yttmp3-api
pm2 save

# Configure nginx
print_status "Configuring nginx for domain $DOMAIN..."
NGINX_SITE="/etc/nginx/sites-available/${DOMAIN}"
if [ -f "nginx.conf" ]; then
    TMP_CONF=$(mktemp)
    sed "s/{{DOMAIN}}/${DOMAIN}/g" nginx.conf > "$TMP_CONF"
    sudo mv "$TMP_CONF" "$NGINX_SITE"
    sudo ln -sf "$NGINX_SITE" "/etc/nginx/sites-enabled/${DOMAIN}"
    # Disable default site
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t && sudo systemctl reload nginx
    print_status "nginx configured and reloaded."
else
    print_warning "nginx.conf not found in project root. Skipping nginx config."
fi

print_status "Deployment completed successfully for ${DOMAIN}!"
echo "Optional: obtain SSL via Let's Encrypt:"
echo "  sudo apt-get install -y certbot python3-certbot-nginx"
echo "  sudo certbot --nginx -d ${DOMAIN} -d www.${DOMAIN} --email ${EMAIL} --agree-tos --non-interactive"