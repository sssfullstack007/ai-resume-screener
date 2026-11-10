# Publish this app to Hugging Face Spaces.
#
# One-time setup:
#   1. Create a Space at https://huggingface.co/new-space
#      SDK: Docker, hardware: CPU basic (free), visibility: public
#   2. Clone it next to this repository:
#        git clone https://huggingface.co/spaces/<user>/ai-resume-screener hf-space
#   3. Run this script from anywhere:
#        powershell -File deploy\huggingface\publish.ps1 -Target ..\hf-space
#
# Re-run the same command after changing app.py to publish an update.

param(
    [string]$Target = "..\hf-space",
    [switch]$Push
)

$ErrorActionPreference = "Stop"

$here = $PSScriptRoot
$src = (Resolve-Path (Join-Path $here "..\..")).Path

if (-not (Test-Path $Target)) {
    throw "Space checkout not found at '$Target'. Clone the Space repository first, or pass -Target."
}
$dst = (Resolve-Path $Target).Path

Write-Host "Copying app files from $src"
Copy-Item (Join-Path $src "app.py")          (Join-Path $dst "app.py")          -Force
Copy-Item (Join-Path $src "requirements.txt") (Join-Path $dst "requirements.txt") -Force
Copy-Item (Join-Path $src "LICENSE")         (Join-Path $dst "LICENSE")         -Force
Copy-Item (Join-Path $src "templates")       (Join-Path $dst "templates")       -Recurse -Force
Copy-Item (Join-Path $src "static")          (Join-Path $dst "static")          -Recurse -Force

Write-Host "Copying Space-specific files"
Copy-Item (Join-Path $here "Dockerfile")     (Join-Path $dst "Dockerfile")     -Force
Copy-Item (Join-Path $here "README.md")      (Join-Path $dst "README.md")      -Force
Copy-Item (Join-Path $here ".dockerignore")  (Join-Path $dst ".dockerignore")  -Force

# The Space only needs these files; anything else is noise in its diff.
foreach ($unwanted in @("tests", "deploy", "__pycache__", "uploads")) {
    $path = Join-Path $dst $unwanted
    if (Test-Path $path) { Remove-Item $path -Recurse -Force }
}

if (-not (Test-Path (Join-Path $dst ".git"))) {
    Write-Host ""
    Write-Host "Files copied. '$dst' is not a git repository, so nothing was pushed."
    Write-Host "Commit and push it to the Space manually."
    exit 0
}

Push-Location $dst
try {
    Write-Host ""
    Write-Host "Space diff:"
    git status --short

    if ($Push) {
        git add -A
        $staged = git diff --cached --name-only
        if ($staged) {
            git -c user.name="Sai Srinivas Shella" `
                -c user.email=shellasaisrinivas@gmail.com `
                commit -m "Sync from github.com/sssfullstack007/ai-resume-screener" | Out-Null
            git push
            Write-Host "Pushed. The Space will rebuild automatically."
        } else {
            Write-Host "Nothing to push; the Space is already up to date."
        }
    } else {
        Write-Host ""
        Write-Host "Review the diff, then re-run with -Push to publish."
    }
}
finally {
    Pop-Location
}
