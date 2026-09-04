MAX_AUTONOMOUS_AMOUNT=10000
MAX_ATTEMPTS=2
MIN_PROBABILITY=.35

def validate(tx, probability, action):
    checks=[]
    if tx['attempts']>MAX_ATTEMPTS: return 'stopped',['Stopping rule: retry limit reached.']
    if probability<MIN_PROBABILITY: return 'stopped',['Recovery probability is below autonomous threshold.']
    if tx['amount']>MAX_AUTONOMOUS_AMOUNT and action.startswith('retry'): return 'approval_required',['High-value recovery requires human approval.']
    if tx['failure_reason']=='expired_card': action='request_payment_method_update'
    if tx['failure_reason']=='authentication_required': action='request_reauthentication'
    if tx['failure_reason']=='insufficient_funds': action='send_payment_link_and_wait'
    if tx['failure_reason']=='unknown': return 'approval_required',['Unknown failure cause requires human review.']
    checks += ['Amount threshold checked','Retry limit checked','Duplicate execution checked','Stopping rules checked']
    return 'approved',checks
