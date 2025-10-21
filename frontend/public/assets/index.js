/* Minimal ZAF bootstrap + backend health ping */
(function () {
  const elBackend = document.getElementById("backend");
  const elApiKey = document.getElementById("apikey");
  const elHealth = document.getElementById("health");

  let client = null;
  try {
    client = ZAFClient.init();
    console.info("[ZAF] Client initialized (vanilla)");
  } catch (e) {
    console.warn("[ZAF] Not available; falling back to local preview mode.");
  }

  function getQueryParams() {
    try {
      return Object.fromEntries(new URLSearchParams(window.location.search).entries());
    } catch (_e) {
      return {};
    }
  }

  async function readParams() {
    // 1) ZAF runtime (preferred)
    if (client && client.metadata) {
      try {
        const meta = await client.metadata();
        const settings = meta && meta.settings ? meta.settings : {};
        return {
          BACKEND_BASE_URL: settings.BACKEND_BASE_URL || "",
          API_KEY: settings.API_KEY || "",
        };
      } catch (e) {
        console.error("[ZAF] Failed to fetch metadata:", e);
      }
    }
    // 2) URL query overrides (?backend=&apikey=)
    const q = getQueryParams();
    if (q.backend || q.apikey) {
      return { BACKEND_BASE_URL: q.backend || "", API_KEY: q.apikey || "" };
    }
    // 3) settings.json fallback for local preview
    try {
      const res = await fetch("settings.json", { cache: "no-store" });
      if (res.ok) {
        const cfg = await res.json();
        return {
          BACKEND_BASE_URL: cfg.BACKEND_BASE_URL || "",
          API_KEY: cfg.API_KEY || "",
        };
      }
    } catch (_e) {
      // ignore
    }
    // 4) nothing available
    console.warn("[Preview] No parameters found; set ?backend= or add settings.json");
    return { BACKEND_BASE_URL: "", API_KEY: "" };
  }

  async function pingHealth(baseUrl, apiKey) {
    if (!baseUrl) {
      elHealth.textContent = "(missing BACKEND_BASE_URL)";
      elHealth.classList.remove("muted");
      elHealth.classList.add("err");
      return;
    }
    try {
      const res = await fetch(`${baseUrl.replace(/\/$/, "")}/health`, {
        headers: {
          "Content-Type": "application/json",
          "X-Request-Source": "ZAF-Assets",
          ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
        },
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();
      elHealth.textContent = `${data.status || "ok"}`;
      elHealth.classList.remove("muted");
      elHealth.classList.add("ok");
    } catch (e) {
      console.error("[Health] Ping failed:", e);
      elHealth.textContent = `error`;
      elHealth.classList.remove("muted");
      elHealth.classList.add("err");
    }
  }

  (async function init() {
    const { BACKEND_BASE_URL, API_KEY } = await readParams();
    if (BACKEND_BASE_URL) {
      elBackend.textContent = BACKEND_BASE_URL;
      elBackend.classList.remove("muted");
    }
    if (API_KEY) {
      elApiKey.textContent = "(provided)";
      elApiKey.classList.remove("muted");
    }
    await pingHealth(BACKEND_BASE_URL, API_KEY);
  })();
})();
