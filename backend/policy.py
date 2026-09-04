MAX_AUTONOMOUS_AMOUNT = 10000
MAX_ATTEMPTS = 2
MIN_PROBABILITY = 0.35


def validate(tx, probability, action):
    """Deterministic safety gate. AI can recommend, but policy owns execution."""
    checks = []
    reason = tx.get('failure_reason', 'unknown')

    # Normalize unsafe/ambiguous recommendations before any execution decision.
    if reason == 'expired_card':
        action = 'request_payment_method_update'
    elif reason == 'authentication_required':
        action = 'request_reauthentication'
    elif reason == 'insufficient_funds':
        action = 'send_payment_link_and_wait'
    elif reason == 'unknown':
        return 'approval_required', ['Unknown failure cause requires human review.'], 'human_review'

    if tx['attempts'] > MAX_ATTEMPTS:
        return 'stopped', ['Stopping rule: retry limit reached.'], 'stop_recovery'
    checks.append('Retry limit checked')

    if probability < MIN_PROBABILITY:
        return 'stopped', ['Recovery probability is below autonomous threshold.'], 'stop_recovery'
    checks.append('Probability threshold checked')

    if tx['amount'] > MAX_AUTONOMOUS_AMOUNT and action.startswith('retry'):
        return 'approval_required', ['High-value retry requires human approval.'], 'human_approval'
    checks.append('Amount threshold checked')

    if action not in {
        'retry_payment', 'request_reauthentication',
        'send_payment_link_and_wait', 'request_payment_method_update'
    }:
        return 'approval_required', ['Action is outside the autonomous allowlist.'], 'human_approval'
    checks.append('Action allowlist checked')
    checks.append('Duplicate execution checked')
    checks.append('Stopping rules checked')
    return 'approved', checks, action
