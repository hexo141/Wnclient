#!/bin/bash

# Linux installation script for Wnclient project
# This script automatically configures Python and installs dependencies

echo "Starting installation for Wnclient project..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
if ! command_exists curl && ! command_exists wget; then
    echo "Error: Neither curl nor wget is installed. Please install one of them."
    exit 1
fi

# Function to download file
download_file() {
    local url="$1"
    local output="$2"
    if command_exists curl; then
        curl -L -o "$output" "$url"
    elif command_exists wget; then
        wget -O "$output" "$url"
    fi
}

# Download client files from GitHub
echo "Downloading Wnclient files from GitHub..."
REPO_URL="https://github.com/hexo141/Wnclient/archive/refs/heads/main.zip"
DOWNLOAD_DIR="/tmp/wnclient_download"
ZIP_FILE="$DOWNLOAD_DIR/main.zip"

# Create temporary directory
mkdir -p "$DOWNLOAD_DIR"

# Download the zip file
if download_file "$REPO_URL" "$ZIP_FILE"; then
    echo "Download completed successfully."
else
    echo "Failed to download from $REPO_URL"
    exit 1
fi

# Check if unzip is installed
if ! command_exists unzip; then
    echo "unzip is not installed. Installing unzip..."
    if command_exists apt; then
        sudo apt update && sudo apt install -y unzip
    elif command_exists yum; then
        sudo yum install -y unzip
    elif command_exists dnf; then
        sudo dnf install -y unzip
    elif command_exists pacman; then
        sudo pacman -S --noconfirm unzip
    else
        echo "Please install unzip manually."
        exit 1
    fi
fi

# Extract the zip file
echo "Extracting files..."
unzip -q "$ZIP_FILE" -d "$DOWNLOAD_DIR"

# Find the extracted directory (will be named Wnclient-main)
EXTRACTED_DIR=$(find "$DOWNLOAD_DIR" -maxdepth 1 -type d -name "Wnclient-main" | head -n 1)

if [ -z "$EXTRACTED_DIR" ]; then
    echo "Failed to find extracted files."
    exit 1
fi

# Copy files to current directory (or specified target)
TARGET_DIR="${1:-.}"
echo "Copying files to $TARGET_DIR..."

# Copy all files except .git, .github, etc.
rsync -av --exclude='.git' --exclude='.github' --exclude='__pycache__' "$EXTRACTED_DIR/" "$TARGET_DIR/" 2>/dev/null || cp -r "$EXTRACTED_DIR"/* "$TARGET_DIR/"

# Clean up
rm -rf "$DOWNLOAD_DIR"
echo "Files downloaded and extracted successfully."

# Check if Python 3 is installed
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    echo "Python 3 is already installed: $PYTHON_VERSION"
else
    echo "Python 3 is not installed. Installing Python 3..."
    # Detect package manager and install Python 3
    if command_exists apt; then
        # Debian/Ubuntu
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv
    elif command_exists yum; then
        # CentOS/RHEL
        sudo yum install -y python3 python3-pip
    elif command_exists dnf; then
        # Fedora
        sudo dnf install -y python3 python3-pip
    elif command_exists pacman; then
        # Arch Linux
        sudo pacman -S --noconfirm python python-pip
    else
        echo "Unsupported package manager. Please install Python 3 manually."
        exit 1
    fi
    echo "Python 3 installed successfully."
fi

# Install uv package manager
echo "Installing uv package manager..."
if command_exists pip3; then
    pip3 install --user uv
elif command_exists pip; then
    pip install --user uv
else
    echo "pip not found. Please check Python installation."
    exit 1
fi

# Add local bin to PATH if not already there
export PATH="$HOME/.local/bin:$PATH"

# Verify uv installation
if ! command_exists uv; then
    echo "uv installation failed. Please check your PATH or Python installation."
    exit 1
fi

echo "uv installed successfully."

# Install dependencies using uv
echo "Installing project dependencies..."
if uv pip install -r requirements.txt --python "$(python3 -c 'import sys; print(sys.executable)')" --only-binary :all:; then
    echo "Dependencies installed successfully."
else
    echo "Failed to install dependencies. Please check the error messages above."
    exit 1
fi

echo "Installation completed! You can now run the project."
echo "To run: python3 main.py"