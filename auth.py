from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

# Şifreleme ayarları (bcrypt algoritması)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Güvenlik Anahtarları (Gerçek projelerde çevre değişkeninde - .env - saklanır)
SECRET_KEY = "etkili-ogrenme-ve-ai-asistani-gizli-anahtar-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # İstediğin 30 dakikalık süre sınırı!

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kullanıcının girdiği şifre ile veritabanındaki hash'lenmiş şifreyi karşılaştırır."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> bool:
    """Girilen düz şifreyi güvenli hash formatına dönüştürür."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Kullanıcıya özel, 30 dakika süreli JWT token üretir."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt