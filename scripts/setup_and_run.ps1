<#
.SYNOPSIS
  scripts\setup_and_run.ps1
  PowerShell helper for project setup, key generation, optional patch apply, tests and start.

.EXAMPLE
  # Install minimal deps, run tests, start server in foreground
  .\scripts\setup_and_run.ps1 -InstallReqs -RunTests -StartServer -Port 8000

  # Apply patches and start detached
  .\scripts\setup_and_run.ps1 -InstallReqs -ApplyPatches -StartServer -Detach -Port 8000
#>

param(
  [switch]$InstallReqs,
  [switch]$ApplyPatches,
  [switch]$RunTests,
  [switch]$StartServer,
  [switch]$Detach,
  [int]$Port = 8000
)

# Root path (one level up from script)
$ScriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
$RootDir = Join-Path $ScriptDir ".." | Resolve-Path -Relative
$RootDir = (Resolve-Path $RootDir).Path

Write-Host "Project root: $RootDir"

# 1) find python
$python = $null
foreach ($candidate in @("python3.13","python3","python")) {
  try {
    $ver = & $candidate --version 2>$null
    if ($LASTEXITCODE -eq 0) { $python = $candidate; break }
  } catch { }
}
if (-not $python) {
  Write-Error "Python not found. Install Python 3.12+ and ensure 'python' is in PATH."
  exit 1
}
Write-Host "Using Python: $($python) --version: $(& $python --version)"

# 2) venv
$venvPath = Join-Path $RootDir ".venv"
if (-not (Test-Path $venvPath)) {
  Write-Host "Creating virtualenv in $venvPath"
  & $python -m venv $venvPath
} else {
  Write-Host "Virtualenv exists."
}

# Activate venv for this PowerShell session
$activate = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activate) {
  Write-Host "Activating virtualenv..."
  . $activate
} else {
  Write-Warning "Activation script not found at $activate"
}

# 3) Install deps if requested
$reqFile = Join-Path $RootDir "requirements.txt"
if ($InstallReqs) {
  if (Test-Path $reqFile) {
    Write-Host "Installing requirements from requirements.txt..."
    pip install --upgrade pip setuptools wheel
    pip install -r $reqFile
  } else {
    Write-Host "requirements.txt not found — installing minimal dependencies..."
    pip install --upgrade pip setuptools wheel
    pip install fastapi "uvicorn[standard]" python-multipart pyyaml numpy requests
  }
}

# 4) .env and key generation
$envFile = Join-Path $RootDir ".env"
if (-not (Test-Path $envFile)) {
  Write-Host "Generating MIND_API_KEY and writing to .env..."
  $key = & $python -c "import secrets;print(secrets.token_urlsafe(48))"
  $envContent = @"
# Auto-generated .env
MIND_API_KEY=$key
"@
  $envContent | Out-File -FilePath $envFile -Encoding utf8
  Write-Host ".env written (do not commit to VCS)"
} else {
  Write-Host ".env already exists. Using existing key."
}

# load .env into session
Get-Content $envFile | ForEach-Object {
  if ($_ -match '^\s*([^#][^=]+)=(.+)$') {
    $name = $matches[1].Trim()
    $val  = $matches[2].Trim()
    Set-Item -Path "Env:\$name" -Value $val
  }
}

if (-not $Env:MIND_API_KEY) {
  Write-Error "MIND_API_KEY not set after reading .env"
  exit 1
}
Write-Host "MIND_API_KEY loaded for this session (hidden)."

# 5) Apply patches: look for patches\*.patch under project root
if ($ApplyPatches) {
  $patchDir = Join-Path $RootDir "patches"
  if (Test-Path $patchDir) {
    $patchFiles = Get-ChildItem -Path $patchDir -Filter *.patch -File -ErrorAction SilentlyContinue
    if ($patchFiles.Count -gt 0) {
      foreach ($pf in $patchFiles) {
        Write-Host "Applying patch: $($pf.FullName)"
        # Try git apply first (requires git)
        if (Get-Command git -ErrorAction SilentlyContinue) {
          git apply $pf.FullName
        } elseif (Get-Command patch -ErrorAction SilentlyContinue) {
          patch -p0 < $pf.FullName
        } else {
          Write-Error "Neither git nor patch available to apply $($pf.Name). Skipping."
        }
      }
    } else {
      Write-Host "No .patch files in $patchDir"
    }
  } else {
    Write-Host "No patches directory found at $patchDir"
  }
}

# 6) Syntax check
Write-Host "Running compileall..."
& $python -m compileall -q $RootDir

# 7) Tests
if ($RunTests) {
  Write-Host "Running unit tests..."
  & $python -m unittest discover -s (Join-Path $RootDir "tests") -v
}

# 8) Start server
if ($StartServer) {
  $startCmd = "$python src\main.py --start-rest --api-port $Port"
  if ($Detach) {
    Write-Host "Starting server detached..."
    $log = Join-Path $RootDir "logs\server.out"
    New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
    Start-Process -FilePath $python -ArgumentList "src\main.py","--start-rest","--api-port",$Port -WindowStyle Hidden -RedirectStandardOutput $log -RedirectStandardError $log
    Write-Host "Server started in background, log -> $log"
  } else {
    Write-Host "Starting server in foreground..."
    & $python src\main.py --start-rest --api-port $Port
  }
} else {
  Write-Host "Setup complete. To start server run (PowerShell):"
  Write-Host "  \$env:MIND_API_KEY = '...'; python src\main.py --start-rest --api-port $Port"
}
