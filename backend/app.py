from ai_engine import analyze_with_ai
import serial
import time
import traceback
import sqlite3
import os

from parser import parse_network
from detector import analyze_network
from database import create_database, save_network

# Configuration

PORT = "COM9" #connected port
BAUD_RATE = 115200

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "database", "ghostnet.db")


def get_historical_networks():
    """Fetches known networks from the DB to detect Evil Twin spoofing."""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT ssid, bssid, security FROM networks")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception:
        return []

# Connect to ESP32


try:
    ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
    time.sleep(2)

    print("=" * 60)
    print("            👻 GhostNet NIDS Started")
    print("=" * 60)

    create_database()
    print("✅ Database Ready")

    while True:

        # Read serial data from ESP32
        raw_data = ser.readline().decode(errors="ignore").strip()

        if not raw_data:
            continue

        # Parse JSON
        network = parse_network(raw_data)

        if network is None:
            continue

        # Fetch history for stateful heuristics
        history = get_historical_networks()

        # Analyze threat (Now with Evil Twin & Honeypot detection)
        threat = analyze_network(network, db_historical_networks=history)

        # AI Analysis
        try:
            ai_report = analyze_with_ai(network, threat)
        except Exception as e:
            ai_report = {"summary": "Error", "threat": "AI connection failed", "recommendation": str(e)}

        # Extract string for database saving (since AI now returns JSON)
        if isinstance(ai_report, dict):
            formatted_ai_report = f"Summary: {ai_report.get('summary', '')}\nThreat: {ai_report.get('threat', '')}\nRecommendation: {ai_report.get('recommendation', '')}"
        else:
            formatted_ai_report = str(ai_report)

        # Save to database
        save_network(network, threat, formatted_ai_report)

        # Console Output
        print("\n" + "=" * 60)
        print("                👻 GhostNet NIDS Report")
        print("=" * 60)

        print(f"SSID      : {network.get('ssid', 'Unknown')}")
        print(f"BSSID     : {network.get('bssid', 'Unknown')}")
        print(f"RSSI      : {network.get('rssi', 0)} dBm")
        print(f"Channel   : {network.get('channel', 0)}")
        print(f"Security  : {network.get('security', 'Unknown')}")
        print(f"Risk      : {threat['level']} (Score: {threat['score']})")
        
        if threat['reasons']:
            print("\n⚠️ Flags:")
            for reason in threat['reasons']:
                print(f" - {reason}")

        print("\n🤖 AI Analysis")
        print("-" * 60)
        print(formatted_ai_report)

        print("=" * 60)

except serial.SerialException:
    print("❌ Could not connect to ESP32.")
    print("Make sure:")
    print("1. ESP32 is connected")
    print(f"2. COM Port is {PORT}")
    print("3. Arduino Serial Monitor is closed")

except KeyboardInterrupt:
    print("\n👋 GhostNet NIDS Stopped.")

except Exception as e:
    print("\n❌ Unexpected Error:")
    traceback.print_exc()