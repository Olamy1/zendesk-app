import React, { useEffect, useState } from "react";
import Dashboard from "./pages/Dashboard.jsx";
import AuditLog from "./pages/AuditLog.jsx";
import Settings from "./pages/Settings.jsx";
import { getAppParams } from "./services/zaf.js";
import { setBackendBaseUrl } from "./services/backendAPI.js";

export default function App() {
  const [route, setRoute] = useState("dashboard");
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        // Pull params from Zendesk App Framework (ZAF)
        const params = await getAppParams();

        // Set backend base URL globally for fetch calls
        if (params?.BACKEND_BASE_URL) {
          setBackendBaseUrl(params.BACKEND_BASE_URL);
          console.log("Backend base URL set:", params.BACKEND_BASE_URL);
        }

        setReady(true);
      } catch (e) {
        console.error("App init failed:", e);
        setError(String(e));
      }
    })();
  }, []);

  const navBtn = (id, label) => (
    <button
      onClick={() => setRoute(id)}
      className={`px-3 py-2 rounded border ${
        route === id ? "bg-black text-white" : "bg-white"
      }`}
    >
      {label}
    </button>
  );

  if (error)
    return <div className="p-4 text-red-700">App init error: {error}</div>;
  if (!ready) return <div className="p-4">Loading…</div>;

  return (
    <div className="p-4 space-y-4">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Directors Reporting</h1>
        <nav className="flex gap-2">
          {navBtn("dashboard", "Dashboard")}
          {navBtn("audit", "Audit Log")}
          {navBtn("settings", "Settings")}
        </nav>
      </header>
      <main>
        {route === "dashboard" && <Dashboard />}
        {route === "audit" && <AuditLog />}
        {route === "settings" && <Settings />}
      </main>
    </div>
  );
}
