<#
.SYNOPSIS
    Downloads, extracts, and sets up the Wnclient project, ensuring Python is installed.

.DESCRIPTION
    This script performs the following steps:
    1. Downloads the repository ZIP from GitHub.
    2. Extracts the ZIP to the current directory.
    3. Checks if Python is installed; if not, installs it using winget (or a fallback download).
    4. Changes to the extracted project folder.
    5. Runs python setup.py.

.NOTES
    Run this script with administrative privileges if Python installation is required.
    The script uses winget for Python installation on Windows 10/11; if winget is not available, it falls back to downloading the official Python installer.
#>

# Stop on errors
$ErrorActionPreference = "Stop"

# Variables
$zipUrl = "https://github.com/hexo141/Wnclient/archive/refs/heads/main.zip"
$zipFile = "$env:TEMP\Wnclient-main.zip"
$extractPath = ".\"   # Extract to current directory
$projectFolder = "Wnclient-main"   # Expected folder name after extraction

# Function to write colored output
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Step 1: Download the ZIP file
Write-Info "Downloading repository from $zipUrl ..."
try {
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipFile -UseBasicParsing
    Write-Success "Download completed: $zipFile"
}
catch {
    Write-ErrorMsg "Failed to download the ZIP file. $_"
    pause
}

# Step 2: Extract the ZIP
Write-Info "Extracting $zipFile to $extractPath ..."
try {
    Expand-Archive -Path $zipFile -DestinationPath $extractPath -Force
    Write-Success "Extraction completed."
}
catch {
    Write-ErrorMsg "Failed to extract the ZIP file. $_"
    pause
}

# Step 3: Check if Python is installed
Write-Info "Checking for Python installation..."
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Info "Python not found. Installing Python..."
    try {
    Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    }
    catch {
        Write-ErrorMsg "Failed to install Chocolatey. $_"
        $fallback = $true
    }


    if ($fallback) {
        # Fallback: download Python installer from official site
        Write-Info "Downloading Python installer from python.org..."
        $pythonInstallerUrl = "https://mirrors.aliyun.com/python-release/windows/python-3.13.12-amd64.exe"   # Adjust version as needed
        $installerPath = "$env:TEMP\python-installer.exe"
        try {
            Invoke-WebRequest -Uri $pythonInstallerUrl -OutFile $installerPath -UseBasicParsing
        }
        catch {
            Write-ErrorMsg "Failed to download Python installer. $_"
            pause
        }

        Write-Info "Installing Python silently..."
        try {
            Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait -NoNewWindow
            Write-Success "Python installation completed via installer."
        }
        catch {
            Write-ErrorMsg "Python installation failed. $_"
            pause
        }
        finally {
            Remove-Item $installerPath -ErrorAction SilentlyContinue
        }
    }

    # Refresh PATH environment variable in current session
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    # Verify again
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        Write-ErrorMsg "Python still not found after installation. Please check manually."
        pause
    }
    else {
        Write-Success "Python is now available."
    }
}
else {
    Write-Success "Python is already installed at $($pythonCmd.Source)"
}

# Step 4: Navigate to the extracted project folder
$projectPath = Join-Path $extractPath $projectFolder
if (-not (Test-Path $projectPath)) {
    Write-ErrorMsg "Extracted folder '$projectFolder' not found at $extractPath"
    pause
}
Write-Info "Changing to directory: $projectPath"
Set-Location $projectPath

# Step 5: Run python setup.py
Write-Info "Running python setup.py ..."
try {
    python setup.py
    Write-Success "Setup completed successfully."
}
catch {
    Write-ErrorMsg "Failed to run python setup.py. $_"
    pause
}

Write-Success "All tasks completed."
