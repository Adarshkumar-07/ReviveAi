from .db import get_transactions
from .ml import train, METRICS, predict, latent_probability


def run_evaluation(n=500):
    rows = get_transactions(min(n, 5000))
    train()
    eligible = [r for r in rows if r['attempts'] <= 2]
    predictions = {r['id']: predict(r) for r in eligible}

    # Independent synthetic outcomes. These are never generated from the model score.
    outcomes = {
        r['id']: int(__import__('random').Random(sum(map(ord, r['id']))).random() < latent_probability(r))
        for r in eligible
    }

    threshold = METRICS.get('threshold', .35)
    qualified = [r for r in eligible if predictions[r['id']] >= threshold]
    strategy_recovered = sum(r['amount'] * outcomes[r['id']] for r in qualified)

    # Baseline: bounded retry strategy for transient failures only, with the same
    # independent outcomes. No arbitrary fixed recovery-rate multiplier.
    baseline_candidates = [
        r for r in eligible
        if r['failure_reason'] in ('temporary_bank_error', 'network_timeout')
    ]
    baseline_recovered = sum(r['amount'] * outcomes[r['id']] for r in baseline_candidates)
    eligible_revenue = sum(r['amount'] for r in eligible)
    qualified_revenue = sum(r['amount'] for r in qualified)
    lift = ((strategy_recovered - baseline_recovered) / baseline_recovered * 100) if baseline_recovered else 0

    return {
        'batch_size': len(rows),
        'evaluation_eligible_events': len(eligible),
        'revenue_at_risk': round(sum(r['amount'] for r in rows), 2),
        'eligible_revenue': round(eligible_revenue, 2),
        'qualified_events': len(qualified),
        'qualified_recoverable_revenue': round(qualified_revenue, 2),
        'actual_recovered_revenue': round(strategy_recovered, 2),
        'expected_recovered_revenue': round(strategy_recovered, 2),
        'baseline_expected_revenue': round(baseline_recovered, 2),
        'recovery_lift_pct': round(lift, 1),
        'evaluation_note': 'Synthetic held-out-style outcomes generated independently from model predictions; not production performance.',
        'ml': METRICS
    }
