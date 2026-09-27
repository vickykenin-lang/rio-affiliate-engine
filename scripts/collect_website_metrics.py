#!/usr/bin/env python3
"""Import privacy-safe website affiliate click counts from the RIO Cloudflare Worker.

This collector records only aggregate/event counts returned by the named RIO
collector. It never converts missing telemetry into zero and never treats a click
as proof of an order or commission.
"""
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'telemetry_state.json'
SUMMARY_URL = 'https://rio-click-telemetry.vickykenin.workers.dev/summary'
HEALTH_URL = 'https://rio-click-telemetry.vickykenin.workers.dev/health'


def load(path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'RIO-Telemetry-Collector/1.0'})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


def main():
    state = load(OUT, {})
    state.update({'schema_version': 1, 'policy': 'UNKNOWN_IS_NOT_ZERO'})
    website = state.setdefault('website', {})
    now = datetime.now(timezone.utc).isoformat()
    try:
        health = fetch_json(HEALTH_URL)
        summary = fetch_json(SUMMARY_URL)
        if health.get('status') != 'READY' or summary.get('status') != 'LIVE':
            raise RuntimeError('collector did not return READY/LIVE')
        clicks = summary.get('retained_click_events')
        if not isinstance(clicks, int) or isinstance(clicks, bool) or clicks < 0:
            raise RuntimeError('collector click count is not a valid non-negative integer')
        website.update({
            'click_collector': 'cloudflare:rio-click-telemetry',
            'collector_url': SUMMARY_URL,
            'collector_version': summary.get('version'),
            'status': 'LIVE',
            'clicks': clicks,
            'sessions': None,
            'source': 'RIO_CLICK_TELEMETRY',
            'by_offer': summary.get('by_offer') or {},
            'list_complete': summary.get('list_complete'),
            'retention_days': summary.get('retention_days'),
            'last_success_at_utc': now,
            'last_attempt_at_utc': now,
            'truth_rule': 'Measured collector events are clicks only; they do not prove merchant orders or commission. Sessions remain UNKNOWN.'
        })
        state['status'] = 'TELEMETRY_PARTIAL' if state.get('instagram', {}).get('last_success_at_utc') is None else 'TELEMETRY_LIVE'
        state.setdefault('decision_guard', {})['allow_no_click_decision'] = False
        state['decision_guard']['rule'] = 'Numeric website clicks are measured collector events. Null/unknown remains unknown. No-click decisions require an explicit observation window and complete collector coverage.'
        OUT.write_text(json.dumps(state, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print(json.dumps({'website_clicks': clicks, 'collector': 'LIVE', 'version': summary.get('version')}))
        return 0
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError, ValueError, OSError) as exc:
        website.update({
            'click_collector': 'cloudflare:rio-click-telemetry',
            'collector_url': SUMMARY_URL,
            'status': 'COLLECTOR_UNAVAILABLE',
            'clicks': None,
            'sessions': None,
            'source': 'RIO_CLICK_TELEMETRY',
            'last_attempt_at_utc': now,
            'collector_error': type(exc).__name__,
            'truth_rule': 'Collector failure means website click telemetry is UNKNOWN, never zero.'
        })
        OUT.write_text(json.dumps(state, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print('website telemetry unavailable:', type(exc).__name__)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
