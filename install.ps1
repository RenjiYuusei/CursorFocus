# CursorFocus Installation Script
# Author: RenjiYuusei
# Description: This script installs CursorFocus Fast in the Downloads folder

# Set error action preference
$ErrorActionPreference = "Stop"

# Define installation path
$installPath = "$env:USERPROFILE\Downloads\CursorFocus"

# Create function to show status messages
function Write-Status {
    param($Message)
    Write-Host "==> $Message" -ForegroundColor Cyan
}

# Check if Python is installed and version is compatible
Write-Status "Checking Python installation..."
try {
    $pythonVersion = python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
    $versionParts = $pythonVersion.Split('.')
    $major = [int]$versionParts[0]
    $minor = [int]$versionParts[1]
    
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
        Write-Host "Python version $pythonVersion detected. CursorFocus requires Python 3.10 or later." -ForegroundColor Red
        Write-Host "Please install a compatible Python version from https://www.python.org/downloads/" -ForegroundColor Red
        exit 1
    }
    Write-Host "Found compatible Python $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python is not installed. Please install Python 3.10 or later from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# Create installation directory if it doesn't exist
Write-Status "Creating installation directory..."
if (Test-Path $installPath) {
    Write-Host "Directory already exists. Cleaning up..." -ForegroundColor Yellow
    Remove-Item -Path $installPath -Recurse -Force
}
New-Item -ItemType Directory -Path $installPath | Out-Null

# Download and extract ZIP file
Write-Status "Downloading CursorFocus..."
$zipUrl = "https://github.com/RenjiYuusei/CursorFocus/archive/refs/heads/main.zip"
$zipPath = Join-Path $installPath "cursorfocus.zip"

# Test internet connection
try {
    $testConnection = Invoke-WebRequest -Uri "https://github.com" -UseBasicParsing -TimeoutSec 10
    Write-Host "Internet connection verified" -ForegroundColor Green
} catch {
    Write-Host "Unable to connect to internet. Please check your connection and try again." -ForegroundColor Red
    exit 1
}

# Download with retry logic
$maxRetries = 3
$retryCount = 0
$downloadSuccess = $false

while (-not $downloadSuccess -and $retryCount -lt $maxRetries) {
    try {
        Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath
        $downloadSuccess = $true
        Write-Host "Downloaded ZIP file successfully" -ForegroundColor Green
    } catch {
        $retryCount++
        if ($retryCount -lt $maxRetries) {
            Write-Host "Download failed, attempt $retryCount of $maxRetries. Retrying..." -ForegroundColor Yellow
            Start-Sleep -Seconds 2
        } else {
            Write-Host "Failed to download after $maxRetries attempts. Error: $_" -ForegroundColor Red
            exit 1
        }
    }
}

Write-Status "Extracting files..."
Expand-Archive -Path $zipPath -DestinationPath $installPath
Move-Item -Path "$installPath\CursorFocus-main\*" -Destination $installPath
Remove-Item -Path "$installPath\CursorFocus-main" -Recurse
Remove-Item -Path $zipPath
Write-Host "Extracted files successfully" -ForegroundColor Green

# Get Gemini API key from user
Write-Status "Setting up Gemini API..."
Write-Host "Please enter your Gemini API key (get one from https://makersuite.google.com/app/apikey):" -ForegroundColor Yellow

do {
    $apiKey = Read-Host
    
    # Validate API key format (basic check for AIzaSy prefix)
    if (-not $apiKey.StartsWith("AIzaSy")) {
        Write-Host "Invalid API key format. API key should start with 'AIzaSy'." -ForegroundColor Red
        Write-Host "Please enter a valid API key:" -ForegroundColor Yellow
        continue
    }

    # Test API key
    Write-Host "Validating API key..." -ForegroundColor Yellow
    try {
        $headers = @{
            'x-goog-api-key' = $apiKey
        }
        $response = Invoke-WebRequest -Uri "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp" -Headers $headers -Method GET
        if ($response.StatusCode -eq 200) {
            Write-Host "API key validated successfully!" -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "Invalid or expired API key. Please check your key and try again." -ForegroundColor Red
        Write-Host "Please enter a valid API key:" -ForegroundColor Yellow
    }
} while ($true)

# Create .env file with user's API key
Write-Status "Creating .env file..."
$envContent = @"
GEMINI_API_KEY=$apiKey
"@
Set-Content -Path (Join-Path $installPath ".env") -Value $envContent -NoNewline
Write-Host "Created .env file with your API key" -ForegroundColor Green

# Install required packages
Write-Status "Installing required packages..."
Set-Location $installPath
python -m pip install -r requirements.txt

Write-Status "Installation completed successfully!"
Write-Host @"

CursorFocus has been installed to: $installPath

To start using CursorFocus:
1. Navigate to the installation directory:
   cd "$installPath"

2. Run the setup script:
   python setup.py --p <path to project folder>

For more information, please visit:
https://github.com/RenjiYuusei/CursorFocus
"@ -ForegroundColor Green

# Ask user if they want to open the installation folder
Write-Host "`nWould you like to open the CursorFocus folder? (Y/N)" -ForegroundColor Yellow
$openFolder = Read-Host
if ($openFolder -eq 'Y' -or $openFolder -eq 'y') {
    Start-Process explorer.exe -ArgumentList $installPath
}