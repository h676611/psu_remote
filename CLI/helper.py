

def process_reply(payload: dict) -> dict:
    payload = payload.get("payload", {})
    cmd = None
    value = None
    for command, response in payload.items():
        cmd = command
        value = response
    return cmd, value 