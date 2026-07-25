from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import sqlite3
import os
from datetime import datetime
from fpdf import FPDF

# ======================================
# FastAPI App
# ======================================

app = FastAPI(title="GhostNet NIDS API")

# ======================================
# Enable CORS
# ======================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================
# Database Path
# ======================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "ghostnet.db")

# ======================================
# WebSocket Manager (Real-Time Updates)
# ======================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# ======================================
# Routes
# ======================================

@app.get("/")
def home():
    return {
        "status": "GhostNet NIDS API Running"
    }

@app.get("/networks")
def get_networks():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            ssid,
            bssid,
            rssi,
            channel,
            security,
            risk,
            score,
            ai_report,
            first_seen,
            last_seen
        FROM networks
        ORDER BY last_seen DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

@app.get("/stats")
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM networks")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM networks WHERE risk='HIGH'")
    high = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM networks WHERE risk='MEDIUM'")
    medium = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM networks WHERE risk='LOW'")
    low = cursor.fetchone()[0]

    conn.close()

    return {
        "total_networks": total,
        "high_risk": high,
        "medium_risk": medium,
        "low_risk": low
    }

# ======================================
# WebSocket Endpoint
# ======================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, can be used to receive manual commands from UI
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ======================================
# PDF Export Endpoint
# ======================================

@app.get("/export/pdf")
def export_pdf():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Fetch high-risk networks for the SOC report
    cursor.execute("SELECT ssid, bssid, security, risk, ai_report FROM networks WHERE risk='HIGH' ORDER BY last_seen DESC")
    high_risk_nets = cursor.fetchall()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.cell(200, 10, "GhostNet NIDS - Security Audit Report", ln=True, align='C')
    
    # Timestamp
    pdf.set_font("Helvetica", size=10)
    pdf.cell(200, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
    pdf.ln(10)

    # Content
    if not high_risk_nets:
        pdf.set_font("Helvetica", style="B", size=12)
        pdf.cell(200, 10, "System Status: SECURE. No High-Risk Networks Detected.", ln=True)
    else:
        for net in high_risk_nets:
            ssid, bssid, security, risk, ai_report = net
            
            pdf.set_font("Helvetica", style="B", size=12)
            pdf.set_text_color(255, 0, 0) # Red for high risk
            pdf.cell(200, 10, f"Threat Detected: {ssid} ({bssid}) - {risk} RISK", ln=True)
            
            pdf.set_font("Helvetica", style="B", size=10)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(200, 8, f"Security Profile: {security}", ln=True)
            
            pdf.set_font("Helvetica", size=10)
            pdf.multi_cell(0, 8, f"AI Analysis:\n{ai_report}")
            pdf.ln(8)

    pdf_path = os.path.join(BASE_DIR, "GhostNet_SOC_Report.pdf")
    pdf.output(pdf_path)
    
    return FileResponse(pdf_path, media_type='application/pdf', filename="GhostNet_SOC_Report.pdf")