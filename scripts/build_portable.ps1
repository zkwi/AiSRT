param(
    [string]$Version = "",
    [string]$Python = ".\.venv\Scripts\python.exe",
    [switch]$InstallDeps,
    [switch]$SkipTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$PythonPath = if ([System.IO.Path]::IsPathRooted($Python)) { $Python } else { Join-Path $RepoRoot $Python }
$PythonPath = (Resolve-Path -LiteralPath $PythonPath).Path
$BuildDir = Join-Path $RepoRoot "build\portable"
$ReleaseDir = Join-Path $RepoRoot "dist\release"
$PackageName = "AiSRT-v$Version-windows-portable"
$PackageDir = Join-Path $BuildDir $PackageName

function Get-ProjectVersion {
    $Pyproject = Get-Content -LiteralPath (Join-Path $RepoRoot "pyproject.toml") -Raw
    if ($Pyproject -notmatch '(?m)^version\s*=\s*"([^"]+)"') {
        throw "Cannot read project version from pyproject.toml."
    }
    return $Matches[1]
}

function Assert-InRepo {
    param([string]$Path)
    $FullPath = [System.IO.Path]::GetFullPath($Path)
    $RootPath = [System.IO.Path]::GetFullPath($RepoRoot)
    if (-not $FullPath.StartsWith($RootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to operate outside repository: $FullPath"
    }
    return $FullPath
}

function Remove-PathInRepo {
    param([string]$Path)
    $FullPath = Assert-InRepo $Path
    if (Test-Path -LiteralPath $FullPath) {
        Remove-Item -LiteralPath $FullPath -Recurse -Force
    }
}

function Invoke-Native {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

function Get-RelativePathCompat {
    param(
        [string]$BasePath,
        [string]$FullPath
    )
    $BaseFullPath = [System.IO.Path]::GetFullPath($BasePath)
    if (-not $BaseFullPath.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
        $BaseFullPath = $BaseFullPath + [System.IO.Path]::DirectorySeparatorChar
    }
    $TargetFullPath = [System.IO.Path]::GetFullPath($FullPath)
    $BaseUri = [System.Uri]::new($BaseFullPath)
    $TargetUri = [System.Uri]::new($TargetFullPath)
    $RelativeUri = $BaseUri.MakeRelativeUri($TargetUri)
    return [System.Uri]::UnescapeDataString($RelativeUri.ToString()).Replace("/", [System.IO.Path]::DirectorySeparatorChar)
}

function Copy-ProjectItem {
    param([string]$RelativePath)
    $Source = Join-Path $RepoRoot $RelativePath
    $Destination = Join-Path $PackageDir $RelativePath
    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Missing package source: $RelativePath"
    }
    $SourceItem = Get-Item -LiteralPath $Source
    if ($SourceItem.PSIsContainer) {
        Copy-Item -LiteralPath $Source -Destination $PackageDir -Recurse -Force
    } else {
        $Parent = Split-Path -Parent $Destination
        if ($Parent) {
            New-Item -ItemType Directory -Path $Parent -Force | Out-Null
        }
        Copy-Item -LiteralPath $Source -Destination $Destination -Force
    }
}

function Write-PortableScripts {
    $InstallScript = @'
@echo off
setlocal EnableExtensions

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        py -3.11 -m venv .venv
        if %ERRORLEVEL% NEQ 0 py -3 -m venv .venv
    ) else (
        python -m venv .venv
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python 3.10+ was not found. Install Python first, then run this script again.
    pause
    exit /b 1
)

set "PYTHONIOENCODING=utf-8"
set "HF_HOME=%PROJECT_DIR%.hf_cache"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
set "TRANSFORMERS_CACHE="

".venv\Scripts\python.exe" -m pip install -U pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
".venv\Scripts\python.exe" -m aisrt doctor

echo.
echo [OK] AISRT runtime dependencies are installed.
pause
'@

    $StartScript = @'
@echo off
setlocal EnableExtensions

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

if not exist ".venv\Scripts\pythonw.exe" (
    call "%PROJECT_DIR%install_runtime.bat"
    if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
)

set "PYTHONIOENCODING=utf-8"
set "HF_HOME=%PROJECT_DIR%.hf_cache"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
set "TRANSFORMERS_CACHE="

start "" "%PROJECT_DIR%.venv\Scripts\pythonw.exe" -m aisrt.gui
endlocal
'@

    $ShellScript = @'
@echo off
setlocal EnableExtensions

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

if not exist ".venv\Scripts\activate.bat" (
    call "%PROJECT_DIR%install_runtime.bat"
    if %ERRORLEVEL% NEQ 0 exit /b %ERRORLEVEL%
)

set "PYTHONIOENCODING=utf-8"
set "HF_HOME=%PROJECT_DIR%.hf_cache"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
set "TRANSFORMERS_CACHE="

call "%PROJECT_DIR%.venv\Scripts\activate.bat"
cmd /k
'@

    Set-Content -LiteralPath (Join-Path $PackageDir "install_runtime.bat") -Value $InstallScript -Encoding ASCII
    Set-Content -LiteralPath (Join-Path $PackageDir "start_gui.bat") -Value $StartScript -Encoding ASCII
    Set-Content -LiteralPath (Join-Path $PackageDir "open_shell.bat") -Value $ShellScript -Encoding ASCII
}

function Write-PortableReadme {
    $Text = @"
AISRT Windows Portable
======================

This package is intentionally lightweight. It does not bundle Python, PyTorch,
CUDA libraries, model weights, model caches, FFmpeg, media files, subtitles,
screenshots, tests, logs, or any generated runtime environment.

Quick start:

1. Install Python 3.10 or newer. Python 3.11 is recommended.
2. Install FFmpeg and make sure ffmpeg and ffprobe are available in PATH.
3. Run install_runtime.bat once to create .venv and install Python dependencies.
4. Run start_gui.bat to open the GUI.

Notes:

- Python dependencies are installed into this package's local .venv directory.
- Model weights are downloaded by AISRT on first use when remote model IDs are used.
- The local .venv, .hf_cache, generated subtitles and logs are runtime artifacts.
  Do not publish them if you redistribute this folder.
"@
    Set-Content -LiteralPath (Join-Path $PackageDir "README_PORTABLE.txt") -Value $Text -Encoding UTF8
}

function Remove-PackageRuntimeArtifacts {
    param([string]$Path)
    Get-ChildItem -LiteralPath $Path -Recurse -Force -Directory | Where-Object {
        $_.Name -in @("__pycache__", ".pytest_cache")
    } | ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Recurse -Force
    }
    Get-ChildItem -LiteralPath $Path -Recurse -Force -File | Where-Object {
        $_.Extension.ToLowerInvariant() -in @(".pyc", ".pyo")
    } | ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Force
    }
}

