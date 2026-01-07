import os

try:
    with open("pyproject.toml", "rb") as f:
        content = f.read(20)
        print(f"First 20 bytes: {content}")
        print(f"Hex: {content.hex()}")
except Exception as e:
    print(f"Error reading file: {e}")
