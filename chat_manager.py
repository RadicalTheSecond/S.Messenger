import json
from datetime import datetime

class Message:
    def __init__(self, sender_id, reciever_id, text, message_id=None, timestamp=None, is_delivered=False):
        self.id = message_id
        self.sender_id = sender_id
        self.reciever_id = reciever_id
        self.text = text
        self.timestamp = timestamp or datetime.now()
        self.is_delivered = is_delivered

class ChatManager:
    def __init__(self, db_manager):
        self.active_connections = {}  
        self.user_statuses = {}       
        self.db = db_manager          

    async def register_connection(self, uid, websocket):
        self.active_connections[uid] = websocket
        self.user_statuses[uid] = "online"
        unread = await self.db.get_unread_messages(uid)
        
        for row in unread:
            packet = {"action": "push_message", "id": row["id"], "sender_id": row["sender_id"], "text": row["text"], "timestamp": str(row["timestamp"])}
            await websocket.send(json.dumps(packet, ensure_ascii=False))
            await self.db.execute_query("UPDATE messages SET is_delivered = true WHERE id = $1;", row["id"])

    async def remove_connection(self, uid):
        if uid in self.active_connections:
            del self.active_connections[uid]
        self.user_statuses[uid] = "offline"

    async def set_user_status(self, uid, status):
        self.user_statuses[uid] = status

    async def send_message(self, message):
        receiver_ws = self.active_connections.get(message.reciever_id)
        is_online = receiver_ws is not None
        query = "INSERT INTO messages (sender_id, receiver_id, text, is_delivered) VALUES ($1, $2, $3, $4) RETURNING id, timestamp;"
        result = await self.db.execute_query(query, message.sender_id, message.reciever_id, message.text, is_online)
        
        if result:
            message.id = result[0]["id"]
            message.timestamp = result[0]["timestamp"]

        if is_online:
            self.user_statuses[message.reciever_id] = "chatting"
            packet = {"action": "push_message", "id": message.id, "sender_id": message.sender_id, "text": message.text, "timestamp": str(message.timestamp)}
            await receiver_ws.send(json.dumps(packet, ensure_ascii=False))

    def get_online_users(self):
        return [uid for uid, status in self.user_statuses.items() if status != "offline"]