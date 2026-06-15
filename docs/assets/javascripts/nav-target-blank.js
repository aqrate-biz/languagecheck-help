(() => {
  const targetPathnames = new Set([
    "/site/api-reference/",
    "/api-reference/",
    "/api-reference/index.html",
  ]);

  function normalizePathname(pathname) {
    return pathname.replace(/index\.html$/, "").replace(/\/+$/, "/") || "/";
  }

  function isStatusLink(link) {
    const href = link.getAttribute("href") || "";
    if (!href) {
      return false;
    }

    try {
      const pathname = normalizePathname(
        new URL(href, window.location.origin).pathname,
      );
      return targetPathnames.has(pathname) || pathname === "/api-reference";
    } catch {
      return false;
    }
  }

  function addIcon(link) {
    if (link.querySelector(".nav-link-icon")) {
      return;
    }

    const icon = document.createElement("span");
    icon.className = "nav-link-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="fill:none;display:inline-block;vertical-align:middle;margin-left:0.35rem;">
        <path stroke="none" d="M0 0h24v24H0z" fill="none" />
        <path d="M12 6h-6a2 2 0 0 0 -2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-6" />
        <path d="M11 13l9 -9" />
        <path d="M15 4h5v5" />
      </svg>
    `;
    link.appendChild(icon);
  }

  function applyTargetBlank() {
    document
      .querySelectorAll(".md-nav a[href], .md-tabs a[href]")
      .forEach((link) => {
        if (isStatusLink(link)) {
          link.setAttribute("target", "_blank");
          link.setAttribute("rel", "noopener noreferrer");
          addIcon(link);
        }
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyTargetBlank);
  } else {
    applyTargetBlank();
  }
})();
