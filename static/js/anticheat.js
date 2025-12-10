

(function(){
  function focusSuppressed(){
    try{
      return !!window.ANTICHEAT_SUPPRESS_FOCUS || (!!window.parent && window.parent !== window && !!window.parent.ANTICHEAT_SUPPRESS_FOCUS);
    }catch(e){
      return !!window.ANTICHEAT_SUPPRESS_FOCUS;
    }
  }

  function isPageVisible(){
    try{
      return document.visibilityState === 'visible';
    }catch(e){
      return true;
    }
  }

  function pageHasFocus(){
    try{
      return typeof document.hasFocus === 'function' ? document.hasFocus() : true;
    }catch(e){
      return true;
    }
  }

  function sendEvent(type, extra){
    try{
      if (focusSuppressed()) return;
      if (type === 'blur' || type === 'focusout') {
        if (isPageVisible()) {
          // If the page is visible but the window lost focus (e.g., user switched windows), count it
          if (pageHasFocus()) {
            // Still focused inside the page — ignore
            return;
          }
        }
      }
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
