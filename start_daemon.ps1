# Start Reachy Mini Daemon
# Usage: .\start_daemon.ps1

Write-Host "🤖 Starting Reachy Mini Daemon" -ForegroundColor Cyan
Write-Host "=" -NoNewline; Write-Host ("=" * 59)
Write-Host ""

# Check if reachy-mini is installed
Write-Host "Checking for reachy-mini SDK..." -ForegroundColor Yellow
try {
    python -c "import reachy_mini; print('✓ reachy-mini SDK found')" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ reachy-mini SDK not found" -ForegroundColor Red
        Write-Host "   Install with: pip install reachy-mini" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Python or reachy-mini SDK not found" -ForegroundColor Red
    exit 1
}

# Check for COM port
Write-Host ""
Write-Host "Checking for Reachy Mini on COM ports..." -ForegroundColor Yellow
$ports = python -c "import serial.tools.list_ports; ports = list(serial.tools.list_ports.comports()); [print(f'{p.device}: {p.description}') for p in ports]"

if ($ports) {
    Write-Host "Available COM ports:"
    Write-Host $ports
} else {
    Write-Host "⚠️  No COM ports found" -ForegroundColor Yellow
    Write-Host "   Make sure Reachy Mini is connected via USB" -ForegroundColor Yellow
}

# Start daemon
Write-Host ""
Write-Host "Starting daemon..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Run the daemon (it will auto-detect the port)
reachy-mini-daemon
