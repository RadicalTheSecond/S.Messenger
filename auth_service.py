import hashlib
import secrets

class AuthService:
    def __init__(self, db):
        self.db = db

    async def register_user(self, username, password):
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        query = "INSERT INTO users (username, password_hash) VALUES ($1, $2) RETURNING id;"
        try:
            result = await self.db.execute_query(query, username, password_hash)
            if not result:
                return False
            user_id = result[0]['id']
            token = secrets.token_hex(16)
            update_query = "UPDATE users SET token = $1 WHERE id = $2;"
            await self.db.execute_query(update_query, token, user_id)
            return {"uid": user_id, "token": token, "username": username}
            
        except Exception as e:
            print(f"Ошибка при регистрации {username}: {e}")
            return False

    async def authentificate_user(self, username, password):
        query = "SELECT id, password_hash, token FROM users WHERE username = $1;"
        result = await self.db.execute_query(query, username)
        
        if not result:
            return None
            
        stored_hash = result[0]['password_hash']
        user_id = result[0]['id']
        existing_token = result[0]['token']  
        
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if input_hash == stored_hash:
            return {"uid": user_id, "token": existing_token}
            
        return None  