function Assert-NoForbiddenPayload {
    param([string]$Path)
    $ForbiddenDirs = @(".venv", ".hf_cache", "hf_cache", "models", "video", "videos", "media", "samples", "screenshots", "logs", "log", "build", "dist", "__pycache__", ".pytest_cache")
    $ForbiddenExtensions = @(".dll", ".pyd", ".exe", ".safetensors", ".pt", ".pth", ".onnx", ".ckpt", ".mp4", ".mkv", ".mov", ".avi", ".m4v", ".webm", ".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".srt", ".vtt", ".ass", ".ssa", ".log")

    $Matches = Get-ChildItem -LiteralPath $Path -Recurse -Force | Where-Object {
        $RelativePath = Get-RelativePathCompat $Path $_.FullName
        $Parts = $RelativePath -split '[\\/]'
        $HasForbiddenDir = @($Parts | Where-Object { $ForbiddenDirs -contains $_ }).Count -gt 0
        $HasForbiddenDir -or
        ((-not $_.PSIsContainer) -and $ForbiddenExtensions -contains $_.Extension.ToLowerInvariant())
    } | Select-Object -First 20

    if ($Matches) {
        $Names = ($Matches | ForEach-Object { $_.FullName }) -join [Environment]::NewLine
        throw "Portable package contains forbidden runtime, model, log or media artifacts:$([Environment]::NewLine)$Names"
    }
}

function Assert-NoPrivateText {
    param([string]$Path)
    $Patterns = @(
        ("[A-Za-z]:\\Us" + "ers\\[^\\\s]+"),
        ("/Us" + "ers/[^/\s]+"),
        ("/ho" + "me/[^/\s]+"),
        "\bgh[pousr]_[A-Za-z0-9_]{20,}\b",
        "\bhf_[A-Za-z0-9]{20,}\b",
        "\bsk-[A-Za-z0-9_-]{20,}\b"
    )
    $TextExtensions = @(".bat", ".md", ".ps1", ".py", ".toml", ".txt", ".yml", ".yaml")

    foreach ($File in Get-ChildItem -LiteralPath $Path -Recurse -File) {
        if ($TextExtensions -notcontains $File.Extension.ToLowerInvariant()) {
            continue
        }
        $Text = Get-Content -LiteralPath $File.FullName -Raw -Encoding UTF8
        foreach ($Pattern in $Patterns) {
            if ($Text -match $Pattern) {
                throw "Portable text contains private data pattern '$Pattern': $($File.FullName)"
            }
        }
    }
}

function Assert-PortableRequiredFiles {
    param([string]$Path)
    $RequiredFiles = @(
        "aisrt\cli.py",
        "aisrt\assets\app.svg",
        "docs\README.md",
        "install_runtime.bat",
        "start_gui.bat",
        "open_shell.bat",
        "README_PORTABLE.txt",
        "README.md",
        "SUPPORT.md",
        "LICENSE",
        "pyproject.toml",
        "requirements.txt",
        "requirements-torch-cu130.txt"
    )
    $Missing = foreach ($File in $RequiredFiles) {
        if (-not (Test-Path -LiteralPath (Join-Path $Path $File) -PathType Leaf)) {
            $File
        }
    }
    $Missing = @($Missing)
    if ($Missing.Count -gt 0) {
        throw "Portable package is missing required files:$([Environment]::NewLine)$($Missing -join [Environment]::NewLine)"
    }
}

function Compress-PortableArchive {
    param(
        [string]$SourceDir,
        [string]$DestinationPath
    )
    $SevenZip = Get-Command 7z -ErrorAction SilentlyContinue
    if (-not $SevenZip) {
        $SevenZip = Get-Command 7za -ErrorAction SilentlyContinue
    }

    if ($SevenZip) {
        Push-Location (Split-Path -Parent $SourceDir)
        try {
            Invoke-Native $SevenZip.Source @("a", "-tzip", "-mx=9", $DestinationPath, ".\$(Split-Path -Leaf $SourceDir)")
        } finally {
            Pop-Location
        }
    } else {
        Compress-Archive -LiteralPath $SourceDir -DestinationPath $DestinationPath -CompressionLevel Optimal -Force
    }
}

function Assert-ZipRequiredFiles {
    param([string]$ZipPath)
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $PackageRoot = [System.IO.Path]::GetFileNameWithoutExtension($ZipPath)
    $RequiredEntries = @(
        "aisrt/cli.py",
        "aisrt/assets/app.svg",
        "docs/README.md",
        "install_runtime.bat",
        "start_gui.bat",
        "open_shell.bat",
        "README_PORTABLE.txt",
        "README.md",
        "SUPPORT.md",
        "LICENSE",
        "pyproject.toml",
        "requirements.txt",
        "requirements-torch-cu130.txt"
    )

    $Zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
    try {
        $Entries = @($Zip.Entries | ForEach-Object { $_.FullName.TrimEnd("/") })
        $Missing = foreach ($Entry in $RequiredEntries) {
            $Expected = "$PackageRoot/$Entry"
            if ($Entries -notcontains $Expected) {
                $Entry
            }
        }
        $Missing = @($Missing)
        if ($Missing.Count -gt 0) {
            throw "ZIP is missing required files:$([Environment]::NewLine)$($Missing -join [Environment]::NewLine)"
        }
    } finally {
        $Zip.Dispose()
    }
}

function Assert-ZipNoForbiddenPayload {
    param([string]$ZipPath)
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $ForbiddenDirs = @(".venv", ".hf_cache", "hf_cache", "models", "video", "videos", "media", "samples", "screenshots", "logs", "log", "build", "dist", "__pycache__", ".pytest_cache")
    $ForbiddenExtensions = @(".dll", ".pyd", ".exe", ".safetensors", ".pt", ".pth", ".onnx", ".ckpt", ".mp4", ".mkv", ".mov", ".avi", ".m4v", ".webm", ".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".srt", ".vtt", ".ass", ".ssa", ".log")

    $Zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
    try {
        $Matches = foreach ($Entry in $Zip.Entries) {
            $Parts = $Entry.FullName -split "/"
            $HasForbiddenDir = @($Parts | Where-Object { $ForbiddenDirs -contains $_ }).Count -gt 0
            $Extension = [System.IO.Path]::GetExtension($Entry.FullName).ToLowerInvariant()
            if ($HasForbiddenDir -or $ForbiddenExtensions -contains $Extension) {
                $Entry.FullName
            }
        }
        $Matches = @($Matches | Select-Object -First 20)
        if ($Matches.Count -gt 0) {
            $Names = $Matches -join [Environment]::NewLine
            throw "ZIP contains forbidden runtime, model, log or media artifacts:$([Environment]::NewLine)$Names"
        }
    } finally {
        $Zip.Dispose()
    }
}

$ProjectVersion = Get-ProjectVersion
if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = $ProjectVersion
    $PackageName = "AiSRT-v$Version-windows-portable"
    $PackageDir = Join-Path $BuildDir $PackageName
} elseif ($Version -ne $ProjectVersion) {
    throw "Requested version $Version does not match pyproject.toml version $ProjectVersion."
}

Push-Location $RepoRoot
try {
    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"

    Remove-PathInRepo $BuildDir
    Remove-PathInRepo $ReleaseDir
    New-Item -ItemType Directory -Path $PackageDir -Force | Out-Null
    New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null

    if ($InstallDeps) {
        Invoke-Native $PythonPath @("-m", "pip", "install", "-r", "requirements-dev.txt")
    }

    if (-not $SkipTests) {
        Invoke-Native $PythonPath @("-m", "pytest", "-q")
        Invoke-Native $PythonPath @("-m", "compileall", "-q", "aisrt", "tests")
        Invoke-Native $PythonPath @("-m", "pip", "check")
        Invoke-Native $PythonPath @("-m", "aisrt", "--help")
        Invoke-Native $PythonPath @("-m", "aisrt", "doctor")
        Invoke-Native $PythonPath @("-m", "aisrt.gui", "--check")
        Invoke-Native "git" @("diff", "--check")
    }

    $PackageItems = @(
        "aisrt",
        "docs",
        ".env.example",
        "AGENTS.md",
        "CHANGELOG.md",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "README.md",
        "SECURITY.md",
        "SUPPORT.md",
        "activate_env.bat",
        "open_ui.bat",
        "pyproject.toml",
        "requirements.txt",
        "requirements-torch-cu130.txt"
    )
    foreach ($Item in $PackageItems) {
        Copy-ProjectItem $Item
    }
    Write-PortableScripts
    Write-PortableReadme
    Remove-PackageRuntimeArtifacts $PackageDir

    Assert-PortableRequiredFiles $PackageDir
    Assert-NoForbiddenPayload $PackageDir
    Assert-NoPrivateText $PackageDir

    $ZipPath = Join-Path $ReleaseDir "$PackageName.zip"
    Compress-PortableArchive $PackageDir $ZipPath
    Assert-ZipRequiredFiles $ZipPath
    Assert-ZipNoForbiddenPayload $ZipPath

    Invoke-Native $PythonPath @("-m", "build", "--wheel", "--no-isolation", "--outdir", $ReleaseDir)

    $Assets = @(Get-ChildItem -LiteralPath $ReleaseDir -File | Where-Object {
        $_.Name -eq "$PackageName.zip" -or
        $_.Name -eq "aisrt-$Version-py3-none-any.whl"
    } | Sort-Object Name)
    if ($Assets.Count -lt 2) {
        throw "Expected release assets were not created."
    }

    $HashLines = foreach ($Asset in $Assets) {
        $Hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Asset.FullName).Hash.ToLowerInvariant()
        "$Hash  $($Asset.Name)"
    }
    Set-Content -LiteralPath (Join-Path $ReleaseDir "SHA256SUMS.txt") -Value $HashLines -Encoding ASCII

    $ReleaseNotesTemplate = Get-Content -LiteralPath (Join-Path $RepoRoot "packaging\release-notes-template.md") -Raw -Encoding UTF8
    $ReleaseNotes = $ReleaseNotesTemplate.Replace('$Version', $Version)
    Set-Content -LiteralPath (Join-Path $ReleaseDir "RELEASE_NOTES.md") -Value $ReleaseNotes -Encoding UTF8

    Write-Host "Release assets:"
    Get-ChildItem -LiteralPath $ReleaseDir -File | Sort-Object Name | Select-Object Name, Length, LastWriteTime | Format-Table -AutoSize
} finally {
    Pop-Location
}
