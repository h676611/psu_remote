import re

CONSTS: dict[str, float] = {
    "mu": 1e-6, 
    "m": 1e-3,
    "n": 1e-9,
    "": 1
}

def process_payload(payload: dict) -> dict:
    for key, value in payload.items():
        if "get" in key:
            print(f"Processing getter command: {key} with value: {value}")
            # For getters, we typically don't have values to process, so we can skip
            return payload
        elif isinstance(value, str):
            # 1. Strip 'A' and 'V' from the ends
            clean_value: str = value.strip("AV")
            
            # 2. Extract the suffix (last 1 or 2 chars) and the numeric part
            # This regex looks for digits/decimals followed by our specific suffixes
            match: re.Match = re.fullmatch(r"([\d\.]+)(m|mu|n)?", clean_value)
            
            if match:
                number_str: str = match.group(1)
                suffix: str = match.group(2) if match.group(2) else "" # Handle the empty string case
                
                try:
                    payload[key] = float(number_str) * CONSTS[suffix]
                except ValueError:
                    raise ValueError(f"Invalid numeric value: {number_str} for key: {key}")
            else:
                raise ValueError(f"Invalid format in value: {value}. Expected number followed by m, mu, or n.")
    
    return payload