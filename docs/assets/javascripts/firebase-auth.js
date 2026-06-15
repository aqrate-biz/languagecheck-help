(function () {
  const cfg = Object.assign(
    {},
    window.LANGUAGECHECK_FIREBASE_CONFIG || {},
    window.LANGUAGECHECK_FIREBASE_CONFIG_OVERRIDES || {},
  );
  const opts = window.LANGUAGECHECK_FIREBASE_AUTH || {};

  function hasFirebaseConfig(config) {
    return Boolean(
      config.apiKey && config.authDomain && config.projectId && config.appId,
    );
  }

  function isFirebaseReady() {
    return typeof window.firebase !== "undefined";
  }

  function setStatus(statusEl, message, kind) {
    statusEl.textContent = message;
    statusEl.className = "lc-auth-status";
    if (kind) {
      statusEl.classList.add("lc-auth-status-" + kind);
    }
  }

  function createUi() {
    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "lc-auth-trigger";
    trigger.textContent = "Sign in";

    const headerSlot = document.createElement("div");
    headerSlot.className = "lc-auth-header-slot";
    headerSlot.appendChild(trigger);

    const panel = document.createElement("div");
    panel.className = "lc-auth-panel";
    panel.hidden = true;

    panel.innerHTML = [
      '<h3 class="lc-auth-title">Developer Sign In</h3>',
      '<div class="lc-auth-line">',
      '<label class="lc-auth-label" for="lc-auth-email">Email</label>',
      '<input class="lc-auth-input" id="lc-auth-email" type="email" placeholder="name@example.com" autocomplete="username" />',
      "</div>",
      '<div class="lc-auth-line">',
      '<label class="lc-auth-label" for="lc-auth-password">Password</label>',
      '<input class="lc-auth-input" id="lc-auth-password" type="password" placeholder="Password" autocomplete="current-password" />',
      "</div>",
      '<div class="lc-auth-actions">',
      '<button class="lc-auth-btn lc-auth-btn-primary" type="button" id="lc-auth-email-signin">Sign in with email</button>',
      '<button class="lc-auth-btn lc-auth-btn-secondary" type="button" id="lc-auth-google">Continue with Google</button>',
      '<button class="lc-auth-btn lc-auth-btn-secondary" type="button" id="lc-auth-signout">Sign out</button>',
      "</div>",
      '<div class="lc-auth-user" id="lc-auth-user">Not signed in</div>',
      '<div class="lc-auth-status" id="lc-auth-status">Ready</div>',
    ].join("");

    const headerInner = document.querySelector(".md-header__inner");
    if (headerInner) {
      headerInner.appendChild(headerSlot);
    } else {
      document.body.appendChild(trigger);
    }
    document.body.appendChild(panel);

    return {
      trigger,
      panel,
      emailInput: panel.querySelector("#lc-auth-email"),
      passwordInput: panel.querySelector("#lc-auth-password"),
      emailSignInBtn: panel.querySelector("#lc-auth-email-signin"),
      googleBtn: panel.querySelector("#lc-auth-google"),
      signOutBtn: panel.querySelector("#lc-auth-signout"),
      userEl: panel.querySelector("#lc-auth-user"),
      statusEl: panel.querySelector("#lc-auth-status"),
    };
  }

  function setup() {
    if (!hasFirebaseConfig(cfg)) {
      return;
    }

    const ui = createUi();
    const emailLine = ui.emailInput.closest(".lc-auth-line");
    const passwordLine = ui.passwordInput.closest(".lc-auth-line");
    const allowEmailPassword = opts.allowEmailPassword !== false;
    const allowGoogle = opts.allowGoogle !== false;

    function setControlsVisibility(isLoggedIn) {
      if (isLoggedIn) {
        emailLine.style.display = "none";
        passwordLine.style.display = "none";
        ui.emailSignInBtn.style.display = "none";
        ui.googleBtn.style.display = "none";
        ui.signOutBtn.style.display = "";
        return;
      }

      emailLine.style.display = allowEmailPassword ? "" : "none";
      passwordLine.style.display = allowEmailPassword ? "" : "none";
      ui.emailSignInBtn.style.display = allowEmailPassword ? "" : "none";
      ui.googleBtn.style.display = allowGoogle ? "" : "none";
      ui.signOutBtn.style.display = "none";
    }

    ui.trigger.addEventListener("click", function () {
      ui.panel.hidden = !ui.panel.hidden;
    });

    document.addEventListener("click", function (event) {
      if (ui.panel.hidden) {
        return;
      }
      if (!ui.panel.contains(event.target) && event.target !== ui.trigger) {
        ui.panel.hidden = true;
      }
    });

    if (!isFirebaseReady()) {
      setStatus(ui.statusEl, "Firebase SDK not loaded.", "error");
      ui.trigger.textContent = "Auth unavailable";
      return;
    }

    if (!hasFirebaseConfig(cfg)) {
      setStatus(
        ui.statusEl,
        "Configure Firebase in firebase-auth-config.js.",
        "error",
      );
      ui.trigger.textContent = "Auth setup";
      return;
    }

    const app = firebase.apps.length
      ? firebase.app()
      : firebase.initializeApp(cfg);
    const auth = firebase.auth(app);

    setControlsVisibility(false);

    auth.onAuthStateChanged(function (user) {
      if (user) {
        const identity = user.email || user.displayName || user.uid;
        ui.userEl.textContent = "Signed in as " + identity;
        ui.trigger.textContent = "Account";
        setStatus(ui.statusEl, "Session active.", "success");
        setControlsVisibility(true);
      } else {
        ui.userEl.textContent = "Not signed in";
        ui.trigger.textContent = "Sign in";
        setStatus(ui.statusEl, "Ready", "info");
        setControlsVisibility(false);
      }
    });

    ui.emailSignInBtn.addEventListener("click", function () {
      const email = ui.emailInput.value.trim();
      const password = ui.passwordInput.value;
      if (!email || !password) {
        setStatus(ui.statusEl, "Enter email and password.", "error");
        return;
      }

      setStatus(ui.statusEl, "Signing in...", "info");
      auth.signInWithEmailAndPassword(email, password).catch(function (error) {
        setStatus(ui.statusEl, error.message, "error");
      });
    });

    ui.googleBtn.addEventListener("click", async function () {
      setStatus(ui.statusEl, "Starting Google sign in...", "info");
      const provider = new firebase.auth.GoogleAuthProvider();

      const method =
        opts.signInWithPopup === false
          ? "signInWithRedirect"
          : "signInWithPopup";

      if (method === "signInWithRedirect") {
        auth.signInWithRedirect(provider).catch(function (error) {
          setStatus(ui.statusEl, error.message, "error");
        });
        return;
      }

      try {
        await auth.signInWithPopup(provider);
      } catch (error) {
        const code = error && error.code ? String(error.code) : "";
        const shouldFallbackToRedirect =
          code === "auth/popup-blocked" ||
          code === "auth/cancelled-popup-request" ||
          code === "auth/operation-not-supported-in-this-environment";

        if (shouldFallbackToRedirect) {
          setStatus(
            ui.statusEl,
            "Popup blocked. Switching to redirect...",
            "info",
          );
          auth.signInWithRedirect(provider).catch(function (redirectError) {
            setStatus(ui.statusEl, redirectError.message, "error");
          });
          return;
        }

        setStatus(ui.statusEl, error.message, "error");
      }
    });

    ui.signOutBtn.addEventListener("click", function () {
      auth.signOut().catch(function (error) {
        setStatus(ui.statusEl, error.message, "error");
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setup);
  } else {
    setup();
  }
})();
