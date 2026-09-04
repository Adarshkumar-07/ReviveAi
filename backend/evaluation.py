from .db import get_transactions
from .ml import train, METRICS, predict

def run_evaluation(n=500):
    rows=get_transactions(min(n,5000)); train()
    qualified=sum(r['amount'] for r in rows if predict(r)>=.35 and r['attempts']<=2)
    baseline=sum(r['amount']*.38 for r in rows if r['failure_reason'] in ('temporary_bank_error','network_timeout') and r['attempts']<=2)
    expected=sum(r['amount']*predict(r) for r in rows if r['attempts']<=2)
    lift=((expected-baseline)/baseline*100) if baseline else 0
    return {'batch_size':len(rows),'revenue_at_risk':round(sum(r['amount'] for r in rows),2),'qualified_recoverable_revenue':round(qualified,2),'expected_recovered_revenue':round(expected,2),'baseline_expected_revenue':round(baseline,2),'recovery_lift_pct':round(lift,1),'ml':METRICS}
