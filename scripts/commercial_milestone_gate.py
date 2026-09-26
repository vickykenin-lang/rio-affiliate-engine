#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M0 = ROOT / 'data/revenue_m0_live_probe.json'
ATTR = ROOT / 'data/affiliate_attribution_state.json'
OUT = ROOT / 'data/commercial_milestone_state.json'


def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def positive(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0


def main() -> int:
    m0 = load(M0, {})
    attr = load(ATTR, {})

    click_collection = m0.get('outbound_click_event_collection_verified') is True
    real_click = m0.get('real_outbound_click_observed') is True
    source_imported = attr.get('status') == 'AFFILIATE_SOURCE_IMPORTED'
    orders = attr.get('orders')
    commission = attr.get('commission_inr')
    settled = attr.get('settled_revenue_inr')

    stage = 'PRE_M0B'
    if click_collection:
        stage = 'M0B_CLICK_COLLECTION_PATH_VERIFIED'
    if click_collection and real_click:
        stage = 'M0C_REAL_OUTBOUND_CLICK_OBSERVED'
    if source_imported and positive(orders):
        stage = 'M1_MERCHANT_REPORTED_QUALIFYING_ORDER'
    if source_imported and positive(commission):
        stage = 'M2_APPROVED_COMMISSION'
    if source_imported and positive(settled):
        stage = 'M3_SETTLED_INR_GT_0'

    result = {
        'schema_version': 1,
        'checked_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': stage,
        'evidence': {
            'm0_probe_present': bool(m0),
            'outbound_click_event_collection_verified': click_collection,
            'real_outbound_click_observed': real_click,
            'affiliate_source_imported': source_imported,
            'orders': orders,
            'commission_inr': commission,
            'settled_revenue_inr': settled,
            'source': attr.get('source'),
            'source_reference': attr.get('source_reference'),
            'evidence_sha256': attr.get('evidence_sha256'),
        },
        'gates': {
            'M0B': click_collection,
            'M0C': click_collection and real_click,
            'M1': source_imported and positive(orders),
            'M2': source_imported and positive(commission),
            'M3': source_imported and positive(settled),
        },
        'revenue_claim_allowed': source_imported and positive(settled),
        'truth_rule': 'Click collection is not revenue. M1/M2/M3 require imported traceable merchant or affiliate-source evidence; missing or null evidence remains UNKNOWN.',
    }
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
