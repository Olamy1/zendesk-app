import React, { useMemo, useState, useEffect } from "react";
import { fetchFrontendToken, runExport } from "../services/backendAPI.js";
import useTickets from "../hooks/useTickets.js";
import TicketTable from "../components/TicketTable.jsx";

function Pill({ label }) {
  return (
    <span className="px-2 py-1 rounded bg-gray-100 text-xs whitespace-nowrap">
      {label}
    </span>
  );
}

export default function Dashboard() {
  const [token, setToken] = useState("");
  const [exporting, setExporting] = useState(false);
  const [err, setErr] = useState("");
  const [showExactAge, setShowExactAge] = useState(false);
  const [selectedTab, setSelectedTab] = useState("All"); // ✅ NEW tab selector

  useEffect(() => {
    (async () => {
      try {
        const t = await fetchFrontendToken();
        setToken(t.token || "");
      } catch (e) {
        console.error("Token fetch failed:", e);
        setErr("Failed to initialize session.");
      }
    })();
  }, []);

  const {
    meetingWindow,
    rows,
    loading,
    err: ticketErr,
    refresh,
    updateStatus,
    reassign,
    addNote,
  } = useTickets(token, { bucketed: !showExactAge });

  // ✅ Apply tab filter
  const filteredRows = useMemo(() => {
    if (selectedTab === "All") return rows;
    return rows.filter((r) =>
      (r.group || "").toLowerCase().includes(selectedTab.toLowerCase())
    );
  }, [rows, selectedTab]);

  const counts = useMemo(() => {
    const init = {
      "Over 30 Days": 0,
      "Over 20 Days": 0,
      "Over 10 Days": 0,
      "Under 10 Days": 0,
    };
    for (const r of filteredRows) init[r.ageBucket] = (init[r.ageBucket] || 0) + 1;
    return init;
  }, [filteredRows]);

  return (
    <div className="space-y-4">
      {/* Header row with title + actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 flex-wrap">
          <h2 className="text-lg font-semibold">Ticket Breakdown</h2>
          {meetingWindow && (
            <Pill
              label={`Window: ${new Date(
                meetingWindow.start
              ).toLocaleString()} → ${new Date(
                meetingWindow.end
              ).toLocaleString()}`}
            />
          )}
        </div>
        <div className="flex gap-2">
          <button
            className="border rounded px-3 py-1"
            onClick={() => refresh()}
            disabled={loading}
            aria-busy={loading}
          >
            {loading ? "Refreshing…" : "Refresh"}
          </button>
          <button
            className="border rounded px-3 py-1"
            onClick={async () => {
              setExporting(true);
              try {
                await runExport(token);
              } catch (e) {
                console.error("Export failed:", e);
                setErr("Export failed. Please try again.");
              } finally {
                setExporting(false);
              }
            }}
            disabled={exporting}
            aria-busy={exporting}
          >
            {exporting ? "Exporting…" : "Export → SharePoint & Email"}
          </button>
        </div>
      </div>

      {/* ✅ Tabs for group filter */}
      <div className="flex gap-2">
        {["All", "AIMS", "R&A", "Policy", "Cross-Functional"].map((tab) => (
          <button
            key={tab}
            onClick={() => setSelectedTab(tab)}
            className={`px-3 py-1 rounded ${
              selectedTab === tab
                ? "bg-black text-white"
                : "bg-gray-100 text-black"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Toggle for bucketed vs exact */}
      <div className="flex items-center gap-3">
        <label className="flex items-center space-x-2 text-sm">
          <input
            type="checkbox"
            checked={showExactAge}
            onChange={() => setShowExactAge(!showExactAge)}
          />
          <span>Show Exact Age (Days)</span>
        </label>
      </div>

      {/* Age bucket counts */}
      <div className="flex gap-2 flex-wrap">
        <Pill label={`>30: ${counts["Over 30 Days"]}`} />
        <Pill label={`>20: ${counts["Over 20 Days"]}`} />
        <Pill label={`>10: ${counts["Over 10 Days"]}`} />
        <Pill label={`<10: ${counts["Under 10 Days"]}`} />
      </div>

      {(err || ticketErr) && (
        <div className="text-red-700">{err || ticketErr}</div>
      )}

      {/* Ticket table */}
      <div className="overflow-auto border rounded">
        <TicketTable
          tickets={filteredRows}
          onStatus={updateStatus}
          onReassign={reassign}
          onNote={addNote}
          showExactAge={showExactAge}
        />
      </div>
    </div>
  );
}
