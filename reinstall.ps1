Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "mcpv" -Force -ErrorAction SilentlyContinue

# Clear PYTHONHOME to prevent build isolation errors
$env:PYTHONHOME = $null

# 1. 패키지 재설치 (라이브러리 업데이트)
uv pip install . --system --reinstall



# 2. Setup (Create Shortcut, etc)
python -m mcpv install --force
