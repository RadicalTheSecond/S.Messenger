import json
from chat_manager import Message

class WebSocketsHandler:
    def __init__(self, chat_manager):
        self.chat_manager = chat_manager

    async def handle_connection(self, websocket):
        uid = None
        try:
            auth_data = await websocket.recv()
            auth_packet = json.loads(auth_data)
            
            if auth_packet.get("action") == "connect" and "token" in auth_packet:
                token = auth_packet.get("token")
                query = "SELECT id FROM users WHERE token = $1;"
                user_record = await self.chat_manager.db.execute_query(query, token)
                if user_record:
                    uid = user_record[0]["id"]
                    await self.chat_manager.register_connection(uid, websocket)
                else:
                    print("[WebSocketsHandler] Попытка входа с невалидным токеном.")
                    await websocket.close(code=4001, reason="Invalid Token")
                    return
            else:
                await websocket.close(code=4000, reason="Missing Connection Action")
                return

            async for raw_message in websocket:
                packet = json.loads(raw_message)
                action = packet.get("action")

                if action == "send_message":
                    msg = Message(
                        sender_id=uid,
                        reciever_id=packet.get("receiver_id"),
                        text=packet.get("text")
                    )
                    await self.chat_manager.send_message(msg)
                    ack = {"status": "success", "message_id": msg.id}
                    await websocket.send(json.dumps(ack, ensure_ascii=False))

                elif action == "get_online_users":
                    await self.handle_get_online_users(websocket)

        except Exception as e:
            print(f"[WebSocketsHandler] Соединение с пользователем {uid} закрылось с ошибкой: {e}")
        finally:
            if uid is not None:
                await self.chat_manager.remove_connection(uid)

    async def handle_get_online_users(self, websocket):
        online_list = self.chat_manager.get_online_users()
        response = {
            "action": "online_users_list",
            "users": online_list
        }
        await websocket.send(json.dumps(response, ensure_ascii=False))