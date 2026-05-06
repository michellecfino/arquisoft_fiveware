import jwt
import time

private_key = "superclave_prueba_123456"

users = [
    {"sub": "admin", "role": "ADMIN"},
    {"sub": "user", "role": "USER"}
]

tokens = []
for user in users:
    payload = {
    "sub": user["sub"],
    "aud": "https://biteco/api",
    "iss": "https://biteco/auth/test",  # <-- Agrega esta línea
    "role": user["role"],
    "iat": int(time.time()),
    "exp": int(time.time()) + 3600
}
    token = jwt.encode(payload, private_key, algorithm="HS256")
    tokens.append(token)

for t in tokens:
    print(t)