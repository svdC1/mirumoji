# Run all Python and Frontend Linters

param([switch]$Fix)

$ErrorActionPreference = "Stop"
$PythonDir = "apps\mirumoji"
$FrontendDir = "apps\frontend"

Write-Host "=== Python: Ruff ===" -ForegroundColor Cyan
if ($Fix) {
    ruff check --fix "$PythonDir\src"
    ruff format "$PythonDir\src"
} else {
    ruff check "$PythonDir\src"
    ruff format --check "$PythonDir\src"
}

Write-Host "=== Python: MyPy ===" -ForegroundColor Cyan
mypy "$PythonDir\src"

Write-Host "=== Frontend: eslint ===" -ForegroundColor Cyan
Push-Location $FrontendDir
try {
    if ($Fix) { npm run lint:fix } else { npm run lint }
} finally { Pop-Location }

Write-Host "=== Frontend: prettier ===" -ForegroundColor Cyan
Push-Location $FrontendDir
try {
    if ($Fix) { npm run format } else { npx prettier --check src }
} finally { Pop-Location }

Write-Host "All checks passed." -ForegroundColor Green
