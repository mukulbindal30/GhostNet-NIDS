const API = "http://127.0.0.1:8000";

async function loadDashboard() {
    try {
        // ==========================
        // Load Statistics
        // ==========================
        const statsResponse = await fetch(`${API}/stats`);
        const stats = await statsResponse.json();

        document.getElementById("totalNetworks").innerText = stats.total_networks;
        document.getElementById("highRisk").innerText = stats.high_risk;
        document.getElementById("mediumRisk").innerText = stats.medium_risk;
        document.getElementById("lowRisk").innerText = stats.low_risk;

        // ==========================
        // Load Networks
        // ==========================
        const networkResponse = await fetch(`${API}/networks`);
        const networks = await networkResponse.json();

        const table = document.getElementById("networkTable");
        const threatBox = document.getElementById("threatBox");
        const timeline = document.getElementById("timeline");

        table.innerHTML = "";
        threatBox.innerHTML = "";
        timeline.innerHTML = "";

        let highRiskDetected = false;

        networks.forEach(network => {
            // -----------------------
            // Risk Color
            // -----------------------
            let riskClass = "low-risk";
            if (network.risk === "HIGH") {
                riskClass = "high-risk";
                highRiskDetected = true;
            } else if (network.risk === "MEDIUM") {
                riskClass = "medium-risk";
            }

            // -----------------------
            // Network Table
            // -----------------------
            table.innerHTML += `
                <tr>
                    <td>${network.ssid || "(Hidden)"}</td>
                    <td>${network.security}</td>
                    <td>${network.rssi}</td>
                    <td class="${riskClass}">
                        ${network.risk}
                    </td>
                </tr>
            `;

            // -----------------------
            // AI Panel
            // -----------------------
            if (network.risk === "HIGH") {
                // Parse the AI report string back into an object if possible, 
                // or just display the formatted string passed from the backend
                threatBox.innerHTML += `
                    <div class="threat-card">
                        <h3>${network.ssid || "Hidden Network"}</h3>
                        <p><b>Risk:</b> <span class="${riskClass}">${network.risk}</span></p>
                        <br>
                        <p style="white-space: pre-line; line-height: 1.5;">${network.ai_report}</p>
                    </div>
                `;
            }

            // -----------------------
            // Timeline
            // -----------------------
            timeline.innerHTML += `
                <div class="timeline-item">
                    <b>${network.ssid || "Hidden Network"}</b><br>
                    Risk: <span class="${riskClass}">${network.risk}</span>
                </div>
            `;
        });

        // -----------------------
        // No High Risk Fallback
        // -----------------------
        if (threatBox.innerHTML === "") {
            threatBox.innerHTML = `
                <div class="threat-card" style="border-left:6px solid #00ff66">
                    <h3>System Status</h3>
                    <p>No High Risk Networks Detected.</p>
                </div>
            `;
        }

        return highRiskDetected;

    } catch (error) {
        console.log("Error loading dashboard data:", error);
    }
}

// ==========================
// WebSocket Integration
// ==========================
function setupWebSocket() {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws");

    ws.onopen = () => {
        console.log("🟢 Live SOC WebSocket Connected");
        document.querySelector(".dot").style.background = "#00ff66";
    };

    ws.onmessage = async (event) => {
        // When the backend broadcasts a new packet, refresh the UI
        const hasHighRisk = await loadDashboard();
        
        // Visual alert for new high-risk threats
        if (hasHighRisk) {
            document.body.style.boxShadow = "inset 0 0 80px rgba(255, 77, 77, 0.4)";
            setTimeout(() => {
                document.body.style.boxShadow = "none";
            }, 1500);
        }
    };

    ws.onclose = () => {
        console.log("🔴 WebSocket Disconnected. Reconnecting...");
        document.querySelector(".dot").style.background = "#ff4d4d";
        setTimeout(setupWebSocket, 3000);
    };
    
    ws.onerror = (error) => {
        console.error("WebSocket Error:", error);
        ws.close();
    };
}

// First Load & Initialize WebSockets
loadDashboard();
setupWebSocket();