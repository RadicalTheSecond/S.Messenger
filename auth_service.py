import hashlib
import secrets

class User:
    def __init__(self, uid, username, password_hash, token):
        self.uid = uid
        self.username = username
        self.password_hash = password_hash
        self.token = token
        
class AuthService:
    def __init__(self, db):
        self.db = db

    async def register_user(self, username, password):
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            token = secrets.token_hex(16)
            result = await self.db.execute_query(
                "INSERT INTO users (username, password_hash, token) VALUES ($1, $2, $3) RETURNING id;", username, password_hash, token)
            if not result:
                return False

            return User(result[0]['id'], username, password_hash, token)
        except Exception as e:
            print(f"Ошибка при регистрации {username}: {e}")
            return False

    async def authentificate_user(self, username, password):
        await self.db.execute_query("UPDATE users SET token = $1 WHERE username = $2;", secrets.token_hex(16), username)
        result = await self.db.execute_query("SELECT id, password_hash, token FROM users WHERE username = $1;", username)
        if not result:
            return None
        U = User(result[0]['id'], username, result[0]['password_hash'],  result[0]['token'])    
        if hashlib.sha256(password.encode()).hexdigest() == U.password_hash:
            return U
        return None