// Minimal anti-cheat script. Sends focus events to server.
// Expects window.ANTICHEAT_CONTEXT = { result_id, test_id } to be set by page.

(function(){
  function sendEvent(type, extra){
    try{
      const ctx = window.ANTICHEAT_CONTEXT || {};
      if(!ctx.result_id) return;
      fetch('/test/' + ctx.test_id + '/save-focus/', {
        method:'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
          result_id: ctx.result_id,
          event_type: type,
          timestamp: new Date().toISOString(),
          extra: JSON.stringify(extra||{})
        }),
        credentials: 'same-origin'
      }).catch(()=>{});
    }catch(e){}
  }
  document.addEventListener('visibilitychange', function(){
    if(document.visibilityState !== 'visible'){
      sendEvent('visibility_hidden', {state: document.visibilityState});
    } else {
      sendEvent('visibility_visible', {state: document.visibilityState});
    }
  });
  window.addEventListener('blur', function(){ sendEvent('blur'); });
  window.addEventListener('focusout', function(){ sendEvent('focusout'); });
  window.addEventListener('pagehide', function(){ sendEvent('pagehide'); });
})();
