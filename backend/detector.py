# ==========================================
# GhostNet NIDS Threat Detection Engine
# ==========================================

def analyze_network(network, db_historical_networks=None):
    """
    Analyzes a parsed network packet for vulnerabilities, Honeypots, and Evil Twin attacks.
    """
    score = 0
    reasons = []

    # Safely extract values
    security = network.get("security", "UNKNOWN").upper()
    rssi = network.get("rssi", -100)
    channel = network.get("channel", 0)
    ssid = network.get("ssid", "")
    bssid = network.get("bssid", "")

    # --------------------------------------
    # 1. Honeypot & Rogue AP Profiling
    # --------------------------------------
    suspicious_keywords = ["free", "public", "admin", "test", "starbucks", "airport", "guest"]
    ssid_lower = ssid.lower()
    
    if any(keyword in ssid_lower for keyword in suspicious_keywords) and security == "OPEN":
        score += 50
        reasons.append(f"High probability of Rogue AP or Honeypot based on SSID profiling ('{ssid}').")

    # --------------------------------------
    # 2. Advanced Evil Twin Detection
    # --------------------------------------
    if db_historical_networks:
        for hist_net in db_historical_networks:
            # If the SSID matches but the physical MAC address (BSSID) is different
            if hist_net['ssid'] == ssid and hist_net['bssid'] != bssid:
                # If the historical network was secure, but this new one is OPEN
                if hist_net['security'] != "OPEN" and security == "OPEN":
                    score += 90
                    reasons.append(f"CRITICAL: Evil Twin Attack Detected! Open network spoofing a known secure SSID ({ssid}).")
                # If they are just broadcasting on a different channel with a different MAC (Potential Clone)
                else:
                    score += 20
                    reasons.append(f"Warning: Multiple APs detected using the same SSID ({ssid}) but different MAC addresses.")

    # --------------------------------------
    # 3. Standard Encryption Analysis
    # --------------------------------------
    if security == "OPEN":
        score += 80
        reasons.append("Open Wi-Fi network (no encryption). Data is transmitted in plaintext.")
    elif "WEP" in security:
        score += 70
        reasons.append("Legacy WEP encryption detected. Highly vulnerable to statistical cracking.")
    elif security == "WPA" and "WPA2" not in security:
        score += 35
        reasons.append("Legacy WPA encryption detected. Vulnerable to dictionary attacks.")
    elif "WPA/WPA2" in security:
        score += 15
        reasons.append("Mixed WPA/WPA2 mode detected. Susceptible to downgrade attacks.")
    elif "WPA2" in security:
        score += 0  # Standard secure baseline
    elif "WPA3" in security:
        score += 0  # Most secure

    # --------------------------------------
    # 4. Hidden SSID
    # --------------------------------------
    if ssid == "" or ssid == "<Hidden>":
        score += 20
        reasons.append("Hidden SSID detected. Often used to mask reconnaissance networks.")

    # --------------------------------------
    # 5. Signal & Channel Analytics
    # --------------------------------------
    signal = "Strong"
    if rssi <= -90:
        signal = "Very Weak"
    elif rssi <= -80:
        signal = "Weak"
    elif rssi <= -70:
        signal = "Medium"

    if channel not in [1, 6, 11] and channel > 0:
        reasons.append(f"Non-standard Wi-Fi channel ({channel}) detected. May indicate misconfiguration or evasion tactics.")

    # --------------------------------------
    # 6. Risk Level Calculation
    # --------------------------------------
    # Ensure score doesn't exceed 100
    score = min(score, 100)

    if score >= 70:
        level = "HIGH"
    elif score >= 30:
        level = "MEDIUM"
    else:
        level = "LOW"

    # De-duplicate reasons just in case
    reasons = list(set(reasons))

    return {
        "score": score,
        "level": level,
        "signal": signal,
        "reasons": reasons
    }