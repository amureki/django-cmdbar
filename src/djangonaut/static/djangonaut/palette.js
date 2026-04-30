(function () {
  "use strict";

  const script = document.currentScript;
  const endpoint = script?.dataset.endpoint || "/djangonaut/commands/";

  const host = document.createElement("djangonaut-palette");
  host.setAttribute("data-open", "false");
  const root = host.attachShadow({ mode: "open" });

  root.innerHTML = `
    <style>
      :host {
        all: initial;
        position: fixed; inset: 0;
        z-index: 2147483000;
        pointer-events: none;
      }
      :host([data-open="true"]) { pointer-events: auto; }
      .backdrop {
        position: fixed; inset: 0;
        background: rgba(15, 15, 20, 0.45);
        backdrop-filter: blur(2px);
        display: none;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      }
      :host([data-open="true"]) .backdrop { display: block; }
      .panel {
        position: absolute;
        top: 15vh; left: 50%; transform: translateX(-50%);
        width: min(640px, 92vw);
        background: #fff; color: #111;
        border-radius: 12px;
        box-shadow: 0 24px 64px rgba(0,0,0,0.35);
        overflow: hidden;
      }
      input {
        width: 100%; box-sizing: border-box;
        padding: 16px 18px; border: 0;
        font-size: 16px; outline: none;
        border-bottom: 1px solid #eee;
      }
      ul { list-style: none; margin: 0; padding: 6px 0; max-height: 50vh; overflow-y: auto; }
      li {
        padding: 10px 18px;
        display: flex; align-items: center; gap: 10px;
        cursor: pointer;
      }
      li[aria-selected="true"] { background: #f2f4ff; }
      .label { font-weight: 500; }
      .hint { color: #777; font-size: 12px; margin-left: auto; }
      .empty { padding: 18px; color: #888; font-size: 13px; }
      @media (prefers-color-scheme: dark) {
        .panel { background: #1e1e22; color: #eee; }
        input { background: #1e1e22; color: #eee; border-bottom-color: #333; }
        li[aria-selected="true"] { background: #2a2b33; }
        .hint { color: #999; }
      }
    </style>
    <div class="backdrop">
      <div class="panel" role="dialog" aria-label="Djangonaut palette">
        <input type="text" placeholder="Jump to… (model, model rick, model #42, model +, @app)" autocomplete="off" />
        <ul role="listbox"></ul>
        <div class="empty" hidden>No matches.</div>
      </div>
    </div>
  `;

  const backdrop = root.querySelector(".backdrop");
  const input = root.querySelector("input");
  const list = root.querySelector("ul");
  const empty = root.querySelector(".empty");

  let results = [];
  let selected = 0;
  let fetchTimer = null;
  let lastToken = 0;

  function open() {
    host.setAttribute("data-open", "true");
    input.value = "";
    results = [];
    render();
    input.focus();
    refresh("");
  }

  function close() {
    host.setAttribute("data-open", "false");
  }

  function isOpen() {
    return host.getAttribute("data-open") === "true";
  }

  function render() {
    list.innerHTML = "";
    if (!results.length) {
      empty.hidden = false;
      return;
    }
    empty.hidden = true;
    results.forEach((r, i) => {
      const li = document.createElement("li");
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", i === selected ? "true" : "false");
      li.innerHTML = `<span class="label"></span><span class="hint"></span>`;
      li.querySelector(".label").textContent = r.label;
      li.querySelector(".hint").textContent = r.hint || "";
      li.addEventListener("click", (e) => choose(i, e.metaKey || e.ctrlKey));
      list.appendChild(li);
    });
  }

  function choose(i, newTab) {
    const r = results[i];
    if (!r) return;
    if (newTab) {
      window.open(r.url, "_blank");
    } else {
      window.location.href = r.url;
    }
    close();
  }

  function refresh(q) {
    clearTimeout(fetchTimer);
    fetchTimer = setTimeout(() => {
      const token = ++lastToken;
      const url = endpoint + "?q=" + encodeURIComponent(q);
      fetch(url, { credentials: "same-origin", headers: { Accept: "application/json" } })
        .then((r) => (r.ok ? r.json() : { results: [] }))
        .then((data) => {
          if (token !== lastToken) return;
          results = data.results || [];
          selected = 0;
          render();
        })
        .catch(() => {});
    }, 80);
  }

  input.addEventListener("input", () => refresh(input.value));
  input.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { close(); return; }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (results.length) { selected = (selected + 1) % results.length; render(); }
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (results.length) { selected = (selected - 1 + results.length) % results.length; render(); }
    } else if (e.key === "Enter") {
      e.preventDefault();
      choose(selected, e.metaKey || e.ctrlKey);
    }
  });

  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) close();
  });

  window.addEventListener("keydown", (e) => {
    const mod = e.metaKey || e.ctrlKey;
    if (mod && e.key.toLowerCase() === "k") {
      e.preventDefault();
      isOpen() ? close() : open();
    }
  });

  function mount() { document.body.appendChild(host); }
  if (document.body) mount();
  else document.addEventListener("DOMContentLoaded", mount);
})();
