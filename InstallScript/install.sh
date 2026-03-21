#!/bin/bash

#===============================================================================
# SYNOPSIS
#    Downloads, extracts, and sets up the Wnclient project, ensuring Python is installed.
#
# DESCRIPTION
#    This script performs the following steps:
#    1. Downloads the repository ZIP from GitHub.
#    2. Extracts the ZIP to the current directory.
#    3. Checks if Python is installed; if not, installs it using the system package manager.
#    4. Changes to the extracted project folder.
#    5. Runs python setup.py.
#
# NOTES
#    Run this script with sudo if Python installation is required.
#    Supports apt (Debian/Ubuntu), pacman (Arch), dnf (Fedora), yum (RHEL/CentOS), zypper (openSUSE)
#===============================================================================

set -e  # Exit on error

# Variables
ZIP_URL="https://github.com/hexo141/Wnclient/archive/refs/heads/main.zip"
ZIP_FILE="/tmp/Wnclient-main.zip"
EXTRACT_PATH="./"
PROJECT_FOLDER="Wnclient-main"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to detect package manager
detect_package_manager() {
    if command -v apt &> /dev/null; then
        echo "apt"
    elif command -v pacman &> /dev/null; then
        echo "pacman"
    elif command -v dnf &> /dev/null; then
        echo "dnf"
    elif command -v yum &> /dev/null; then
        echo "yum"
    elif command -v zypper &> /dev/null; then
        echo "zypper"
    else
        echo "unknown"
    fi
}

# Function to install Python using package manager
install_python() {
    local pkg_manager=$1
    
    print_info "Installing Python using $pkg_manager..."
    
    case $pkg_manager in
        apt)
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv
            # Create python symlink if it doesn't exist
            if ! command -v python &> /dev/null && command -v python3 &> /dev/null; then
                sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1
            fi
            ;;
        pacman)
            sudo pacman -Sy --noconfirm python python-pip
            ;;
        dnf)
            sudo dnf install -y python3 python3-pip
            # Create python symlink if it doesn't exist
            if ! command -v python &> /dev/null && command -v python3 &> /dev/null; then
                sudo alternatives --set python /usr/bin/python3 || true
            fi
            ;;
        yum)
            sudo yum install -y python3 python3-pip
            # Create python symlink if it doesn't exist
            if ! command -v python &> /dev/null && command -v python3 &> /dev/null; then
                sudo alternatives --set python /usr/bin/python3 || true
            fi
            ;;
        zypper)
            sudo zypper install -y python3 python3-pip
            # Create python symlink if it doesn't exist
            if ! command -v python &> /dev/null && command -v python3 &> /dev/null; then
                sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1
            fi
            ;;
        *)
            print_error "Unsupported package manager. Please install Python manually."
            exit 1
            ;;
    esac
}

# Function to check if Python is properly installed
check_python() {
    # Check if python or python3 command exists
    if command -v python &> /dev/null; then
        local python_version=$(python --version 2>&1)
        print_success "Python found: $python_version"
        return 0
    elif command -v python3 &> /dev/null; then
        local python_version=$(python3 --version 2>&1)
        print_success "Python3 found: $python_version"
        # Create alias for python command
        alias python=python3 2>/dev/null || true
        return 0
    else
        return 1
    fi
}

# Step 1: Download the ZIP file
print_info "Downloading repository from $ZIP_URL ..."
if command -v wget &> /dev/null; then
    wget -O "$ZIP_FILE" "$ZIP_URL" 2>&1 | sed 's/^/[WGET] /'
elif command -v curl &> /dev/null; then
    curl -L -o "$ZIP_FILE" "$ZIP_URL" 2>&1 | sed 's/^/[CURL] /'
else
    print_error "Neither wget nor curl is installed. Please install one of them first."
    exit 1
fi

if [ ! -f "$ZIP_FILE" ]; then
    print_error "Failed to download the ZIP file."
    exit 1
fi
print_success "Download completed: $ZIP_FILE"

# Step 2: Extract the ZIP
print_info "Extracting $ZIP_FILE to $EXTRACT_PATH ..."
if command -v unzip &> /dev/null; then
    unzip -o "$ZIP_FILE" -d "$EXTRACT_PATH"
else
    print_error "unzip is not installed. Please install unzip first."
    print_info "You can install it with: sudo apt install unzip (Debian/Ubuntu) or sudo pacman -S unzip (Arch)"
    exit 1
fi

if [ ! -d "$EXTRACT_PATH/$PROJECT_FOLDER" ]; then
    print_error "Extraction failed. Folder '$PROJECT_FOLDER' not found."
    exit 1
fi
print_success "Extraction completed."

# Step 3: Check if Python is installed
print_info "Checking for Python installation..."
if ! check_python; then
    print_warning "Python not found. Attempting to install..."
    
    PKG_MANAGER=$(detect_package_manager)
    if [ "$PKG_MANAGER" = "unknown" ]; then
        print_error "Could not detect package manager. Please install Python manually."
        exit 1
    fi
    
    install_python "$PKG_MANAGER"
    
    # Verify installation
    if ! check_python; then
        print_error "Python installation failed. Please install Python manually."
        exit 1
    fi
fi

# Step 4: Navigate to the extracted project folder
PROJECT_PATH="$EXTRACT_PATH/$PROJECT_FOLDER"
print_info "Changing to directory: $PROJECT_PATH"
cd "$PROJECT_PATH" + "/InstallScript"

# Step 5: Run python setup.py
print_info "Running setup.py ..."
if command -v python &> /dev/null; then
    python ../setup.py
elif command -v python3 &> /dev/null; then
    python3 ../setup.py
else
    print_error "Python command not found even after installation."
    exit 1
fi

if [ $? -eq 0 ]; then
    print_success "Setup completed successfully."
    print_info "Running gen_path.py to generate necessary paths..."
    if command -v python &> /dev/null; then
        python gen_path.py
    elif command -v python3 &> /dev/null; then
        python3 gen_path.py
    else
        print_error "Python command not found even after installation."
        exit 1
    fi
else
    print_error "Failed to run setup.py."
    exit 1
fi

print_success "All tasks completed.You can now run the program using 'python main.py'"