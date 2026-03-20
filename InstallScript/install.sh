#!/bin/bash

# Stop on errors
set -e

# Variables
ZIP_URL="https://github.com/hexo141/Wnclient/archive/refs/heads/main.zip"
ZIP_FILE="/tmp/Wnclient-main.zip"
EXTRACT_PATH="."                     # Extract to current directory
PROJECT_FOLDER="Wnclient-main"

# Colors for output (optional)
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

info() {
    echo -e "${CYAN}[INFO] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    exit 1
}

# Step 1: Download the ZIP file
info "Downloading repository from $ZIP_URL ..."
if command -v wget >/dev/null 2>&1; then
    wget -q -O "$ZIP_FILE" "$ZIP_URL" || error "Failed to download with wget."
elif command -v curl >/dev/null 2>&1; then
    curl -s -L -o "$ZIP_FILE" "$ZIP_URL" || error "Failed to download with curl."
else
    error "Neither wget nor curl is installed. Please install one and try again."
fi
success "Download completed: $ZIP_FILE"

# Step 2: Extract the ZIP
info "Extracting $ZIP_FILE to $EXTRACT_PATH ..."
if ! command -v unzip >/dev/null 2>&1; then
    error "unzip is not installed. Please install it (e.g., sudo apt install unzip) and try again."
fi
unzip -q "$ZIP_FILE" -d "$EXTRACT_PATH" || error "Failed to extract ZIP file."
success "Extraction completed."

# Step 3: Check for Python installation
info "Checking for Python installation..."
if command -v python3 >/dev/null 2>&1; then
    success "Python3 is already installed: $(python3 --version)"
else
    info "Python3 not found. Attempting to install..."

    # Detect package manager and install python3
    if command -v apt >/dev/null 2>&1; then
        info "Using apt to install python3..."
        sudo apt update && sudo apt install -y python3 python3-pip || error "Failed to install python3 via apt."
    elif command -v yum >/dev/null 2>&1; then
        info "Using yum to install python3..."
        sudo yum install -y python3 python3-pip || error "Failed to install python3 via yum."
    elif command -v dnf >/dev/null 2>&1; then
        info "Using dnf to install python3..."
        sudo dnf install -y python3 python3-pip || error "Failed to install python3 via dnf."
    elif command -v pacman >/dev/null 2>&1; then
        info "Using pacman to install python3..."
        sudo pacman -S --noconfirm python python-pip || error "Failed to install python3 via pacman."
    else
        error "No supported package manager found. Please install python3 manually."
    fi

    # Verify installation
    if command -v python3 >/dev/null 2>&1; then
        success "Python3 installed successfully: $(python3 --version)"
    else
        error "Python3 installation failed. Please install it manually."
    fi
fi

# Step 4: Navigate to the extracted project folder
PROJECT_PATH="$EXTRACT_PATH/$PROJECT_FOLDER"
if [ ! -d "$PROJECT_PATH" ]; then
    error "Extracted folder '$PROJECT_FOLDER' not found at $EXTRACT_PATH"
fi
info "Changing to directory: $PROJECT_PATH"
cd "$PROJECT_PATH"

# Step 5: Run python setup.py
info "Running python setup.py ..."
python3 setup.py || error "Failed to run python setup.py"

success "All tasks completed."
