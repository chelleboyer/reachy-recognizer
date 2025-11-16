# Setup Development Environment for Reachy Recognizer
# Usage: .\start_dev.ps1

Write-Host "🚀 Setting up Reachy Recognizer Development Environment" -ForegroundColor Cyan
Write-Host "=" -NoNewline; Write-Host ("=" * 59)
Write-Host ""

# Check Python version
Write-Host "Checking Python environment..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check for and activate virtual environment
Write-Host "Checking for virtual environment..." -ForegroundColor Yellow
if ($env:VIRTUAL_ENV) {
    Write-Host "✓ Virtual environment already active: $env:VIRTUAL_ENV" -ForegroundColor Green
} elseif (Test-Path ".venv") {
    Write-Host "Found .venv directory, activating..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1
    Write-Host "✓ Virtual environment activated: $env:VIRTUAL_ENV" -ForegroundColor Green
} elseif (Test-Path "venv") {
    Write-Host "Found venv directory, activating..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
    Write-Host "✓ Virtual environment activated: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "No virtual environment found." -ForegroundColor Yellow
    $response = Read-Host "Create one? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        python -m venv .venv
        & .\.venv\Scripts\Activate.ps1
        Write-Host "✓ Virtual environment created and activated" -ForegroundColor Green
    } else {
        Write-Host "⚠️  No virtual environment active" -ForegroundColor Yellow
        Write-Host "   Consider creating one: python -m venv .venv" -ForegroundColor Yellow
    }
}
Write-Host ""

# Set environment variables for OpenCV
Write-Host "Setting environment variables..." -ForegroundColor Yellow
$env:OPENCV_VIDEOIO_PRIORITY_MSMF = "0"
$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"
Write-Host "✓ OpenCV video backend configured" -ForegroundColor Green
Write-Host "✓ PYTHONPATH set to include project root" -ForegroundColor Green
Write-Host ""

# Check for required packages and install if missing
Write-Host "Checking required packages..." -ForegroundColor Yellow
$packages = @(
    "opencv-python",
    "numpy",
    "face-recognition",
    "pyyaml"
)

$missingPackages = @()

foreach ($package in $packages) {
    try {
        $result = python -c "import $($package.Replace('-','_'))" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ $package" -ForegroundColor Green
        } else {
            Write-Host "✗ $package (not installed)" -ForegroundColor Red
            $missingPackages += $package
        }
    } catch {
        Write-Host "✗ $package (not installed)" -ForegroundColor Red
        $missingPackages += $package
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

# Install missing packages
if ($missingPackages.Count -gt 0) {
    Write-Host "⚠️  $($missingPackages.Count) package(s) missing" -ForegroundColor Yellow
    $response = Read-Host "Install missing packages? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "Installing missing packages..." -ForegroundColor Yellow
        if (Test-Path "requirements.txt") {
            Write-Host "Installing from requirements.txt..." -ForegroundColor Yellow
            pip install -r requirements.txt
        } else {
            Write-Host "Installing individual packages..." -ForegroundColor Yellow
            foreach ($pkg in $missingPackages) {
                pip install $pkg
            }
        }
        Write-Host "✓ Package installation complete" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "⚠️  Some packages are missing. Install them manually:" -ForegroundColor Yellow
        Write-Host "   pip install $($missingPackages -join ' ')" -ForegroundColor Yellow
        Write-Host ""
    }
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
