import json

def parse_network(raw_data):
    """
    Safely parses the incoming JSON string from the ESP32.
    """
    try:
        # Check if the data is purely empty or whitespace
        if not raw_data or not raw_data.strip():
            return None
            
        return json.loads(raw_data)

    except json.JSONDecodeError:
        # Silently ignore broken serial lines (common in hardware communication)
        return None
    except Exception as e:
        print(f"Parser Error: {e}")
        return None