import zeep
from zeep import Client
from zeep.helpers import serialize_object
from lxml import etree

class SOAPHandler:
    def __init__(self, auth_service, security_gate, wsdl_path="schema.wsdl"):
        self.auth_service = auth_service
        self.security_gate = security_gate
        self.client = Client(wsdl_path)
        self.binding = self.client.service._binding
        self.factory = self.client.type_factory('http://localhost:8000/soap')
        self.types = self.client.wsdl.types

    def _parse_request(self, xml, element_name):
        try:
            xml_text = etree.fromstring(xml.encode('utf-8'))                
            xsd = self.types.get_element(f"{{http://localhost:8000/soap}}{element_name}")            
            parsed_obj = xsd.parse(xml_text.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Body")[0], self.types)
            params = serialize_object(parsed_obj)
            
            for field_name, element in xsd.type.elements:
                if not element.is_optional and params.get(field_name) is None:
                    raise ValueError(f"Missing required field: '{field_name}'")

            return params.get("username"), params.get("password"), params.get("ip")

        except Exception as e:
            print(f"SOAP: {e}")
            raise ValueError(f"Invalid SOAP Request: {e}")

    def _build_response(self, element_name, data):
        xsd = self.types.get_element(f"{{http://localhost:8000/soap}}{element_name}")
        response = etree.Element(f"{{http://localhost:8000/soap}}{element_name}")
        xsd.render(response, data)
        body_content = etree.tostring(response, encoding="utf-8").decode('utf-8')
        return f"""<?xml version="1.0" encoding="utf-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="http://localhost:8000/soap">
        <soapenv:Body>
        {body_content}
        </soapenv:Body>
        </soapenv:Envelope>"""

    def _build_fault(self, fault_code, fault_string):
        return f"""<?xml version="1.0" encoding="utf-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
        <soapenv:Body>
        <soapenv:Fault>
        <faultcode>{fault_code}</faultcode>
        <faultstring>{fault_string}</faultstring>
        </soapenv:Fault>
        </soapenv:Body>
        </soapenv:Envelope>"""
    
    async def registration(self, xml):
        try:
            username, password, ip = self._parse_request(xml, "registrationRequest")
            if not username or not password:
                return self._build_fault("Client", "Wrong XML format")
        except ValueError as e:
            return self._build_fault("Client", str(e))

        if self.security_gate.is_blocked(ip):
            return self._build_fault("403", "Registration temporarily blocked for this IP")

        Rdata = await self.auth_service.register_user(username, password)
        
        if Rdata:
            response_data = {
                "status": "success",
                "message": f"User {Rdata.username} created",
                "uid": Rdata.uid,
                "token": Rdata.token
            }
            return self._build_response("registrationResponse", response_data)
        else:
            self.security_gate.register_failed_attempt(ip)
            return self._build_fault("Client", "User already exists")

    async def login(self, xml):
        try:
            username, password, ip = self._parse_request(xml, "loginRequest")
            if not username or not password:
                return self._build_fault("Client", "Wrong XML format")
        except ValueError as e:
            return self._build_fault("Client", str(e))
        if self.security_gate.is_blocked(ip):
            return self._build_fault("403", "Access temporarily blocked for this IP")
            
        Adata = await self.auth_service.authentificate_user(username, password)
        if Adata:
            response_data = {
                "status": "success",
                "username": Adata.username,
                "uid": Adata.uid,
                "token": Adata.token
            }
            return self._build_response("loginResponse", response_data)
        else:
            self.security_gate.register_failed_attempt(ip)
            return self._build_fault("Client", "Invalid username or password")