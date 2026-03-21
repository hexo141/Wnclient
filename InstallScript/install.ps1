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

# Function to check if Python is truly installed (not the Microsoft Store placeholder)
function Test-RealPython {
    param([string]$pythonPath)
    
    # Check if it's the Microsoft Store placeholder
    if ($pythonPath -like "*WindowsApps*") {
        # Try to get real Python by checking multiple possible locations
        $realPythonPaths = @(
            "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
            "$env:ProgramFiles\Python313\python.exe",
            "$env:ProgramFiles\Python312\python.exe",
            "$env:ProgramFiles\Python311\python.exe",
            "$env:ProgramFiles\Python310\python.exe"
        )
        
        foreach ($path in $realPythonPaths) {
            if (Test-Path $path) {
                return $path
            }
        }
        return $null
    }
    
    # Check if it's a real Python executable
    try {
        $version = & $pythonPath --version 2>$null
        if ($version -match "Python") {
            return $pythonPath
        }
    }
    catch {
        return $null
    }
    return $null
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
    exit 1
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
    exit 1
}

# Step 3: Check if Python is installed
Write-Info "Checking for Python installation..."
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
$realPythonPath = $null

if ($pythonCmd) {
    $realPythonPath = Test-RealPython -pythonPath $pythonCmd.Source
    if ($realPythonPath) {
        Write-Success "Python is already installed at $realPythonPath"
        # Update pythonCmd to point to real Python
        $pythonCmd = Get-Command $realPythonPath -ErrorAction SilentlyContinue
    }
    else {
        Write-Info "Found Microsoft Store Python placeholder at $($pythonCmd.Source). Will install real Python..."
        $pythonCmd = $null
    }
}

if (-not $pythonCmd) {
    Write-Info "Python not found or only Microsoft Store placeholder exists. Installing Python..."
    
    # Try to install Python using winget first
    $wingetInstalled = $false
    try {
        $wingetPath = Get-Command winget -ErrorAction SilentlyContinue
        if ($wingetPath) {
            Write-Info "Installing Python using winget..."
            winget install Python.Python.3.13 --silent --accept-package-agreements
            $wingetInstalled = $true
        }
    }
    catch {
        Write-Info "winget installation failed or not available."
    }
    
    # If winget failed or not available, use direct download
    if (-not $wingetInstalled) {
        # Download Python installer from official site
        Write-Info "Downloading Python installer from mirrors.aliyun.com..."
        $pythonInstallerUrl = "https://mirrors.aliyun.com/python-release/windows/python-3.13.12-amd64.exe"
        $installerPath = "$env:TEMP\python-installer.exe"
        try {
            Invoke-WebRequest -Uri $pythonInstallerUrl -OutFile $installerPath -UseBasicParsing
            Write-Info "Installing Python silently..."
            Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait -NoNewWindow
            Write-Success "Python installation completed via installer."
        }
        catch {
            Write-ErrorMsg "Failed to download or install Python. $_"
            pause
            exit 1
        }
        finally {
            Remove-Item $installerPath -ErrorAction SilentlyContinue
        }
    }
    
    # Refresh PATH environment variable in current session
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    # Wait a moment for the system to register the new installation
    Start-Sleep -Seconds 2
    
    # Verify Python installation by checking actual installation paths
    $possiblePaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:ProgramFiles\Python313\python.exe",
        "$env:ProgramFiles\Python312\python.exe"
    )
    
    $foundPython = $false
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $realPythonPath = $path
            $foundPython = $true
            break
        }
    }
    
    # Also try getting from PATH again
    if (-not $foundPython) {
        $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
        if ($pythonCmd) {
            $realPythonPath = Test-RealPython -pythonPath $pythonCmd.Source
            if ($realPythonPath) {
                $foundPython = $true
            }
        }
    }
    
    if (-not $foundPython) {
        Write-ErrorMsg "Python still not found after installation. Please check manually."
        pause
        exit 1
    }
    else {
        Write-Success "Python is now available at $realPythonPath"
        $pythonCmd = Get-Command $realPythonPath -ErrorAction SilentlyContinue
    }
}

# Step 4: Navigate to the extracted project folder
$projectPath = Join-Path $extractPath $projectFolder
if (-not (Test-Path $projectPath)) {
    Write-ErrorMsg "Extracted folder '$projectFolder' not found at $extractPath"
    pause
    exit 1
}
Write-Info "Changing to directory: $projectPath"
Set-Location $projectPath

# Step 5: Run python setup.py
Write-Info "Running python setup.py ..."
try {
    # Use the actual Python executable path to avoid any PATH issues
    if ($realPythonPath) {
        & $realPythonPath setup.py
    }
    else {
        python setup.py
        Set-Location $projectPath + "\InstallScript"
        python gen_path.py
    }
    Write-Success "Setup completed successfully."
}
catch {
    Write-ErrorMsg "Failed to run python setup.py. $_"
    pause
    exit 1
}

Write-Success "All tasks completed.You can now run the program using 'python main.py'"