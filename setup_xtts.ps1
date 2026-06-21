#Requires -Version 5.1
<#
.SYNOPSIS
    Installe tous les prerequis du moteur XTTS (voix neuronale naturelle) pour
    audio-report, sans toucher au Python systeme.

.DESCRIPTION
    Idempotent : on peut le relancer sans risque. Etapes :
      1. uv (gestionnaire d'environnements Python, installe via pip si absent)
      2. Python 3.11 isole (via uv)
      3. venv dedie : %USERPROFILE%\tts-bench\venv-xtts
      4. PyTorch CUDA + coqui-tts + transformers (epingle >=4.57,<5)
      5. ffmpeg (telecharge un build statique et l'ajoute au PATH si absent)

    Le modele XTTS (~1,8 Go) se telecharge tout seul au 1er usage du moteur.

.PARAMETER VenvDir
    Dossier du venv XTTS. Defaut : %USERPROFILE%\tts-bench\venv-xtts

.PARAMETER CudaIndex
    Index PyTorch CUDA. Defaut : cu124. Mettre "cpu" pour une install sans GPU
    (https://download.pytorch.org/whl/cpu).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\setup_xtts.ps1
#>
[CmdletBinding()]
param(
    [string]$VenvDir = "$env:USERPROFILE\tts-bench\venv-xtts",
    [string]$CudaIndex = "cu124"
)

$ErrorActionPreference = "Stop"

function Info($m) { Write-Host "==> $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "    $m" -ForegroundColor Green }

# --- 0) Python systeme (pour amorcer uv) --------------------------------------
$py = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $py) { throw "Python introuvable dans le PATH. Installe Python puis relance." }
Info "Python systeme : $($py.Source)"

# --- 1) uv --------------------------------------------------------------------
Info "Verification de uv..."
& python -m uv --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Info "Installation de uv (pip --user)..."
    & python -m pip install --user --quiet uv
}
Ok ("uv " + (& python -m uv --version))

# --- 2) Python 3.11 isole -----------------------------------------------------
Info "Installation de Python 3.11 (via uv, sans toucher au systeme)..."
& python -m uv python install 3.11
Ok "Python 3.11 pret."

# --- 3) venv dedie ------------------------------------------------------------
Info "Creation du venv : $VenvDir"
& python -m uv venv --python 3.11 $VenvDir
$venvPy = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $venvPy)) { throw "venv non cree : $venvPy" }
Ok $venvPy

# --- 4) PyTorch + coqui-tts ---------------------------------------------------
$torchIndex = "https://download.pytorch.org/whl/$CudaIndex"
Info "Installation de PyTorch ($CudaIndex) — gros telechargement..."
& python -m uv pip install --python $venvPy torch torchaudio --index-url $torchIndex
Info "Installation de coqui-tts + transformers (>=4.57,<5)..."
& python -m uv pip install --python $venvPy coqui-tts "transformers>=4.57,<5"
Ok "Moteur XTTS installe dans le venv."

# --- 5) ffmpeg ----------------------------------------------------------------
Info "Verification de ffmpeg..."
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Ok "ffmpeg deja present dans le PATH."
} else {
    Info "ffmpeg absent : telechargement d'un build statique..."
    $zip  = Join-Path $env:TEMP "ffmpeg.zip"
    $dest = Join-Path $env:USERPROFILE "ffmpeg"
    Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $zip
    if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
    Expand-Archive -Path $zip -DestinationPath $dest -Force
    $bin = (Get-ChildItem -Recurse -Filter ffmpeg.exe $dest | Select-Object -First 1).DirectoryName
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$bin*") {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$bin", "User")
        Ok "ffmpeg ajoute au PATH utilisateur : $bin"
        Write-Host "    (ouvre un NOUVEAU terminal pour que le PATH soit pris en compte)" -ForegroundColor Yellow
    } else { Ok "ffmpeg deja dans le PATH utilisateur." }
}

Write-Host ""
Info "Termine. Test rapide :"
Write-Host '    python generate_audio.py texts\<jour>\<sujet>.txt --engine xtts --voice "Sofia Hellen" --output audio\<jour>\<sujet>' -ForegroundColor White
if ($VenvDir -ne "$env:USERPROFILE\tts-bench\venv-xtts") {
    Write-Host "    (venv non standard : exporte XTTS_PYTHON='$venvPy' ou passe --xtts-python)" -ForegroundColor Yellow
}
