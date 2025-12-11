from hashlib import sha256

SALT = "PASSWORD_SALT"
pw = "admin5151"
hashed = sha256((SALT + pw).encode("utf-8")).hexdigest()
print(hashed)
