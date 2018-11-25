import ure as re


ENCODING = 'utf-8'
TRUE = "true"
FALSE = 'false'


def payload_down(payload):
    if payload is None:
        return ""

    if isinstance(payload, bool):
        return TRUE if payload else FALSE
    elif isinstance(payload, int):
        return str(payload)
    elif isinstance(payload, float):
        return str(payload)
    elif isinstance(payload, str):
        return payload

    raise Exception("Failed to convert payload to string")


def payload_up(payload):
    if payload is "":
        return None

    if not isinstance(payload, str):
        raise Exception("Payload must be of string type")

    if payload == TRUE:
        return True
    elif payload == FALSE:
        return False
    try:
        return int(payload)
    except ValueError:
        pass
    try:
        return float(payload)
    except ValueError:
        pass
    return payload


def string_down(msg):
    if msg is None:
        return b""
    if isinstance(msg, str):
        return msg.encode("utf-8")
    raise Exception("Failed to convert string to bytes")


def string_up(msg):
    if msg == b"":
        return None
    if isinstance(msg, bytes):
        return msg.decode("utf-8")
    raise Exception("Failed to convert bytes to string")


id_regex = re.compile(r"^[a-z0-9][a-z0-9\-]*[a-z0-9]$")


def valid_id(id):
    if not id:
        return False
    match = id_regex.match(id)
    return True if match else False
