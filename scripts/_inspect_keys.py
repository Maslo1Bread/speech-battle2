from backend.app.config import get_settings
from backend.app.security import decrypt_text, _fernet
from cryptography.fernet import Fernet, InvalidToken
import hashlib, base64, sqlite3

s = get_settings()
print("secret_is_default", s.secret_key == "change-me-to-a-long-random-string-please")
print("secret_len", len(s.secret_key))

c = sqlite3.connect("speech_battle.db")
row = c.execute("select id, username_enc from users where id=2").fetchone()
print("enc_prefix", row[1][:20] if row else None)

def fernet_from(secret: str) -> Fernet:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)

candidates = [
    s.secret_key,
    "change-me-to-a-long-random-string-please",
    "dev-secret",
    "secret",
]
enc = row[1]
for cand in candidates:
    try:
        text = fernet_from(cand).decrypt(enc.encode()).decode()
        print("DECRYPTED with candidate index", candidates.index(cand), "->", text)
    except Exception as e:
        print("fail index", candidates.index(cand), type(e).__name__)
