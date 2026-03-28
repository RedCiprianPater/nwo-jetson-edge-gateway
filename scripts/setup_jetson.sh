#!/bin/bash
# Setup script for Jetson Orin

echo "Setting up NWO Jetson Edge Gateway..."

# Check if running on Jetson
if ! grep -q "Jetson" /proc/device-tree/model 2>/dev/null; then
    echo "Warning: This script is designed for Jetson Orin"
fi

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo pip3 install docker-compose
fi

# Enable Jetson Clocks for max performance
sudo jetson_clocks

# Create model cache directory
mkdir -p models/cache
mkdir -p logs

# Set environment variables
echo "export NWO_API_KEY=your_api_key_here" >> ~/.bashrc
echo "export NWO_AGENT_ID=g1_001" >> ~/.bashrc

echo "Setup complete! Please:"
echo "1. Set your NWO_API_KEY in ~/.bashrc"
echo "2. Run: source ~/.bashrc"
echo "3. Start with: docker-compose up -d"
