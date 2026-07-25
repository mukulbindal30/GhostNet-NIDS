import json
from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def analyze_with_ai(network, threat):
    """
    Passes the network telemetry and heuristic threat data to the LLM.
    Enforces a strict JSON response format for seamless UI/DB integration.
    """
    
    # Safely extract data in case keys are missing
    ssid = network.get('ssid', 'Unknown')
    security = network.get('security', 'Unknown')
    rssi = network.get('rssi', 'Unknown')
    channel = network.get('channel', 'Unknown')
    level = threat.get('level', 'Unknown')
    score = threat.get('score', 0)
    reasons = ", ".join(threat.get("reasons", ["No specific heuristic flags."]))

    prompt = f"""
    You are an expert Cyber Security System analyzing wireless network telemetry.
    
    Analyze the following Wi-Fi network:
    SSID: {ssid}
    Security: {security}
    RSSI: {rssi} dBm
    Channel: {channel}
    
    Heuristic Engine Threat Level: {level} (Score: {score})
    Heuristic Flags: {reasons}

    You MUST respond in raw JSON format with exactly these three keys:
    "summary": A brief, professional overview of the network's risk profile (max 2 sentences).
    "threat": Specific details about the potential attack vector or vulnerabilities (max 2 sentences).
    "recommendation": Actionable steps to mitigate the risk (max 2 sentences).
    """

    try:
        chat = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Low temperature for deterministic, factual outputs
            response_format={"type": "json_object"}  # Forces the LLM to output valid JSON
        )

        # Parse the string response into a Python dictionary
        response_text = chat.choices[0].message.content
        return json.loads(response_text)

    except json.JSONDecodeError:
        # Fallback if the LLM fails to generate proper JSON
        return {
            "summary": "AI Parsing Error",
            "threat": "The AI model returned an improperly formatted response.",
            "recommendation": "Check the API endpoint and prompt constraints."
        }
    except Exception as e:
        # Fallback for network timeouts or invalid API keys
        return {
            "summary": "AI Connection Failed",
            "threat": "Could not reach the AI diagnostic engine.",
            "recommendation": f"Verify Groq API Key and internet connection. Error: {str(e)}"
        }