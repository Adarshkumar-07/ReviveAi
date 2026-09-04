import os

os.environ['LLM_PROVIDER'] = 'mock'

from backend.db import init_db, reset_simulation, seed_transactions, get_transaction
from backend.policy import validate
from backend.decision import decide_transaction


def setup_function():
    init_db()
    reset_simulation()
    seed_transactions(100)


def test_policy_normalizes_expired_card_action():
    tx = get_transaction('RV-10000')
    tx['failure_reason'] = 'expired_card'
    status, checks, action = validate(tx, 0.90, 'retry_payment')
    assert status == 'approved'
    assert action == 'request_payment_method_update'


def test_low_probability_is_stopped():
    tx = get_transaction('RV-10000')
    status, _, action = validate(tx, 0.10, 'retry_payment')
    assert status == 'stopped'
    assert action == 'stop_recovery'


def test_unknown_failure_requires_human_approval():
    tx = get_transaction('RV-10000')
    tx['failure_reason'] = 'unknown'
    status, _, action = validate(tx, 0.90, 'retry_payment')
    assert status == 'approval_required'
    assert action == 'human_review'


def test_decision_uses_policy_action():
    result = decide_transaction('RV-10000')
    assert result['policy']['action'] == result['final_action'] or result['policy']['status'] != 'approved'


def test_reset_clears_previous_simulation_events():
    from backend.db import conn
    with conn() as c:
        c.execute("INSERT INTO audit_logs(transaction_id,event,details) VALUES('RV-10000','TEST','before reset')")
    reset_simulation()
    with conn() as c:
        assert c.execute('SELECT COUNT(*) FROM audit_logs').fetchone()[0] == 0
