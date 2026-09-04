import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pathlib import Path
from backend.db import init_db, seed_transactions, get_transactions, get_transaction, get_metrics, get_audit
from backend.decision import decide_transaction
from backend.recovery import simulate_recovery
from backend.evaluation import run_evaluation

ROOT = Path(__file__).resolve().parent
DIST = ROOT / 'frontend' / 'dist'
app = Flask(__name__, static_folder=str(DIST), static_url_path='')

allowed_origins = [x.strip() for x in os.getenv('CORS_ORIGINS', '').split(',') if x.strip()]
if allowed_origins:
    CORS(app, origins=allowed_origins)

init_db()
seed_transactions(500)


def json_body():
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}


def parse_count(payload):
    value = payload.get('count', 500)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError('count must be an integer')
    return min(max(value, 50), 5000)


@app.get('/api/health')
def health():
    return jsonify({'status': 'ok', 'mode': 'SIMULATION / TEST MODE'})


@app.get('/api/metrics')
def metrics():
    return jsonify(get_metrics())


@app.get('/api/transactions')
def transactions():
    try:
        limit = int(request.args.get('limit', 30))
    except (TypeError, ValueError):
        return jsonify({'error': 'limit must be an integer'}), 400
    return jsonify(get_transactions(min(max(limit, 1), 100)))


@app.get('/api/transactions/<tx_id>')
def transaction(tx_id):
    tx = get_transaction(tx_id)
    return (jsonify(tx), 200) if tx else (jsonify({'error': 'not found'}), 404)


@app.post('/api/transactions/seed')
def seed():
    try:
        count = parse_count(json_body())
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    seed_transactions(count, reset=True)
    return jsonify({'transactions': count, 'metrics': get_metrics()})


@app.post('/api/decide')
def decide():
    tx_id = json_body().get('transaction_id')
    if not isinstance(tx_id, str) or not tx_id.strip() or len(tx_id) > 64:
        return jsonify({'error': 'valid transaction_id required'}), 400
    result = decide_transaction(tx_id.strip())
    return jsonify(result), 200 if 'error' not in result else 404


@app.post('/api/recover')
def recover():
    payload = json_body()
    tx_id = payload.get('transaction_id')
    if not isinstance(tx_id, str) or not tx_id.strip() or len(tx_id) > 64:
        return jsonify({'error': 'valid transaction_id required'}), 400
    approved = payload.get('approved', False)
    if not isinstance(approved, bool):
        return jsonify({'error': 'approved must be boolean'}), 400
    return jsonify(simulate_recovery(tx_id.strip(), approved))


@app.post('/api/simulate')
def simulate():
    try:
        count = parse_count(json_body())
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    seed_transactions(count, reset=True)
    return jsonify({
        'metrics': get_metrics(),
        'evaluation': run_evaluation(count),
        'transactions': get_transactions(30)
    })


@app.get('/api/evaluation')
def evaluation():
    return jsonify(run_evaluation(len(get_transactions(5000))))


@app.get('/api/audit')
def audit():
    return jsonify(get_audit(100))


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def frontend(path):
    if path and (DIST / path).is_file():
        return send_from_directory(DIST, path)
    if (DIST / 'index.html').exists():
        return send_from_directory(DIST, 'index.html')
    return jsonify({'message': 'Run the Vite frontend with npm run dev, or build it with npm run build.'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_DEBUG') == '1')
