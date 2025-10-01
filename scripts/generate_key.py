import secrets
import os

# Generiere einen sicheren 32-Byte-Schlüssel (256 Bit)
key = secrets.token_urlsafe(32)
print(f"Ihr sicherer JWT-Schlüssel: {key}")
print("\nFüge dies in deine .env-Datei ein:")
print(f"MIND_JWT_SECRET={key}")