import json
from chat_manager import Message

class WebSocketsHandler:
    def __init__(self, chat_manager):
        self.chat_manager = chat_manager

    async def handle_connection(self, websocket):
        uid = None
        try:
            Adata = await websocket.recv()            
            try:
                Apacket = json.loads(Adata)
            except Exception:
                await websocket.close(code=4000, reason="Invalid JSON")
                return
            
            if Apacket.get("action") == "connect" and "token" in Apacket:
                user_record = await self.chat_manager.db.execute_query("SELECT id FROM users WHERE token = $1;", Apacket.get("token"))
                if user_record:
                    uid = int(user_record[0]["id"])
                    await self.chat_manager.register_connection(uid, websocket)
                else:
                    await websocket.close(code=4001, reason="Invalid Token")
                    return
            else:
                await websocket.close(code=4000, reason="Missing Connection Action")
                return

            async for raw_message in websocket:
                try:
                    packet = json.loads(raw_message)
                except Exception:
                    print(f"{uid} Invalid JSON.")
                    continue
                action = packet.get("action")
                if action == "send_message":
                    msg = Message(
                        sender_id=uid,
                        receiver_id=int(packet.get("receiver_id")),
                        text=packet.get("text")
                    )
                    await self.chat_manager.send_message(msg)
                    ack = {"status": "success", "message_id": msg.id}
                    await websocket.send(json.dumps(ack, ensure_ascii=False))
                elif action == "get_online_users":
                    await self.handle_get_online_users(websocket)

        except Exception as e:
            print(f"Соединение с {uid} закрылось с ошибкой: {e}")
        finally:
            if uid is not None:
                await self.chat_manager.remove_connection(uid)

    async def handle_get_online_users(self, websocket):
        await websocket.send(json.dumps({"action": "online_users_list","users": self.chat_manager.get_online_users()}, ensure_ascii=False))