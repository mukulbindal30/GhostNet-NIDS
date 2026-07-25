import os
import sqlite3

# ==============================
# Database Path
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "database", "ghostnet.db")

# ==============================
# Create Database
# ==============================

def create_database():
    # Ensure the database directory exists
    os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS networks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ssid TEXT,
            bssid TEXT UNIQUE,
            rssi INTEGER,
            channel INTEGER,
            security TEXT,
            risk TEXT,
            score INTEGER,
            ai_report TEXT,
            first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# ==============================
# Save Network
# ==============================

def save_network(network, threat, ai_report):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO networks
        (
            ssid,
            bssid,
            rssi,
            channel,
            security,
            risk,
            score,
            ai_report,
            last_seen
        )
        VALUES
        (
            ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
        )
    """,
    (
        network.get("ssid", "Unknown"),
        network.get("bssid", "Unknown"),
        network.get("rssi", 0),
        network.get("channel", 0),
        network.get("security", "Unknown"),
        threat["level"],
        threat["score"],
        ai_report
    ))

    conn.commit()
    conn.close()