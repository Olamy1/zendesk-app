import React from "react";
export default function StatusBadge({ status }) {
  const map = {
    open: "bg-blue-100 text-blue-800",
    pending: "bg-yellow-100 text-yellow-800",
    "on-hold": "bg-orange-100 text-orange-800",
    solved: "bg-green-100 text-green-800",
    closed: "bg-gray-200 text-gray-800"
  };
  return <span className={`px-2 py-1 rounded text-xs ${map[status] || "bg-gray-100"}`}>{status}</span>;
}
