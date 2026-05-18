# ============================================================
# Waze Ingest - Server Bootstrap Script
# Run this in PowerShell AS ADMINISTRATOR on KCPSSQLPROD
# ============================================================

# Step 1 - Check if Python is already installed somewhere
Write-Host "Searching for Python on this machine..." -ForegroundColor Cyan
$pythonPaths = @(
    "C:\Python3\python.exe",
    "C:\Python311\python.exe",
    "C:\Python312\python.exe",
    "C:\Python313\python.exe",
    "C:\Python314\python.exe",
    "C:\Python310\python.exe",
    "C:\Program Files\Python311\python.exe",
    "C:\Program Files\Python312\python.exe",
    "C:\Program Files\Python313\python.exe",
    "C:\Program Files\Python314\python.exe",
    "C:\Users\nwssvc\AppData\Local\Programs\Python\Python311\python.exe",
    "C:\Users\nwssvc\AppData\Local\Programs\Python\Python312\python.exe",
    "C:\Users\nwssvc\AppData\Local\Programs\Python\Python313\python.exe",
    "C:\Users\nwssvc\AppData\Local\Programs\Python\Python314\python.exe"
)

$found = $null
foreach ($p in $pythonPaths) {
    if (Test-Path $p) {
        Write-Host "  Found: $p" -ForegroundColor Green
        $found = $p
        break
    }
}

if (-not $found) {
    # Try locating via where.exe
    $whereResult = where.exe python 2>$null
    if ($whereResult) {
        $found = $whereResult | Select-Object -First 1
        Write-Host "  Found via PATH: $found" -ForegroundColor Green
    }
}

if ($found) {
    Write-Host ""
    Write-Host "Python found at: $found" -ForegroundColor Green
    & $found --version

    # Install dependencies
    Write-Host ""
    Write-Host "Installing required packages..." -ForegroundColor Cyan
    & $found -m pip install --upgrade pip
    & $found -m pip install pyodbc requests pywin32

    # Run pywin32 post-install
    Write-Host ""
    Write-Host "Running pywin32 post-install script..." -ForegroundColor Cyan
    & $found -c "import sys; sys.path.insert(0, ''); exec(open(sys.prefix + '/Scripts/pywin32_postinstall.py').read())" 2>$null

    Write-Host ""
    Write-Host "All dependencies installed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next step: Copy the ingest folder to this server and run:" -ForegroundColor Yellow
    Write-Host "  & '$found' C:\WazeIngest\install_service.py install" -ForegroundColor Yellow
    Write-Host "  & '$found' C:\WazeIngest\install_service.py start" -ForegroundColor Yellow

} else {
    Write-Host ""
    Write-Host "Python NOT found. Downloading Python 3.11 installer..." -ForegroundColor Yellow

    $installer = "$env:TEMP\python-3.11.9-amd64.exe"
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile $installer

    Write-Host "Installing Python 3.11 (all users, add to PATH)..." -ForegroundColor Cyan
    Start-Process -FilePath $installer -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait

    Write-Host "Python installed! Please CLOSE and REOPEN PowerShell as Admin, then re-run this script." -ForegroundColor Green
}
