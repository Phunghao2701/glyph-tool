(function(){
  "use strict";
  var nonce = window.__FV_NONCE;
  var revisionId = window.__FV_REVISION_ID;
  var edits = window.__FV_INITIAL_EDITS || [];
  var port = null;
  var queued = [];
  var pending = new Map();
  var serial = 0;

  function post(message) {
    var packet = Object.assign({ nonce: nonce }, message);
    if (port) port.postMessage(packet);
    else queued.push(packet);
  }
  function keyFor(edit) {
    return (edit.kind === "mark" ? "m-" : "g-") + edit.id;
  }
  window.__FV_BRIDGE = {
    dirty: function(key) { post({ type: "editor:dirty", key: key }); }
  };
  window.__FV_DB = {
    doc: function() {
      return { set: function(body) {
        return new Promise(function(resolve, reject) {
          var requestId = String(++serial) + "-" + Date.now();
          pending.set(requestId, { resolve: resolve, reject: reject });
          post({ type: "glyph:save", requestId: requestId, revisionId: revisionId, key: body.key, edit: body });
        });
      } };
    },
    collection: function() {
      return { get: function() {
        return Promise.resolve({ docs: edits.map(function(edit) {
          return { data: function() { return edit; } };
        }) });
      } };
    }
  };
  window.addEventListener("message", function(event) {
    if (event.source !== parent || !event.data || event.data.type !== "vfk:connect" ||
        event.data.nonce !== nonce || !event.ports || !event.ports[0]) return;
    port = event.ports[0];
    port.onmessage = function(messageEvent) {
      var data = messageEvent.data || {};
      if (data.nonce !== nonce) return;
      if (data.type === "glyph:save-result") {
        var waiter = pending.get(data.requestId);
        if (!waiter) return;
        pending.delete(data.requestId);
        if (data.ok) waiter.resolve(data);
        else waiter.reject(new Error(data.error || "Lưu glyph thất bại."));
      } else if (data.type === "flush" && data.requestId) {
        Promise.resolve(window.__edFlush()).then(function() {
          port.postMessage({ type: "flush:result", nonce: nonce, requestId: data.requestId, ok: true });
        }).catch(function(error) {
          port.postMessage({ type: "flush:result", nonce: nonce, requestId: data.requestId, ok: false, error: error.message });
        });
      }
    };
    port.start();
    queued.forEach(function(packet) { port.postMessage(packet); });
    queued = [];
  });
  parent.postMessage({ type: "vfk:frame-ready", nonce: nonce }, "*");
})();