# Setup Development Environment for Reachy Recognizer
# Usage: .\start_dev.ps1

Write-Host "🚀 Setting up Reachy Recognizer Development Environment" -ForegroundColor Cyan
Write-Host "=" -NoNewline; Write-Host ("=" * 59)
Write-Host ""

# Set environment variables for OpenCV
Write-Host "Setting environment variables..." -ForegroundColor Yellow
$env:OPENCV_VIDEOIO_PRIORITY_MSMF = "0"
$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"
Write-Host "✓ OpenCV video backend configured" -ForegroundColor Green
Write-Host "✓ PYTHONPATH set to include project root" -ForegroundColor Green
Write-Host ""

# Check Python version
Write-Host "Checking Python environment..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "✓ $pythonVersion" -ForegroundColor Green

# Check if virtual environment is active
if ($env:VIRTUAL_ENV) {
    Write-Host "✓ Virtual environment active: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "⚠️  No virtual environment active" -ForegroundColor Yellow
    Write-Host "   Consider activating one for isolation" -ForegroundColor Yellow
}
Write-Host ""

# Check for required packages
Write-Host "Checking required packages..." -ForegroundColor Yellow
$packages = @(
    "opencv-python",
    "numpy",
    "face-recognition",
    "pyyaml"
)

foreach ($package in $packages) {
    try {
        $result = python -c "import $($package.Replace('-','_')); print('installed')" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ $package" -ForegroundColor Green
        } else {
            Write-Host "✗ $package (not installed)" -ForegroundColor Red
        }
    } catch {
        Write-Host "✗ $package (not installed)" -ForegroundColor Red
    }
}
Write-Host ""

# Check for Reachy SDK (optional)
Write-Host "Checking optional packages..." -ForegroundColor Yellow
try {
    python -c "import reachy_mini" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ reachy-mini (for robot control)" -ForegroundColor Green
    } else {
        Write-Host "○ reachy-mini (optional - for robot control)" -ForegroundColor Gray
    }
} catch {
    Write-Host "○ reachy-mini (optional - for robot control)" -ForegroundColor Gray
}
Write-Host ""

# Show available commands
Write-Host "Available commands:" -ForegroundColor Cyan
Write-Host "  python main.py                    - Run main recognition system" -ForegroundColor White
Write-Host "  python demo.py                    - Run demo with Reachy robot" -ForegroundColor White
Write-Host "  python add_face.py 'Name'         - Add face to database (webcam)" -ForegroundColor White
Write-Host "  python add_face.py 'Name' --reachy - Add face to database (Reachy camera)" -ForegroundColor White
Write-Host "  python integrated_demo.py         - Run integrated demo" -ForegroundColor White
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Edit: src/config/config.yaml" -ForegroundColor White
Write-Host "  Enable robot: Set 'enable_robot: true' in config.yaml" -ForegroundColor White
Write-Host ""
Write-Host "✨ Environment ready! Happy coding!" -ForegroundColor Green
Write-Host ""
