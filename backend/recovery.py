from .db import get_transaction, conn, log
from .decision import decide_transaction

def simulate_recovery(tx_id, approved=False):
    d=decide_transaction(tx_id); tx=d.get('transaction')
    if not tx: return d
    status=d['policy']['status']
    if status=='approval_required' and not approved:
        log('RECOVERY_GATED',tx_id,'Human approval required; no payment attempted.')
        return {'success':False,'status':'approval_required','message':'Recovery is gated. No payment was attempted.','decision':d}
    if status=='stopped':
        log('RECOVERY_STOPPED',tx_id,'Stopping rule prevented execution.')
        return {'success':False,'status':'stopped','message':'Recovery stopped by policy.','decision':d}
    with conn() as c:
        duplicate=c.execute("SELECT 1 FROM recovery_events WHERE transaction_id=?",(tx_id,)).fetchone()
        if duplicate: return {'success':False,'status':'duplicate','message':'Duplicate execution prevented.','decision':d}
        outcome='recovered' if __import__('random').Random(sum(map(ord,tx_id))).random()<d['ml']['recovery_probability'] else 'failed'
        c.execute('INSERT INTO recovery_events(transaction_id,action,amount,result) VALUES(?,?,?,?)',(tx_id,d['final_action'],tx['amount'],outcome))
        c.execute('UPDATE transactions SET status=? WHERE id=?',('recovered' if outcome=='recovered' else 'processed',tx_id))
    log('RECOVERY_SIMULATED',tx_id,f"Outcome={outcome}; action={d['final_action']}")
    return {'success':outcome=='recovered','status':outcome,'message':'Test-mode recovery workflow executed; no real payment was charged.','decision':d}
