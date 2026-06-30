import asyncio
from aiohttp import web
import websockets

from database import DatabaseManager
from auth_service import AuthService
from security_gate import SecurityGate
from soap_handler import SOAPHandler
from chat_manager import ChatManager
from websockets_handler import WebSocketsHandler

DSN = "postgresql://postgres:qweasdzxc098@localhost:5432/MDB"

async def handle_soap_request(request):
    soap_handler = request.app['soap_handler']
    
    if request.method == "GET":
        try:
            with open("schema.wsdl", "r", encoding="utf-8") as f:
                wsdl_content = f.read()
            return web.Response(text=wsdl_content, content_type="text/xml", charset="utf-8")
        except FileNotFoundError:
            error_xml = "<?xml version='1.0'?><error>WSDL file 'schema.wsdl' not found on server</error>"
            return web.Response(text=error_xml, content_type="text/xml", status=404)

    elif request.method == "POST":
        xml_data = await request.text()
        
        if "registrationRequest" in xml_data:
            response_xml = await soap_handler.registration(xml_data)
        elif "loginRequest" in xml_data:
            response_xml = await soap_handler.login(xml_data)
        else:
            response_xml = """<?xml version="1.0"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><soap:Fault><faultcode>Client</faultcode><faultstring>Unknown request</faultstring></soap:Fault></soap:Body></soap:Envelope>"""
        
        return web.Response(text=response_xml, content_type="text/xml", charset="utf-8")


async def main():
    db = DatabaseManager(DSN)
    await db.connect()

    auth_service = AuthService(db)
    security_gate = SecurityGate()
    soap_handler = SOAPHandler(auth_service, security_gate)

    chat_manager = ChatManager(db)
    ws_handler = WebSocketsHandler(chat_manager)

    app = web.Application()
    app['soap_handler'] = soap_handler  
    app.router.add_get('/soap', handle_soap_request)
    app.router.add_post('/soap', handle_soap_request)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8000)

    print("-> SOAP сервер запущен на http://localhost:8000/soap")
    print("-> WebSocket сервер запущен на ws://localhost:8765")

    await site.start() 
    async with websockets.serve(ws_handler.handle_connection, "localhost", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Сервер] Работа успешно завершена.")