from usocket import socket, getaddrinfo, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
import uasyncio.core as asyncio
import ujson as json

from homie.modules.base import HomieModule, import_module
from homie.core.logger import Logger


LOG = Logger("API Module")


class Request:
    def __init__(self, client, method, path, version, headers, body=None):
        self._client = client
        self._method = method
        self._path = path
        self._version = version
        self._headers = headers
        self._body = body


class Response:
    def __init__(self, client):
        self._client = client
        self._status = 200
        self._headers = {}
        self._body = None

    def json(self, json_str, status=200):
        self._status = status
        self._headers['content-type'] = 'application/json'
        self._body = json_str.encode('UTF-8')


def parse_heading(heading_str):
    method, path, version = heading_str.split(' ')
    return (method, path, version)


def build_heading(code):
    return "HTTP/1.1 {} Unknown".format(code)


def parse_header(header_str):
    k, v = header_str.split(':', 1)
    return (k.lower(), v.strip())


def build_header(k, v):
    return "{}: {}".format(k.lower(), v.strip())


def handel_client(client, handel_request):
    request_line = client.readline().strip(b"\r\n")
    method, path, version = parse_heading(request_line.decode("UTF-8"))
    LOG.debug('method:', method, 'path:', path, "version:", version)

    headers = {}
    while True:
        request_line = client.readline().strip(b"\r\n")
        if not request_line or request_line == b"":
            break
        request_line = request_line.decode("UTF-8")
        k, v = parse_header(request_line)
        headers[k] = v

    body = None
    if 'content-length' in headers:
        content_length = int(headers['content-length'])
        print('content_length:', content_length)
        if content_length > 1024:
            # error
            pass
        elif content_length > 0:
            body = client.read(content_length)

    request = Request(client, method, path, version, headers, body)
    response = Response(client)

    handel_request(request, response)

    client.write(build_heading(response._status).encode("UTF-8"))
    client.write(b'\r\n')

    if response._body:
        content_length = len(response._body)
        if content_length > 1024:
            # error
            pass
        elif content_length > 0:
            response._headers['content-length'] = str(content_length)

    response._headers['connection'] = 'close'

    for k, v in response._headers.items():
        client.write(build_header(k, v).encode("UTF-8"))
        client.write(b'\r\n')

    client.write(b'\r\n')
    client.write(response._body)

    client.close()


class APIModule(HomieModule):
    def init(self):
        LOG.debug("Init")
        self._config = None
        self._socket = None
        self._task = None

    def start(self):
        LOG.debug('Start')
        self._config = import_module(self._homie, "ConfigurationModule")

        addr = getaddrinfo('0.0.0.0', 81,  0, SOCK_STREAM)[0]
        self._socket = socket(addr[0], addr[1], addr[2])
        self._socket.setblocking(False)
        self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self._socket.bind(addr[-1])
        self._socket.listen(1)

        self._task = self._homie.add_task(self.handle_connections, homie_arg=False)

    def stop(self, reason):
        LOG.debug("Stop:", reason)
        if self._task:
            self._homie.stop_task(self._task)
        self._socket.close()

    async def handle_connections(self):
        while True:
            try:
                client, client_addr = self._socket.accept()
                # client.setblocking(False)
                handel_client(client, self.handel_request)
            except OSError:
                pass

            await asyncio.sleep_ms(10)

    def handel_request(self, req, res):
        method = req._method
        path = req._path
        if method == 'GET':
            if path == "/info":
                info = {
                    "device_name": "name"
                }
                return res.json(json.dumps(info))
            elif path == "/config":
                current_config = self._config.current_config
                current_config["network"]["wifi"]["ssid"] = "***"
                return res.json(json.dumps(current_config))
