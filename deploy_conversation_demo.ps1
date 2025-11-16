# Deploy Conversation Demo to Raspberry Pi
# Usage: .\deploy_conversation_demo.ps1 <pi-ip-address>

param(
    [Parameter(Mandatory=$true)]
    [string]$PiHost,
    [string]$PiUser = "pi",
    [string]$TargetDir = "/home/pi/reachy-mini-dev"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deploying Conversation Demo to Pi5   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$RemoteConnection = "${PiUser}@${PiHost}"

# Check if we can reach the Pi
Write-Host "[1/7] Testing connection to ${RemoteConnection}..." -ForegroundColor Yellow
$pingResult = Test-Connection -ComputerName $PiHost -Count 1 -Quiet
if (-not $pingResult) {
    Write-Host "✗ Cannot reach ${PiHost}" -ForegroundColor Red
    Write-Host "   Make sure the Pi is on and connected to the network" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Connection successful" -ForegroundColor Green
Write-Host ""

# Files to deploy
Write-Host "[2/7] Preparing files for deployment..." -ForegroundColor Yellow
$filesToDeploy = @(
    "conversation_demo.py",
    "requirements.txt",
    ".env",
    "src/",
    "models/vosk-model-small-en-us-0.15/"
)

# Check if files exist
$missingFiles = @()
foreach ($file in $filesToDeploy) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "✗ Missing required files:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "   - $file" -ForegroundColor Red
    }
    exit 1
}
Write-Host "✓ All required files present" -ForegroundColor Green
Write-Host ""

# Create target directory on Pi
Write-Host "[3/7] Creating target directory on Pi..." -ForegroundColor Yellow
ssh ${RemoteConnection} "mkdir -p ${TargetDir}"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to create directory on Pi" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Target directory ready" -ForegroundColor Green
Write-Host ""

# Deploy conversation_demo.py
Write-Host "[4/7] Deploying conversation_demo.py..." -ForegroundColor Yellow
scp conversation_demo.py "${RemoteConnection}:${TargetDir}/"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to deploy conversation_demo.py" -ForegroundColor Red
    exit 1
}
Write-Host "✓ conversation_demo.py deployed" -ForegroundColor Green
Write-Host ""

# Deploy requirements.txt and .env
Write-Host "[5/7] Deploying configuration files..." -ForegroundColor Yellow
scp requirements.txt "${RemoteConnection}:${TargetDir}/"
scp .env "${RemoteConnection}:${TargetDir}/"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to deploy config files" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Configuration files deployed" -ForegroundColor Green
Write-Host ""

# Deploy src directory
Write-Host "[6/7] Deploying source code..." -ForegroundColor Yellow
scp -r src "${RemoteConnection}:${TargetDir}/"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to deploy src directory" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Source code deployed" -ForegroundColor Green
Write-Host ""

# Deploy Vosk model
Write-Host "[7/7] Deploying Vosk model..." -ForegroundColor Yellow
Write-Host "   This may take a few minutes (~40MB)..." -ForegroundColor Gray
ssh ${RemoteConnection} "mkdir -p ${TargetDir}/models"
scp -r models/vosk-model-small-en-us-0.15 "${RemoteConnection}:${TargetDir}/models/"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to deploy Vosk model" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Vosk model deployed" -ForegroundColor Green
Write-Host ""

# Install dependencies on Pi
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installing Dependencies on Pi        " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$installScript = @"
cd ${TargetDir}
echo "Installing Python packages..."
pip install --quiet vosk pyaudio openai python-dotenv mediapipe 2>&1 | grep -v 'Requirement already satisfied' || true
echo "✓ Dependencies installed"
"@

ssh ${RemoteConnection} $installScript

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Some dependencies may have failed to install" -ForegroundColor Yellow
    Write-Host "   You may need to install them manually on the Pi" -ForegroundColor Yellow
} else {
    Write-Host "✓ All dependencies installed" -ForegroundColor Green
}
Write-Host ""

# Test script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete!                  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run the conversation demo on your Pi:" -ForegroundColor Green
Write-Host ""
Write-Host "  1. SSH to your Pi:" -ForegroundColor White
Write-Host "     ssh ${RemoteConnection}" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Navigate to the project:" -ForegroundColor White
Write-Host "     cd ${TargetDir}" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Run the demo:" -ForegroundColor White
Write-Host "     python conversation_demo.py --reachy" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Or run headless (recommended for SSH):" -ForegroundColor White
Write-Host "     python conversation_demo.py --reachy --headless" -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to open SSH session to Pi..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Open SSH session
ssh ${RemoteConnection}
