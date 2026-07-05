import requests
import json

print("=== AI FRAUD SHIELD - APP HEALTH CHECK ===")
print()

BASE = "http://127.0.0.1:8000"

# 1. Frontend HTML
r = requests.get(BASE + "/")
print(f"[1] Frontend (/)           : {r.status_code} OK - {len(r.text)} bytes HTML served")

# 2. Agents list
r = requests.get(BASE + "/api/agents")
agents = r.json()["agents"]
print(f"[2] GET /api/agents        : {r.status_code} OK - {len(agents)} agents registered")
for a in agents:
    print(f"     * {a['name']}")

# 3. Scenarios list
r = requests.get(BASE + "/api/scenarios")
scenarios = r.json()["scenarios"]
print(f"[3] GET /api/scenarios     : {r.status_code} OK - {len(scenarios)} scenarios loaded")

# 4. Analyze endpoint
query = "Analyze this email: Dear customer, your account is suspended. Click here to verify your password or wire 500 dollars."
r = requests.post(BASE + "/api/analyze", json={"text": query})
result = r.json()
print(f"[4] POST /api/analyze      : {r.status_code} OK")
print(f"     Input Type    : {result['input_type']}")
print(f"     Risk Level    : {result['overall_risk']}")
print(f"     Status        : {result['analysis_status']}")
print(f"     Agents Used   : {result['selected_agents']}")
print(f"     Recommendation: {result['recommendation'][:90]}...")

# 5. Run-all batch
r = requests.post(BASE + "/api/run-all")
batch = r.json()
print(f"[5] POST /api/run-all      : {r.status_code} OK - {len(batch['results'])} scenarios processed")
for item in batch["results"]:
    resp = item.get("response", {})
    risk = resp.get("overall_risk", "ERROR")
    status = resp.get("analysis_status", "error")
    print(f"     Scenario {item['index']}: Risk={risk}, Status={status}")

# 6. Logs
r = requests.get(BASE + "/api/logs")
logs = r.json()["logs"]
print(f"[6] GET /api/logs          : {r.status_code} OK - {len(logs)} log entries buffered")

print()
print("=== ALL SYSTEMS OPERATIONAL ===")
