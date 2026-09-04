import random
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / 'reviveai.db'
FAILURES = ['temporary_bank_error', 'insufficient_funds', 'authentication_required', 'network_timeout', 'expired_card', 'unknown']
METHODS = ['card', 'upi', 'netbanking', 'wallet']


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with conn() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS transactions(
            id TEXT PRIMARY KEY, customer TEXT, amount REAL, failure_reason TEXT,
            payment_method TEXT, attempts INTEGER, customer_age_days INTEGER,
            historical_success_rate REAL, prior_failures_30d INTEGER,
            minutes_since_failure INTEGER, subscription INTEGER,
            status TEXT DEFAULT 'pending'
        );
        CREATE TABLE IF NOT EXISTS decisions(
            id INTEGER PRIMARY KEY AUTOINCREMENT, transaction_id TEXT,
            probability REAL, diagnosis TEXT, recommendation TEXT,
            final_action TEXT, policy_status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS recovery_events(
            id INTEGER PRIMARY KEY AUTOINCREMENT, transaction_id TEXT,
            action TEXT, amount REAL, result TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS audit_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT, transaction_id TEXT,
            event TEXT, details TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        ''')


def reset_simulation():
    """Clear all simulation state so every run starts from a clean batch."""
    with conn() as c:
        c.execute('DELETE FROM recovery_events')
        c.execute('DELETE FROM decisions')
        c.execute('DELETE FROM audit_logs')
        c.execute('DELETE FROM transactions')


def seed_transactions(n=500, reset=False):
    if reset:
        reset_simulation()
    rng = random.Random(20260904 + n)
    with conn() as c:
        existing = c.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]
        if existing >= n:
            return
        for i in range(existing, n):
            reason = rng.choices(FAILURES, [27, 17, 13, 21, 8, 4])[0]
            amount = rng.choice([799, 1299, 2499, 4999, 7999, 12999, 24999])
            c.execute(
                'INSERT OR REPLACE INTO transactions VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                (f'RV-{10000+i}', f'C-{rng.randint(100,999)}', amount, reason,
                 rng.choice(METHODS), rng.choices([1,2,3,4], [55,28,12,5])[0],
                 rng.randint(30,1200), round(rng.uniform(.45,.99),2),
                 rng.randint(0,4), rng.randint(5,720), rng.choice([0,1]), 'pending')
            )


def get_transactions(limit=30):
    with conn() as c:
        return [dict(r) for r in c.execute(
            'SELECT * FROM transactions ORDER BY amount DESC LIMIT ?', (limit,)
        ).fetchall()]


def get_transaction(tx_id):
    with conn() as c:
        r = c.execute('SELECT * FROM transactions WHERE id=?', (tx_id,)).fetchone()
        return dict(r) if r else None


def log(event, tx_id, details):
    with conn() as c:
        c.execute(
            'INSERT INTO audit_logs(transaction_id,event,details) VALUES(?,?,?)',
            (tx_id, event, details)
        )


def get_audit(limit=100):
    with conn() as c:
        return [dict(r) for r in c.execute(
            'SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?', (limit,)
        ).fetchall()]


def get_metrics():
    with conn() as c:
        total = c.execute('SELECT COALESCE(SUM(amount),0) FROM transactions').fetchone()[0]
        qualified = c.execute('''
            SELECT COALESCE(SUM(t.amount),0)
            FROM transactions t
            JOIN (
                SELECT transaction_id, probability,
                       ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY id DESC) rn
                FROM decisions
            ) d ON d.transaction_id=t.id AND d.rn=1
            WHERE d.probability >= .35 AND t.attempts <= 2
              AND t.status='pending'
        ''').fetchone()[0]
        recovered = c.execute(
            "SELECT COALESCE(SUM(amount),0) FROM recovery_events WHERE result='recovered'"
        ).fetchone()[0]
        recovery_attempts = c.execute('SELECT COUNT(*) FROM recovery_events').fetchone()[0]
        approvals = c.execute(
            "SELECT COUNT(*) FROM decisions WHERE policy_status='approval_required'"
        ).fetchone()[0]
        stopped = c.execute(
            "SELECT COUNT(*) FROM decisions WHERE policy_status='stopped'"
        ).fetchone()[0]
        violations = c.execute('''
            SELECT COUNT(*) FROM recovery_events e
            JOIN decisions d ON d.transaction_id=e.transaction_id
            WHERE d.policy_status != 'approved'
        ''').fetchone()[0]
        return {
            'transactions': c.execute('SELECT COUNT(*) FROM transactions').fetchone()[0],
            'at_risk': round(total, 2),
            'recoverable': round(qualified, 2),
            'recovered': round(recovered, 2),
            'recovery_rate': round(recovered / total * 100, 1) if total else 0,
            'auto_actions': recovery_attempts,
            'approvals': approvals,
            'stopped': stopped,
            'policy_violations': violations
        }
