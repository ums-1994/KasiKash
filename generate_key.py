import secrets
import base64

# Generate a secure random key
key = secrets.token_hex(32)
print(f"Generated Secret Key: {key}")

# Also generate a base64 encoded version (sometimes preferred)
b64_key = base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
print(f"\nBase64 Encoded Key: {b64_key}") 