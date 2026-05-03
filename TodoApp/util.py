import hashlib
from passlib.context import CryptContext

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    sha_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return bcrypt_context.hash(sha_hash)

def verify_password(plain: str, hashed: str) -> bool:
    sha_hash = hashlib.sha256(plain.encode("utf-8")).hexdigest()
    return bcrypt_context.verify(sha_hash, hashed)
