#!/bin/bash
# VideoGenFX VPS Installation Script

set -e

echo "🚀 Installing VideoGenFX on VPS..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv nginx ffmpeg git

# Install additional multimedia libraries
sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev
sudo apt install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev
sudo apt install -y libgtk-3-dev libcairo2-dev libgirepository1.0-dev

# Create application directory
APP_DIR="/opt/videogenfx"
echo "📁 Creating application directory: $APP_DIR"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Clone or copy application files
echo "📥 Setting up application files..."
# If you're running this script from the app directory:
cp -r . $APP_DIR/
cd $APP_DIR

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📂 Creating application directories..."
mkdir -p uploads outputs/images outputs/videos temp logs

# Set permissions
echo "🔐 Setting permissions..."
sudo chown -R www-data:www-data $APP_DIR
sudo chmod -R 755 $APP_DIR

# Configure Nginx
echo "🌐 Configuring Nginx..."
sudo cp deploy/nginx.conf /etc/nginx/sites-available/videogenfx

# Update paths in nginx config
sudo sed -i "s|/path/to/your/videogenfx|$APP_DIR|g" /etc/nginx/sites-available/videogenfx

# Enable site
sudo ln -sf /etc/nginx/sites-available/videogenfx /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Configure systemd service
echo "⚙️ Configuring systemd service..."
sudo cp deploy/systemd_service.conf /etc/systemd/system/videogenfx.service

# Update paths in service file
sudo sed -i "s|/path/to/your/videogenfx|$APP_DIR|g" /etc/systemd/system/videogenfx.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable videogenfx
sudo systemctl start videogenfx

# Check service status
echo "✅ Checking service status..."
sudo systemctl status videogenfx --no-pager

# Configure firewall (if ufw is installed)
if command -v ufw &> /dev/null; then
    echo "🔥 Configuring firewall..."
    sudo ufw allow 'Nginx Full'
    sudo ufw allow ssh
fi

echo "🎉 VideoGenFX installation completed!"
echo ""
echo "📋 Next steps:"
echo "1. Update your domain in /etc/nginx/sites-available/videogenfx"
echo "2. Configure SSL certificate (optional)"
echo "3. Set up your API keys via the web interface"
echo "4. Test the application at http://your-server-ip"
echo ""
echo "🔧 Useful commands:"
echo "  sudo systemctl status videogenfx    # Check service status"
echo "  sudo systemctl restart videogenfx   # Restart service"
echo "  sudo journalctl -u videogenfx -f    # View logs"
echo "  sudo nginx -t                       # Test nginx config"