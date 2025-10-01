import React from "react";

export default function Settings() {
  return (
    <div className="space-y-2">
      <h2 className="text-lg font-semibold">Settings</h2>
      <p className="text-sm text-gray-600">
        For MVP, all app settings are managed via environment variables and
        Zendesk app parameters.
      </p>
      <p className="text-sm text-gray-500 italic">
        Future versions will allow directors to configure default filters (e.g.,
        Policy group only, status sets) directly in-app.
      </p>
    </div>
  );
}
