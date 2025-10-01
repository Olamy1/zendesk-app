import React from "react";
export default function ClosedByMeetingFlag({ value }) {
  return (
    <span className={`px-2 py-1 rounded text-xs ${value ? "bg-green-200 font-semibold" : "bg-gray-100"}`}>
      {value ? "Yes" : "No"}
    </span>
  );
}
