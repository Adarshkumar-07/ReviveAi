import os, json

def reason(tx, probability):
    provider=os.getenv('LLM_PROVIDER','mock')
    if provider!='mock' and os.getenv('LLM_API_KEY'):
        # Provider adapter point: keep execution policy-controlled.
        # The default demo intentionally requires no paid API.
        pass
    r=tx['failure_reason']
    diagnosis={
      'temporary_bank_error':'Likely transient issuer/bank failure; a bounded retry is reasonable.',
      'network_timeout':'The payment response timed out; retry may succeed without changing the payment method.',
      'authentication_required':'Customer authentication is required before another attempt.',
      'insufficient_funds':'Immediate repeated retries are low-value; give the customer time and a payment link.',
      'expired_card':'The payment instrument is expired, so updating the payment method is safer than retrying.',
      'unknown':'The failure is ambiguous; keep execution gated for human review.'}.get(r,'Unknown failure.')
    action={'temporary_bank_error':'retry_payment','network_timeout':'retry_payment','authentication_required':'request_reauthentication','insufficient_funds':'send_payment_link_and_wait','expired_card':'request_payment_method_update','unknown':'human_review'}[r]
    return {'provider':'fallback','diagnosis':diagnosis,'recommended_action':action,'reasoning':[f'ML recovery probability: {probability:.0%}.',f'Failure class: {r}.','Final execution remains subject to deterministic policy.'],'customer_message':'We could not complete your payment. We have selected the safest next step to help complete it.','confidence':round(min(.98,max(.45,probability)),2)}
