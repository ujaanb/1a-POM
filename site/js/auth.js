/**
 * Client-side login gate for the POM Study Hub.
 * Credentials are not persisted; every navigation re-prompts.
 */
(function () {
  "use strict";

  var USER_HASH = "08fb13e4";
  var PASS_HASH = "a4a0c769";
  var GATE_ID = "pom-auth-gate";
  var STYLE_ID = "pom-auth-style";
  var LOCK_CLASS = "pom-auth-locked";

  function shortHash(value) {
    var h = 2166136261;
    var data = "pom1a|" + value;
    for (var i = 0; i < data.length; i++) {
      h ^= data.charCodeAt(i);
      h = Math.imul(h, 16777619) >>> 0;
    }
    var hex = h.toString(16);
    return ("00000000" + hex).slice(-8);
  }

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = [
      "html." + LOCK_CLASS + ",html." + LOCK_CLASS + " body{",
      "margin:0!important;min-height:100vh!important;width:100%!important;overflow:hidden!important;",
      "}",
      "html." + LOCK_CLASS + " body>*:not(#" + GATE_ID + "){",
      "display:none!important;",
      "}",
      "#" + GATE_ID + "{",
      "position:fixed!important;top:0!important;left:0!important;right:0!important;bottom:0!important;",
      "width:100vw!important;height:100vh!important;max-width:none!important;margin:0!important;",
      "z-index:2147483647!important;display:flex!important;align-items:center!important;justify-content:center!important;",
      "padding:1.5rem!important;box-sizing:border-box!important;",
      "background:radial-gradient(1200px 600px at 10% -10%,#c8ebe9 0%,transparent 55%),",
      "radial-gradient(900px 500px at 100% 0%,#f8d9cf 0%,transparent 45%),",
      "linear-gradient(180deg,#eef4f6 0%,#f2f6f8 40%,#e8f0f2 100%)!important;",
      "font-family:'DM Sans',sans-serif!important;color:#0c1f2e!important;",
      "}",
      "#" + GATE_ID + " .pom-auth-card{",
      "width:22rem!important;max-width:100%!important;background:#fff!important;border:1px solid #d0dde6!important;",
      "border-radius:14px!important;box-shadow:0 12px 40px rgba(12,31,46,.08)!important;",
      "padding:1.75rem 1.5rem 1.5rem!important;box-sizing:border-box!important;",
      "}",
      "#" + GATE_ID + " .pom-auth-brand{",
      "font-family:'Fraunces',Georgia,serif!important;font-weight:700!important;font-size:1.35rem!important;",
      "margin:0 0 .25rem!important;color:#0e7c7b!important;",
      "}",
      "#" + GATE_ID + " .pom-auth-lead{",
      "margin:0 0 1.25rem!important;font-size:.92rem!important;color:#5a7385!important;line-height:1.45!important;",
      "}",
      "#" + GATE_ID + " label{",
      "display:block!important;font-size:.78rem!important;font-weight:600!important;letter-spacing:.02em!important;",
      "text-transform:uppercase!important;color:#243b4a!important;margin:0 0 .35rem!important;",
      "}",
      "#" + GATE_ID + " .pom-auth-field{margin:0 0 .9rem!important;}",
      "#" + GATE_ID + " input{",
      "width:100%!important;box-sizing:border-box!important;border:1px solid #d0dde6!important;border-radius:10px!important;",
      "padding:.7rem .85rem!important;font:inherit!important;font-size:1rem!important;color:#0c1f2e!important;background:#f2f6f8!important;",
      "}",
      "#" + GATE_ID + " input:focus{outline:2px solid #0e7c7b!important;outline-offset:1px!important;background:#fff!important;}",
      "#" + GATE_ID + " button{",
      "width:100%!important;margin-top:.35rem!important;border:0!important;border-radius:10px!important;",
      "padding:.75rem 1rem!important;cursor:pointer!important;font:inherit!important;font-weight:600!important;",
      "font-size:.95rem!important;color:#fff!important;background:#0e7c7b!important;",
      "}",
      "#" + GATE_ID + " button:hover{background:#095958!important;}",
      "#" + GATE_ID + " .pom-auth-error{",
      "display:none!important;margin:.85rem 0 0!important;padding:.65rem .75rem!important;border-radius:10px!important;",
      "background:#fdecea!important;color:#c44536!important;font-size:.88rem!important;line-height:1.4!important;",
      "}",
      "#" + GATE_ID + " .pom-auth-error.is-visible{display:block!important;}",
    ].join("");
    (document.head || document.documentElement).appendChild(style);
  }

  function lock() {
    document.documentElement.classList.add(LOCK_CLASS);
  }

  function unlock() {
    document.documentElement.classList.remove(LOCK_CLASS);
    var gate = document.getElementById(GATE_ID);
    if (gate && gate.parentNode) gate.parentNode.removeChild(gate);
  }

  function showError(el) {
    if (!el) return;
    el.textContent = "Incorrect username or password.";
    el.classList.add("is-visible");
  }

  function buildGate() {
    if (document.getElementById(GATE_ID)) return;

    var gate = document.createElement("div");
    gate.id = GATE_ID;
    gate.setAttribute("role", "dialog");
    gate.setAttribute("aria-modal", "true");
    gate.setAttribute("aria-labelledby", "pom-auth-title");

    gate.innerHTML =
      '<div class="pom-auth-card">' +
      '<p class="pom-auth-brand" id="pom-auth-title">POM Study Hub</p>' +
      '<p class="pom-auth-lead">Enter your credentials to continue.</p>' +
      '<form id="pom-auth-form" autocomplete="off">' +
      '<div class="pom-auth-field"><label for="pom-auth-user">Username</label>' +
      '<input id="pom-auth-user" name="username" type="text" autocomplete="username" autofocus /></div>' +
      '<div class="pom-auth-field"><label for="pom-auth-pass">Password</label>' +
      '<input id="pom-auth-pass" name="password" type="password" autocomplete="current-password" /></div>' +
      '<button type="submit">Sign in</button>' +
      '<p class="pom-auth-error" id="pom-auth-error" role="alert"></p>' +
      "</form></div>";

    document.body.appendChild(gate);

    var form = document.getElementById("pom-auth-form");
    var userInput = document.getElementById("pom-auth-user");
    var passInput = document.getElementById("pom-auth-pass");
    var errorEl = document.getElementById("pom-auth-error");

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var user = String(userInput.value || "")
        .trim()
        .toLowerCase();
      var pass = String(passInput.value || "");
      if (shortHash(user) === USER_HASH && shortHash(pass) === PASS_HASH) {
        unlock();
        return;
      }
      showError(errorEl);
      passInput.value = "";
      passInput.focus();
    });

    if (userInput && typeof userInput.focus === "function") {
      try {
        userInput.focus();
      } catch (e) {
        /* ignore */
      }
    }
  }

  function boot() {
    injectStyles();
    lock();
    if (document.body) {
      buildGate();
    } else {
      document.addEventListener("DOMContentLoaded", buildGate);
    }
  }

  window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
      window.location.reload();
    }
  });

  boot();
})();
