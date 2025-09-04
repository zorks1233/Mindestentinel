\
    # create_venv_and_zip.ps1
    # Usage: .\create_venv_and_zip.ps1 -ProjectPath "C:\path\to\project" [-WithReqs]
    param(
      [string]$ProjectPath = ".",
      [switch]$WithReqs = $false
    )
    Push-Location $ProjectPath
    $python = "python3.13"
    if (-not (Get-Command $python -ErrorAction SilentlyContinue)) {
      foreach ($p in @("python3","python")) {
        if (Get-Command $p -ErrorAction SilentlyContinue) { $python = $p; break }
      }
    }
    Write-Host "Using $python"
    & $python -m venv .venv
    . .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip setuptools wheel
    if ($WithReqs -and (Test-Path requirements.txt)) {
      pip install -r requirements.txt
    }
    Deactivate
    $zipName = (Split-Path -Leaf (Get-Location)) + "-with-venv.zip"
    Write-Host "Creating zip $zipName (this may be large)"
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory((Get-Location).Path, (Join-Path (Get-Location).Parent.FullName $zipName))
    Pop-Location
    Write-Host "Done. Zip created in parent folder."
