import re

CONSTS: dict[str, float] = {
    "mu": 1e-6, 
    "m": 1e-3,
    "n": 1e-9,
    "": 1
}


def process_payload(payload: dict) -> dict:
    """Normalize payload values for PSU commands."""
    new_payload: dict = {}
    for key, value in payload.items():
        if "get" in key:
            # Getters don't need value processing.
            new_payload[key] = value
            pass
        elif value == "CURR" or value == "VOLT":
            new_payload[key] = value
            pass
        elif key == "set_channel":
            # For set_channel, we expect an integer channel number.
            try:
                new_payload[key] = int(value)
            except ValueError:
                raise ValueError(f"Invalid channel number: {value} for key: {key}")
        elif isinstance(value, str):
            # Strip trailing A/V units, then parse optional scale suffix.
            clean_value: str = value.strip("AV")
            match: re.Match = re.fullmatch(r"([-\d\.]+)(m|mu|n)?", clean_value)
            if match:
                number_str: str = match.group(1)
                suffix: str = match.group(2) if match.group(2) else ""
                try:
                    new_payload[key] = float(number_str) * CONSTS[suffix]
                except ValueError:
                    raise ValueError(f"Invalid numeric value: {number_str} for key: {key}")
            else:
                raise ValueError(
                    f"Invalid format in value: {value}. Expected number followed by m, mu, or n."
                )
        else:
            new_payload[key] = value
    return new_payload
