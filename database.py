import asyncio
import asyncpg

class DatabaseManager:
    def __init__(self, dsn):
        self._pool = None
        self.dsn = dsn

    async def connect(self):
        if not self._pool:
            self._pool = await asyncpg.create_pool(self.dsn)
            print("База данных успешно подключена.")

    async def disconnect(self):
        if self._pool:
            await self._pool.close()

    async def execute_query(self, query, *args):
        if not self._pool:
            raise RuntimeError("Пул соединений не инициализирован.")
        
        async with self._pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def get_unread_messages(self, uid):
        query = """
            SELECT id, sender_id, receiver_id, text, timestamp 
            FROM messages 
            WHERE receiver_id = $1 AND is_delivered = FALSE
            ORDER BY timestamp ASC;
        """
        return await self.execute_query(query, uid)