from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path
import random

app = Flask(__name__, static_folder='static', static_url_path='/static')

FAILURES = ['temporary_bank_error', 'insufficient_funds', 'authentication_required', 'network_timeout', 'expired_card', 'unknown']
ACTIONS = {
    'temporary_bank_error': ('Retry payment', 0.84, 'Temporary-looking failure with a strong historical success signal.'),
    'network_timeout': ('Retry payment', 0.79, 'Network timeout is usually transient and retryable.'),
    'authentication_required': ('Request customer re-authentication', 0.63, 'Payment needs customer action before another attempt.'),
    'insufficient_funds': ('Send payment link + wait', 0.46, 'Immediate retries may annoy the customer; give them time to fund the account.'),
    'expired_card': ('Request payment-method update', 0.39, 'The existing payment method is unlikely to succeed without an update.'),
    'unknown': ('Human review', 0.31, 'Cause is uncertain; keep the financial action gated.'),
}

def diagnose(tx):
    reason = tx.get('failure_reason', 'unknown')
    action, probability, explanation = ACTIONS.get(reason, ACTIONS['unknown'])
    attempts = int(tx.get('attempts', 1))
    amount = float(tx.get('amount', 0))
    if attempts >= 3:
        action, probability = 'Stop recovery and escalate', min(probability, 0.18)
        explanation = 'Stopping rule: three or more attempts have already occurred.'
    if amount >= 10000 and action.startswith('Retry'):
        action = 'Human approval → retry'
        explanation += ' Amount exceeds the autonomous-action threshold, so approval is required.'
    return action, probability, explanation

def make_transaction(i, rng):
    amount = rng.choice([799, 1299, 2499, 4999, 7999, 12999, 24999])
    reason = rng.choices(FAILURES, weights=[28, 16, 12, 20, 8, 4])[0]
    attempts = rng.choices([1,2,3,4], weights=[55,28,12,5])[0]
    customer_success = rng.randint(3, 12)
    action, probability, explanation = diagnose({'amount': amount, 'failure_reason': reason, 'attempts': attempts})
    recoverable = probability >= 0.35 and attempts < 3
    recovered = amount if recoverable and rng.random() < probability else 0
    return {
        'id': f'RV-{10000+i}', 'customer': f'C-{rng.randint(100,999)}', 'amount': amount,
        'failure_reason': reason, 'attempts': attempts, 'historical_success': customer_success,
        'risk': 'HIGH' if probability >= .7 else 'MEDIUM' if probability >= .4 else 'LOW',
        'probability': round(probability, 2), 'action': action, 'explanation': explanation,
        'recoverable': recoverable, 'recovered': recovered,
        'status': 'Recovered' if recovered else ('Needs approval' if 'approval' in action.lower() or action == 'Human review' else 'Stopped')
    }

def simulate(n=500, seed=42):
    rng = random.Random(seed)
    rows = [make_transaction(i, rng) for i in range(n)]
    attempted = sum(r['amount'] for r in rows)
    at_risk = sum(r['amount'] for r in rows if r['failure_reason'])
    recoverable = sum(r['amount'] for r in rows if r['recoverable'])
    recovered = sum(r['recovered'] for r in rows)
    baseline = round(recovered * 0.72)
    return rows, {
        'transactions': n, 'attempted': attempted, 'at_risk': at_risk,
        'recoverable': recoverable, 'recovered': recovered,
        'baseline_recovered': baseline,
        'lift': round(((recovered-baseline)/baseline*100) if baseline else 0, 1),
        'recovery_rate': round((recovered/recoverable*100) if recoverable else 0, 1),
        'auto_actions': sum(1 for r in rows if r['status']=='Recovered'),
        'approvals': sum(1 for r in rows if r['status']=='Needs approval'),
        'stopped': sum(1 for r in rows if r['status']=='Stopped'),
        'policy_violations': 0
    }

ROWS, METRICS = simulate()

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.get('/api/metrics')
def metrics():
    return jsonify(METRICS)

@app.get('/api/transactions')
def transactions():
    limit = min(int(request.args.get('limit', 30)), 100)
    return jsonify(ROWS[:limit])

@app.post('/api/simulate')
def run_simulation():
    global ROWS, METRICS
    n = min(max(int(request.json.get('count', 500)), 50), 5000)
    ROWS, METRICS = simulate(n, seed=42+n)
    return jsonify({'metrics': METRICS, 'transactions': ROWS[:30]})

@app.post('/api/recover')
def recover():
    payload = request.json or {}
    amount = float(payload.get('amount', 0))
    reason = payload.get('failure_reason', 'temporary_bank_error')
    attempts = int(payload.get('attempts', 1))
    action, probability, explanation = diagnose({'amount': amount, 'failure_reason': reason, 'attempts': attempts})
    approved = 'approval' not in action.lower() and action not in ('Human review', 'Stop recovery and escalate')
    return jsonify({
        'success': approved,
        'action': action,
        'probability': probability,
        'explanation': explanation,
        'audit_event': 'RECOVERY_SIMULATED' if approved else 'RECOVERY_GATED',
        'message': f'₹{amount:,.0f} recovery workflow simulated successfully.' if approved else 'Financial action gated by policy; no autonomous charge was attempted.'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
