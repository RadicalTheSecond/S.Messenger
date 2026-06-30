from lxml import etree

class SOAPHandler:
    def __init__(self, auth_service, security_gate):
        self.auth_service = auth_service
        self.security_gate = security_gate

    def _build_soap_response(self, body_content):
        return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
   <soap:Body>
      {body_content}
   </soap:Body>
</soap:Envelope>"""

    def _build_soap_fault(self, fault_code, fault_string):
        return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
   <soap:Body>
      <soap:Fault>
          <faultcode>{fault_code}</faultcode>
          <faultstring>{fault_string}</faultstring>
      </soap:Fault>
   </soap:Body>
</soap:Envelope>"""

    def _parse_credentials(self, xml_text):
        try:
            root = etree.fromstring(xml_text.encode('utf-8'))
            username = root.find(".//username").text
            password = root.find(".//password").text
            ip_tag = root.find(".//ip")
            ip = ip_tag.text if ip_tag is not None else "127.0.0.1"
            return username, password, ip
        except Exception:
            return None, None, None

    async def registration(self, xml):
        username, password, ip = self._parse_credentials(xml)
        if not username or not password:
            return self._build_soap_fault("Client", "Wrong XML format")

        if self.security_gate.is_blocked(ip):
            return self._build_soap_fault("403", "Registration temporarily blocked for this IP")

        reg_data = await self.auth_service.register_user(username, password)
        
        if reg_data:
            body = f"""<registrationResponse>
            <status>success</status>
            <message>User {reg_data['username']} created and logged in</message>
            <uid>{reg_data['uid']}</uid>
            <token>{reg_data['token']}</token>
    </registrationResponse>"""
            return self._build_soap_response(body)
        else:
            self.security_gate.register_failed_attempt(ip)
            return self._build_soap_fault("Client", "User already exists")

    async def login(self, xml):
        username, password, ip = self._parse_credentials(xml)
        if not username or not password:
            return self._build_soap_fault("Client", "Wrong XML format")
        if self.security_gate.is_blocked(ip):
            return self._build_soap_fault("403", "Access temporarily blocked for this IP")
        auth_data = await self.auth_service.authentificate_user(username, password)
        if auth_data:
            body = f"""<loginResponse>
            <status>success</status>
            <username>{username}</username>
            <uid>{auth_data['uid']}</uid>
            <token>{auth_data['token']}</token>
</loginResponse>"""
            return self._build_soap_response(body)
        else:
            self.security_gate.register_failed_attempt(ip)
            return self._build_soap_fault("Client", "Invalid username or password")