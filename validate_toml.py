import tomllib
import sys

print("Checking pyproject.toml...")
try:
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    print("✅ Valid TOML. Parsed content:")
    print(data)
except Exception as e:
    print(f"❌ Invalid TOML: {e}")
    # Print hex of first 50 bytes
    with open("pyproject.toml", "rb") as f:
        print(f"Hex dump: {f.read(50).hex()}")
    sys.exit(1)
