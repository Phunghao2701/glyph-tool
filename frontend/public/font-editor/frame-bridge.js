(function(){
  "use strict";
  var nonce = window.__FV_NONCE;
  var revisionId = window.__FV_REVISION_ID;
  var edits = window.__FV_INITIAL_EDITS || [];
  var localeResources = {};
  try { localeResources = JSON.parse(document.getElementById("editor-i18n").textContent || "{}"); } catch (e) {}
  var locale = "vi";
  function message(key, values) {
    var value = (localeResources[locale] || localeResources.vi || {});
    String(key).split(".").forEach(function(part) { value = value && value[part]; });
    if (typeof value !== "string") return key;
    Object.keys(values || {}).forEach(function(name) { value = value.replace(new RegExp("{{\\s*" + name + "\\s*}}", "g"), String(values[name])); });
    return value;
  }
  function applyLocale(initial) {
    document.documentElement.lang = locale;
    var bindings = [
      [".ed-bar", "aria-label", "toolbar"], ["[data-tool=select]", "title", "select"], ["[data-tool=select]", "aria-label", "selectLabel"],
      [".ed-pgb", "title", "penGroupTitle"], [".ed-pgb", "aria-label", "penGroup"], [".ed-pgf", "aria-label", "penGroup"],
      [".ed-pgf [data-tool=pen]", "title", "penTitle"], [".ed-pgf [data-tool=addpt]", "title", "addAnchorTitle"],
      [".ed-pgf [data-tool=delpt]", "title", "deleteAnchorTitle"], [".ed-pgf [data-tool=convert]", "title", "convertTitle"],
      ["[data-tool=brush]", "title", "brushTitle"], ["[data-tool=brush]", "aria-label", "brush"],
      ["[data-tool=comp]", "title", "componentTitle"], ["[data-tool=comp]", "aria-label", "component"],
      ["[data-ed=undo]", "title", "undo"], ["[data-ed=undo]", "aria-label", "undo"], ["[data-ed=redo]", "title", "redo"], ["[data-ed=redo]", "aria-label", "redo"],
      ["[data-tool=hand]", "title", "pan"], ["[data-tool=hand]", "aria-label", "pan"], ["[data-ed=zin]", "title", "zoomIn"], ["[data-ed=zin]", "aria-label", "zoomIn"],
      ["[data-ed=zout]", "title", "zoomOut"], ["[data-ed=zout]", "aria-label", "zoomOut"], ["[data-ed=fit]", "title", "fit"], ["[data-ed=fit]", "aria-label", "fit"],
      ["[data-ed=reset]", "title", "resetTitle"], ["[data-ed=reset]", "aria-label", "reset"], [".ed-cv", "aria-label", "drawing"],
      [".ed-opts", "aria-label", "viewOptions"], ["[data-opt=grid]", "title", "grid"], ["[data-opt=grid]", "aria-label", "grid"], ["[data-opt=grid] span", "text", "grid"],
      ["[data-opt=rulers]", "title", "rulers"], ["[data-opt=rulers]", "aria-label", "rulers"], ["[data-opt=metrics]", "title", "metrics"], ["[data-opt=metrics]", "aria-label", "metrics"],
      ["[data-opt=rulers] span", "text", "rulers"], ["[data-opt=metrics] span", "text", "baseline"],
      ["[data-opt=orig]", "title", "original"], ["[data-opt=orig]", "aria-label", "original"], ["[data-opt=orig] span", "text", "original"], ["[data-opt=adv]", "title", "advance"], ["[data-opt=adv]", "aria-label", "advance"], ["[data-opt=adv] span", "text", "advance"],
      ["[data-opt=lbox]", "title", "lineBox"], ["[data-opt=lbox]", "aria-label", "lineBox"], ["[data-opt=lbox] span", "text", "lineBox"], ["[data-opt=axis]", "title", "axis"], ["[data-opt=axis]", "aria-label", "axis"], ["[data-opt=axis] span", "text", "axis"],
      ["[data-opt=nodes]", "title", "nodes"], ["[data-opt=nodes]", "aria-label", "nodes"], ["[data-opt=nodes] span", "text", "nodes"], ["[data-opt=snap]", "title", "snap"], ["[data-opt=snap]", "aria-label", "snap"], ["[data-opt=snap] span", "text", "snap"],
      [".ed-resetc [data-a=yes]", "text", "resetConfirm"], [".ed-resetc [data-a=no]", "text", "nevermind"],
      [".ed-side .ed-tabs", "aria-label", "groupChars"], ["#ed-find", "placeholder", "search"], ["#ed-find", "aria-label", "find"],
      ["label[for=ed-note]", "text", "note"], ["#ed-note", "placeholder", "notePlaceholder"], ["label[for=ed-pvtext]", "text", "sample"],
      [".ed-pvh b", "text", "preview"], [".ed-pv svg", "aria-label", "preview"], [".ed-pvin .ed-notel", "text", "sample"], [".ed-whyd summary", "text", "whySummary"], [".ed-resetc #ed-rct", "text", "resetQuestion"],
      [".ed-resetc #ed-rcd", "text", "resetDescription"], ["label[for=ed-bw]", "text", "brushWidth"],
      [".ed-brushrow .mini", "text", "fontUnits"], [".ed-tabs [data-tab=vn]", "text", "vietnameseChars"], [".ed-tabs [data-tab=marks]", "text", "marks"],
      [".ed-tabs [data-tab=latin]", "text", "latin"], [".ed-pg [data-tool=pen] span", "text", "pen"], [".ed-pg [data-tool=addpt] span", "text", "addAnchor"],
      [".ed-pg [data-tool=delpt] span", "text", "deleteAnchor"], [".ed-pg [data-tool=convert] span", "text", "convert"],
      ["#ed-pvtext", "aria-label", "sample"],
    ];
    bindings.forEach(function(binding) {
      var element = document.querySelector(binding[0]);
      if (!element) return;
      if (binding[1] === "text") element.textContent = message(binding[2]);
      else element.setAttribute(binding[1], message(binding[2]));
    });
    if (initial) { var saveStatus = document.querySelector(".ed-save"); if (saveStatus) saveStatus.textContent = message("connecting"); }
    if (typeof window.__edSetLocale === "function") window.__edSetLocale(locale);
  }
  window.__FV_T = message;
  var firstLocale = true;
  window.__FV_SET_LOCALE = function(language) {
    locale = String(language || "vi").toLowerCase().indexOf("en") === 0 ? "en" : "vi";
    window.__FV_LOCALE = locale;
    applyLocale(firstLocale);
    firstLocale = false;
  };
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
      if (data.type === "editor:locale") {
        window.__FV_SET_LOCALE(data.language);
      } else if (data.type === "glyph:save-result") {
        var waiter = pending.get(data.requestId);
        if (!waiter) return;
        pending.delete(data.requestId);
        if (data.ok) waiter.resolve(data);
        else waiter.reject(new Error(data.error || message("saveFailed")));
      } else if (data.type === "flush" && data.requestId) {
        Promise.resolve(window.__edFlush()).then(function() {
          port.postMessage({ type: "flush:result", nonce: nonce, requestId: data.requestId, ok: true });
        }).catch(function(error) {
          port.postMessage({ type: "flush:result", nonce: nonce, requestId: data.requestId, ok: false, error: error.message });
        });
      }
    };
    port.start();
    window.__FV_SET_LOCALE(event.data.language);
    queued.forEach(function(packet) { port.postMessage(packet); });
    queued = [];
  });
  parent.postMessage({ type: "vfk:frame-ready", nonce: nonce }, "*");
})();
