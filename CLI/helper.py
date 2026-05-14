

def process_reply(payload: dict) -> tuple:
    """Process the reply from the server and extract the command and value."""
    payload = payload.get("payload", {})
    cmd = None
    value = None
    for command, response in payload.items():
        cmd = command
        value = response
    return cmd, value 