import collections
import logging
import os
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from fraud_shield.coordinator import CoordinatorAgent
from fraud_shield.registry import AgentRegistry
from fraud_shield.interfaces import CoordinatorResponse
from fraud_shield.router import RoutingDecision

# Custom logging handler to store recent logs in memory for the UI Logs viewer
class MemoryLogHandler(logging.Handler):
    def __init__(self, capacity: int = 200):
        super().__init__()
        self.buffer = collections.deque(maxlen=capacity)
        
    def emit(self, record):
        try:
            # Format the record to get standard text representation
            msg = self.format(record)
            self.buffer.append({
                "timestamp": self.formatter.formatTime(record, "%Y-%m-%d %H:%M:%S") if self.formatter else str(record.created),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage()
            })
        except Exception:
            self.handleError(record)

# Initialize logging handler
log_handler = MemoryLogHandler()
log_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log_handler.setLevel(logging.INFO)

# Attach handler to root logger to capture all system and agent logs
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.INFO)

# Also explicitly ensure fraud_shield logger forwards to it
fs_logger = logging.getLogger("fraud_shield")
fs_logger.addHandler(log_handler)
fs_logger.setLevel(logging.INFO)

# FastAPI App initialization
app = FastAPI(
    title="AI Fraud Shield Coordinator Dashboard",
    description="Backend API supporting the AI Fraud Shield Multi-Agent cybersecurity verification dashboard."
)

# Enable CORS for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared coordinator agent instance
coordinator = CoordinatorAgent()

# Static scenarios
EXAMPLES: List[str] = [
    "Analyze this email: Dear customer, your account is suspended. Click here to verify your password or wire $500.",
    "Is this WhatsApp message a scam? 'Hey mom, I lost my phone, please transfer $2000 to my friend's account immediately.'",
    "Check this URL: https://goog1e-security-login.com/index.html",
    "Is this internship genuine? I received a Telegram message offering a remote data entry job paying $100 per hour, but I need to deposit $50 first for training.",
    "Is this shopping website trustworthy? The online store is selling high-end cameras with a 95% discount, but they have no refund policy or phone contact details.",
    "My bank called and asked for my OTP verification code because of an unusual login.",
    "Analyze everything and give me a risk report: Here is the email urgent security warning, the payment link is http://amazon-security-update.com, and they want me to send a gift card verification code."
]

class AnalysisRequest(BaseModel):
    text: str
    selected_agents: Optional[List[str]] = None

@app.get("/api/scenarios")
def get_scenarios():
    """Returns the pre-configured capstone scenarios."""
    return {"scenarios": EXAMPLES}

@app.get("/api/agents")
def get_agents():
    """Returns the list of dynamically registered agents and their metadata."""
    return {"agents": AgentRegistry.get_agent_metadata()}

@app.post("/api/analyze")
def analyze(payload: AnalysisRequest):
    """Analyzes a fraud-related text, either auto-routing or targeting specific sub-agents."""
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")
    
    logging.info(f"Received web analysis request: '{payload.text[:60]}...'")
    
    try:
        # Override routing if specific agents were selected by the user in Custom Query
        if payload.selected_agents and len(payload.selected_agents) > 0:
            logging.info(f"Bypassing automatic router. Manually executing agents: {payload.selected_agents}")
            response = coordinator.process_request(payload.text, selected_agents=payload.selected_agents)
        else:
            response = coordinator.process_request(payload.text)
            
        return response
    except Exception as e:
        logging.error(f"Error during API analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal analysis error: {str(e)}")

@app.post("/api/run-all")
def run_all():
    """Runs all 7 capstone scenarios sequentially and returns the compiled result list."""
    logging.info("Running batch analysis on all 7 capstone scenarios...")
    results = []
    for idx, scenario in enumerate(EXAMPLES, 1):
        try:
            response = coordinator.process_request(scenario)
            results.append({
                "index": idx,
                "scenario": scenario,
                "response": response
            })
        except Exception as e:
            logging.error(f"Error running scenario {idx}: {str(e)}")
            results.append({
                "index": idx,
                "scenario": scenario,
                "error": str(e)
            })
    return {"results": results}

@app.get("/api/logs")
def get_logs(level: Optional[str] = None):
    """Streams the buffered logs for the Logs terminal UI page."""
    logs = list(log_handler.buffer)
    if level and level.lower() != "all":
        logs = [log for log in logs if log["level"].upper() == level.upper()]
    return {"logs": logs}

@app.post("/api/logs/clear")
def clear_logs():
    """Clears the current logging buffer."""
    log_handler.buffer.clear()
    logging.info("Backend logging buffer cleared by user request.")
    return {"status": "success"}

# Serve static files for frontend SPA dashboard
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    uvicorn.run("server:app", host=host, port=port, reload=reload)

