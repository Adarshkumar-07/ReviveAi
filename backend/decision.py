import json
from .db import get_transaction, conn, log
from .ml import predict
from .llm import reason
from .policy import validate


def decide_transaction(tx_id):
    tx = get_transaction(tx_id)
    if not tx:
        return {'error': 'transaction not found'}

    probability = predict(tx)
    ai = reason(tx, probability)
    status, checks, policy_action = validate(tx, probability, ai['recommended_action'])
    final = policy_action if status == 'approved' else (
        'human_approval' if status == 'approval_required' else 'stop_recovery'
    )

    with conn() as c:
        c.execute(
            'INSERT INTO decisions(transaction_id,probability,diagnosis,recommendation,final_action,policy_status) VALUES(?,?,?,?,?,?)',
            (tx_id, probability, ai['diagnosis'], ai['recommended_action'], final, status)
        )

    log('DECISION_CREATED', tx_id, json.dumps({
        'probability': round(probability, 4),
        'provider': ai['provider'],
        'policy': status,
        'recommended_action': ai['recommended_action'],
        'policy_action': policy_action,
        'final_action': final
    }))

    return {
        'transaction': tx,
        'ml': {'recovery_probability': round(probability, 4)},
        'llm': ai,
        'policy': {'status': status, 'checks': checks, 'action': policy_action},
        'final_action': final
    }
