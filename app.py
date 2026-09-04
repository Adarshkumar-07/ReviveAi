from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pathlib import Path
from backend.db import init_db, seed_transactions, get_transactions, get_metrics, get_audit
from backend.decision import decide_transaction
from backend.recovery import simulate_recovery
from backend.evaluation import run_evaluation

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "frontend" / "dist"
app = Flask(__name__, static_folder=str(DIST), static_url_path="")
CORS(app)
init_db()
seed_transactions(500)

@app.get("/api/health")
def health(): return jsonify({"status":"ok","mode":"SIMULATION / TEST MODE"})

@app.get("/api/metrics")
def metrics(): return jsonify(get_metrics())

@app.get("/api/transactions")
def transactions():
    limit=min(max(int(request.args.get("limit",30)),1),100)
    return jsonify(get_transactions(limit))

@app.get("/api/transactions/<tx_id>")
def transaction(tx_id):
    rows=get_transactions(500)
    tx=next((r for r in rows if r["id"]==tx_id),None)
    return (jsonify(tx),200) if tx else (jsonify({"error":"not found"}),404)

@app.post("/api/transactions/seed")
def seed():
    count=min(max(int((request.json or {}).get("count",500)),50),5000)
    seed_transactions(count, reset=True)
    return jsonify({"transactions":count,"metrics":get_metrics()})

@app.post("/api/decide")
def decide():
    tx_id=(request.json or {}).get("transaction_id")
    if not tx_id: return jsonify({"error":"transaction_id required"}),400
    result=decide_transaction(tx_id)
    return jsonify(result), 200 if "error" not in result else 404

@app.post("/api/recover")
def recover():
    payload=request.json or {}
    if not payload.get("transaction_id"): return jsonify({"error":"transaction_id required"}),400
    return jsonify(simulate_recovery(payload["transaction_id"], bool(payload.get("approved",False))))

@app.post("/api/simulate")
def simulate():
    count=min(max(int((request.json or {}).get("count",500)),50),5000)
    seed_transactions(count, reset=True)
    return jsonify({"metrics":get_metrics(),"evaluation":run_evaluation(count),"transactions":get_transactions(30)})

@app.get("/api/evaluation")
def evaluation(): return jsonify(run_evaluation(len(get_transactions(5000))))
@app.get("/api/audit")
def audit(): return jsonify(get_audit(100))

@app.route("/", defaults={"path":""})
@app.route("/<path:path>")
def frontend(path):
    if path and (DIST / path).is_file(): return send_from_directory(DIST,path)
    if (DIST/"index.html").exists(): return send_from_directory(DIST,"index.html")
    return jsonify({"message":"Run the Vite frontend with npm run dev, or build it with npm run build."}),404

if __name__=="__main__": app.run(host="0.0.0.0",port=5000,debug=True)
