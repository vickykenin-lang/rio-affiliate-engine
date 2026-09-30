(() => {
  const endpoint = 'https://rio-click-telemetry.vickykenin.workers.dev/click';
  const file = (location.pathname.split('/').pop() || '').replace(/\.html$/i, '');
  const allowed = new Set(['SPICE_RACK_001', 'UNDER_SINK_001', 'TROLLEY_001']);
  if (!allowed.has(file)) return;

  document.addEventListener('click', (event) => {
    const link = event.target && event.target.closest ? event.target.closest('a[href]') : null;
    if (!link) return;
    const target = link.href || '';
    if (!target.includes('amazon.in/') || !target.includes('tag=rioaffiliate-21')) return;

    const payload = JSON.stringify({
      offer_id: file,
      path: location.pathname,
      target
    });

    try {
      if (navigator.sendBeacon) {
        const blob = new Blob([payload], { type: 'application/json' });
        if (navigator.sendBeacon(endpoint, blob)) return;
      }
      fetch(endpoint, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: payload,
        keepalive: true,
        mode: 'cors',
        credentials: 'omit'
      }).catch(() => {});
    } catch (_) {
      // Telemetry must never block the affiliate destination.
    }
  }, { capture: true });
})();
