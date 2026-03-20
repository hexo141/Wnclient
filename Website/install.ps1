# PowerShell installation script for Wnclient project
# This script automatically downloads client files, configures Python and installs dependencies
# Note: Does not use winget - manual Python installation required if not present

Write-Host "Starting installation for Wnclient project..." -ForegroundColor Green

# Function to download file
function Download-File {
    param(
        [string]$Url,
        [string]$OutputPath
    )
    try {
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($Url, $OutputPath)
        return $true
    } catch {
        Write-Host "Download failed: $_" -ForegroundColor Red
        return $false
    }
}

# Function to extract zip
function Expand-ZipFile {
    param(
        [string]$ZipPath,
        [string]$Destination
    )
    try {
        Expand-Archive -Path $ZipPath -DestinationPath $Destination -Force
        return $true
    } catch {
        Write-Host "Extraction failed: $_" -ForegroundColor Red
        return $false
    }
}

# Download client files from GitHub
Write-Host "`nDownloading Wnclient files from GitHub..." -ForegroundColor Cyan
$REPO_URL = "https://github.com/hexo141/Wnclient/archive/refs/heads/main.zip"
$DOWNLOAD_DIR = "$env:TEMP\wnclient_download"
$ZIP_FILE = "$DOWNLOAD_DIR\main.zip"

# Create temporary directory
if (Test-Path $DOWNLOAD_DIR) {
    Remove-Item -Recurse -Force $DOWNLOAD_DIR
}
New-Item -ItemType Directory -Path $DOWNLOAD_DIR -Force | Out-Null

# Download the zip file
if (Download-File -Url $REPO_URL -OutputPath $ZIP_FILE) {
    Write-Host "✓ Download completed successfully." -ForegroundColor Green
} else {
    Write-Host "✗ Failed to download from $REPO_URL" -ForegroundColor Red
    exit 1
}

# Extract the zip file
Write-Host "Extracting files..." -ForegroundColor Cyan
if (Expand-ZipFile -ZipPath $ZIP_FILE -Destination $DOWNLOAD_DIR) {
    Write-Host "✓ Extraction completed successfully." -ForegroundColor Green
} else {
    Write-Host "✗ Failed to extract files." -ForegroundColor Red
    exit 1
}

# Find the extracted directory (will be named Wnclient-main)
$EXTRACTED_DIR = Get-ChildItem -Path $DOWNLOAD_DIR -Directory | Where-Object { $_.Name -eq "Wnclient-main" } | Select-Object -First 1

if (-not $EXTRACTED_DIR) {
    Write-Host "✗ Failed to find extracted files." -ForegroundColor Red
    exit 1
}

# Copy files to current directory (or specified target)
$TARGET_DIR = if ($args.Count -gt 0) { $args[0] } else { "." }
Write-Host "Copying files to $TARGET_DIR..." -ForegroundColor Cyan

# Get absolute path
$TARGET_DIR = Resolve-Path $TARGET_DIR -ErrorAction SilentlyContinue
if (-not $TARGET_DIR) {
    New-Item -ItemType Directory -Path $TARGET_DIR -Force | Out-Null
    $TARGET_DIR = Resolve-Path $TARGET_DIR
}

# Copy all files
Copy-Item -Path "$($EXTRACTED_DIR.FullName)\*" -Destination $TARGET_DIR -Recurse -Force

# Clean up
Remove-Item -Recurse -Force $DOWNLOAD_DIR
Write-Host "✓ Files copied successfully." -ForegroundColor Green

# Check if Python is installed
function Test-PythonInstalled {
    try {
        $pythonVersion = python --version 2>&1
        $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
        Write-Host "✓ Python detected: $pythonVersion" -ForegroundColor Yellow
        Write-Host "  Path: $pythonPath" -ForegroundColor Gray
        return $true
    } catch {
        return $false
    }
}

# Check if Python is installed (version 3.8+)
if (-not (Test-PythonInstalled)) {
    Write-Host "`n⚠ Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python 3.8 or higher:" -ForegroundColor Cyan
    Write-Host "  1. Download from: https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "  2. During installation, CHECK 'Add Python to PATH'" -ForegroundColor White
    Write-Host "  3. After installation, restart this script" -ForegroundColor White
    Write-Host ""
    
    # Optional: Offer Chocolatey installation (if user has choco)
    $useChoco = Read-Host "Do you have Chocolatey installed and want to use it? (y/N)"
    if ($useChoco -eq 'y' -or $useChoco -eq 'Y') {
        try {
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
            Write-Host "Installing Python via Chocolatey..." -ForegroundColor Yellow
            choco install python311 -y --install-arguments '/AddToPath=1'
            # Refresh PATH in current session
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
            if (Test-PythonInstalled) {
                Write-Host "✓ Python installed via Chocolatey successfully." -ForegroundColor Green
            } else {
                Write-Host "⚠ Python installed but not detected. Please restart your terminal and run this script again." -ForegroundColor Yellow
                exit 1
            }
        } catch {
            Write-Host "✗ Chocolatey installation failed. Please install Python manually." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Waiting for manual Python installation..." -ForegroundColor Yellow
        Write-Host "Press Enter after installing Python, or Ctrl+C to cancel."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        
        # Re-check Python
        if (-not (Test-PythonInstalled)) {
            Write-Host "✗ Python still not detected. Installation aborted." -ForegroundColor Red
            exit 1
        }
    }
}

# Verify Python version (3.8+)
$pythonVersionOutput = python --version 2>&1
if ($pythonVersionOutput -match "Python (\d+)\.(\d+)") {
    $major = [int]$matches[1]
    $minor = [int]$matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
        Write-Host "✗ Python $major.$minor detected. Please install Python 3.8 or higher." -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Python version $major.$minor is compatible." -ForegroundColor Green
}

# Install uv package manager
Write-Host "`nInstalling uv package manager..." -ForegroundColor Cyan
try {
    # Use python -m pip to ensure we're using the correct Python
    python -m pip install --user uv
    Write-Host "✓ uv installed successfully." -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to install uv." -ForegroundColor Red
    Write-Host "  Try running: python -m pip install --user uv" -ForegroundColor Gray
    exit 1
}

# Refresh PATH to include user Scripts directory (where uv is installed)
$userScripts = "$env:APPDATA\Python\Python3*\Scripts"
if (Test-Path $userScripts) {
    $env:Path = "$userScripts;$env:Path"
}

# Install dependencies using uv
Write-Host "`nInstalling project dependencies with uv..." -ForegroundColor Cyan
try {
    # Get the actual Python executable path for uv
    $pythonExe = python -c "import sys; print(sys.executable)"
    
    # Install with --only-binary :all: for faster, more reliable installs
    uv pip install -r requirements.txt --python $pythonExe --only-binary :all:
    
    Write-Host "✓ Dependencies installed successfully." -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to install dependencies." -ForegroundColor Red
    Write-Host "  Check your requirements.txt and network connection." -ForegroundColor Gray
    exit 1
}

# Final verification
Write-Host "`n" + ("="*50) -ForegroundColor Green
Write-Host "✓ Installation completed successfully!" -ForegroundColor Green
Write-Host "="*50 -ForegroundColor Green
Write-Host "`nYou can now run the project:" -ForegroundColor Cyan
Write-Host "  python main.py" -ForegroundColor White
Write-Host "`nTip: Use 'uv run python main.py' to run in isolated environment." -ForegroundColor Gray