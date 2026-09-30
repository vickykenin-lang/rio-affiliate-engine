(() => {
  'use strict';
  const COLLECTOR = 'https://rio-click-telemetry.vickykenin.workers.dev/click';

  function offerIdFor(anchor) {
    const card = anchor.closest('[data-offer-id]');
    if (card && card.dataset.offerId) return card.dataset.offerId;
    const match = location.pathname.match(/\/products\/([A-Z0-9_]+)\.html$/i);
    return match ? match[1].toUpperCase() : '';
  }

  document.addEventListener('click', (event) => {
    const anchor = event.target.closest('a[href]');
    if (!anchor) return;
    const target = anchor.href || '';
    if (!target.includes('amazon.in/') || !target.includes('tag=rioaffiliate-21')) return;
    const offerId = offerIdFor(anchor);
    if (!offerId) return;
    const payload = JSON.stringify({offer_id: offerId, path: location.pathname, target});
    fetch(COLLECTOR, {
      method: 'POST',
      headers: {'content-type': 'application/json'},
      body: payload,
      keepalive: true,
      credentials: 'omit'
    }).catch(() => {});
  }, {capture: true});
})();
