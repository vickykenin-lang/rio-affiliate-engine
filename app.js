(function(){
  'use strict';
  const STORAGE_KEY='rio_events';
  function safeRead(){
    try { const v=JSON.parse(localStorage.getItem(STORAGE_KEY)||'[]'); return Array.isArray(v)?v:[]; }
    catch (_) { return []; }
  }
  function trackOutboundClick(offerId,placement,status){
    const event={event:'affiliate_click_intent',offer_id:offerId||'unknown',placement:placement||'unknown',link_status:status||'unknown',timestamp:new Date().toISOString(),path:location.pathname};
    const prior=safeRead(); prior.push(event); if(prior.length>200) prior.splice(0,prior.length-200);
    try { localStorage.setItem(STORAGE_KEY,JSON.stringify(prior)); } catch (_) {}
    if(window.RIO_DEBUG) console.log('RIO event',event);
  }
  document.querySelectorAll('[data-offer]').forEach(function(el){
    el.addEventListener('click',function(e){
      const disabled=el.getAttribute('aria-disabled')==='true';
      if(disabled) e.preventDefault();
      trackOutboundClick(el.dataset.offer,el.dataset.placement,disabled?'pending':'active');
    });
  });

  // Real Amazon product images are primary. Local RIO cards are emergency
  // fallbacks only, so a temporary media-host failure never leaves a blank card.
  document.querySelectorAll('img[data-fallback-src]').forEach(function(img){
    img.addEventListener('error',function(){
      if(img.dataset.fallbackApplied==='true') return;
      img.dataset.fallbackApplied='true';
      img.src=img.dataset.fallbackSrc;
    });
  });

  // Sticky mobile "buy" bar: mirrors the first real, already-verified offer
  // link on an article page so mobile readers always have the CTA in view.
  // Purely presentational — clones the existing <a>, adds no new data.
  (function stickyCta(){
    var mainBtn = document.querySelector('article .card [data-offer]');
    if(!mainBtn) return;
    var bar = document.createElement('div');
    bar.className = 'rio-sticky-cta';
    var link = mainBtn.cloneNode(true);
    link.removeAttribute('id');
    bar.appendChild(link);
    document.body.appendChild(bar);
    link.addEventListener('click', function(e){
      var disabled = link.getAttribute('aria-disabled') === 'true';
      if (disabled) e.preventDefault();
      trackOutboundClick(link.dataset.offer, (link.dataset.placement||'')+'_sticky', disabled ? 'pending' : 'active');
    });
    function toggle(){
      var rect = mainBtn.getBoundingClientRect();
      var offscreen = rect.bottom < 0 || rect.top > (window.innerHeight || document.documentElement.clientHeight);
      bar.classList.toggle('is-active', offscreen);
    }
    toggle();
    window.addEventListener('scroll', toggle, {passive:true});
    window.addEventListener('resize', toggle);
  })();
})();
