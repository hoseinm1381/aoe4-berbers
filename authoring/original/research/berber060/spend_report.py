"""Offline credit receipts and conservative budget, never an account invoice."""
import math,re
from common import OUT,read,write


def parse_credit(value):
    if isinstance(value,bool):raise ValueError('Boolean is not a character-credit count')
    try:cost=float(value)
    except (TypeError,ValueError,OverflowError):raise ValueError('Malformed character-credit count') from None
    if not math.isfinite(cost) or cost<0:raise ValueError('Character credits must be finite and nonnegative')
    return cost


def _unknown_attempt(reservation,evidence):
    if reservation.get('status') not in ('reserved_before_request','started','failed_or_unknown','rejected_or_unknown'):
        return False
    if not evidence:return True
    # Transport ambiguity remains unknown even if an incomplete response exposed
    # some headers. A saved complete response/quality rejection is a different case.
    if any('outcome unknown' in item.get('error','').lower() for item in evidence):return True
    for item in evidence:
        error=item.get('error','')
        if re.fullmatch(r'ElevenLabs HTTP (?:400|401|402|403|409|422|429); status=[A-Za-z0-9_]+',error):return False
        if error=='ElevenLabs preconnect DNS failure; request not transmitted':return False
        if item.get('request_transmission_proof',{}).get('request_body_transmitted') is False:return False
        if item.get('master_sha256') or item.get('source_sha256'):return False
        if item.get('provider_receipt'):return False
        if item.get('status') in ('response_received','accepted_acoustic','review_required'):return False
    return True


def build_report(budget,rows):
    """Pure accounting over supplied snapshots; no file or network mutations."""
    receipts={};conflicts=[];invalid=[];attempts={}
    for path,row in rows:
        if row.get('batch_id') and 'jobs' not in row:
            continue  # Member receipts duplicate the same batch provider charge.
        history=row.get('previous_attempts',[])+[row]
        for item in history:
            attempt=item.get('attempt_key') or item.get('batch_id') or item.get('request_id')
            if attempt:attempts.setdefault(attempt,[]).append(item)
            provider=item.get('provider_receipt') or {}
            cost=provider.get('character-cost')
            if cost is None:continue
            try:cost=parse_credit(cost)
            except ValueError as error:
                invalid.append({'evidence':str(path),'attempt_key':attempt,'reason':str(error)})
                continue
            key=provider.get('history-item-id') or provider.get('request-id') or item.get('attempt_key') or item.get('batch_id') or item.get('request_id')
            if not key:
                invalid.append({'evidence':str(path),'reason':'Credit header has no attributable request identity'})
                continue
            if key in receipts and receipts[key]['credits']!=cost:
                conflicts.append({'provider_request':key,'first':receipts[key]['credits'],'second':cost})
                continue  # Preserve first observed value; report incomplete evidence.
            receipts[key]={'credits':cost,'evidence':str(path)}
    reservations=budget['reservations']
    unknown=[{'attempt_key':key,'status':r.get('status')}
             for key,r in reservations.items() if _unknown_attempt(r,attempts.get(key,[]))]
    result={'schema':'berber060-credit-evidence/v1',
        'authorized_prepaid_cap_usd':budget['cap_usd'],
        'conservative_reserved_usd':round(sum(r['reserved_usd'] for r in reservations.values()),6),
        'provider_reported_character_credits':sum(r['credits'] for r in receipts.values()),
        'provider_receipts_with_credit_counts':len(receipts),'credit_receipt_conflicts':conflicts,
        'invalid_credit_receipts':invalid,'credit_evidence_complete':not (invalid or conflicts),
        'explicit_auth_refusal_reservations_released':sum(r.get('refused_request_estimate_usd',0) for r in reservations.values()),
        'account_balance':'Unavailable: user_read permission absent; human supplied $100 prepaid budget snapshot',
        'invoice_dollars_spent':'Unavailable: reported character credits are not an account invoice or live credit balance',
        'unknown_outcomes':len(unknown),'unknown_outcome_attempts':unknown,
        'unknown_outcome_basis':'Unique reserved attempts, excluding batch member duplicates; complete-response metadata and explicit refusals are known outcomes, not a live invoice',
        'provider_receipts':receipts}
    return result


def generate():
    budget=read(OUT/'budget.json')
    paths=list((OUT/'batches').glob('*/receipt.json'))+list((OUT/'receipts').glob('*.json'))
    result=build_report(budget,[(path,read(path)) for path in paths])
    write(OUT/'credit-usage.json',result)
    print({k:v for k,v in result.items() if k!='provider_receipts'});return result


if __name__=='__main__':generate()
