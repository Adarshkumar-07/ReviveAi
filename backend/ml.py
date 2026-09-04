import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from .db import get_transactions

MODEL=None
METRICS={}

def features(rows):
    reason={k:i for i,k in enumerate(['temporary_bank_error','insufficient_funds','authentication_required','network_timeout','expired_card','unknown'])}
    method={k:i for i,k in enumerate(['card','upi','netbanking','wallet'])}
    return np.array([[r['amount']/25000, r['attempts']/4, reason.get(r['failure_reason'],5)/5, method.get(r['payment_method'],0)/3, r['customer_age_days']/1200, r['historical_success_rate'], r['prior_failures_30d']/4, r['minutes_since_failure']/720, r['subscription']] for r in rows],dtype=float)

def latent_probability(r):
    p=.18 + .48*r['historical_success_rate']
    if r['failure_reason'] in ('temporary_bank_error','network_timeout'): p+=.20
    if r['failure_reason']=='authentication_required': p+=.03
    if r['failure_reason']=='insufficient_funds': p-=.08
    if r['failure_reason']=='expired_card': p-=.20
    p-=.12*max(0,r['attempts']-1); p-=.04*r['prior_failures_30d']; p-=.000003*r['amount']
    return max(.02,min(.96,p))

def train():
    global MODEL,METRICS
    rows=get_transactions(5000)
    if len(rows)<50: return
    y=np.array([int(np.random.RandomState(1000+i).random()<latent_probability(r)) for i,r in enumerate(rows)])
    X=features(rows)
    Xtr,Xtmp,ytr,ytmp=train_test_split(X,y,test_size=.30,random_state=42,stratify=y)
    Xv,Xte,yv,yte=train_test_split(Xtmp,ytmp,test_size=.50,random_state=42,stratify=ytmp)
    MODEL=RandomForestClassifier(n_estimators=180,max_depth=8,min_samples_leaf=3,class_weight='balanced',random_state=42,n_jobs=-1)
    MODEL.fit(Xtr,ytr)
    pv=MODEL.predict_proba(Xv)[:,1]
    thresholds=np.arange(.25,.76,.05)
    threshold=max(thresholds,key=lambda t:f1_score(yv,(pv>=t).astype(int),zero_division=0))
    pt=MODEL.predict_proba(Xte)[:,1]; pred=(pt>=threshold).astype(int)
    METRICS={'roc_auc':round(roc_auc_score(yte,pt),3),'precision':round(precision_score(yte,pred,zero_division=0),3),'recall':round(recall_score(yte,pred,zero_division=0),3),'f1':round(f1_score(yte,pred,zero_division=0),3),'threshold':round(float(threshold),2),'split':'70% train / 15% validation / 15% held-out test'}

def predict(r):
    global MODEL
    if MODEL is None: train()
    if MODEL is None: return .5
    return float(MODEL.predict_proba(features([r]))[0,1])
