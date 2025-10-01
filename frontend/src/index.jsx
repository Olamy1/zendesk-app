import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./styles/globals.css";
import ZAFClient from "zendesk_app_framework_sdk";

const client = ZAFClient.init();

client.on("app.registered", async () => {
  try {
    // Pull backend URL from manifest.json parameter
    const meta = await client.metadata();
    const backendBaseUrl = meta.settings.BACKEND_BASE_URL;

    console.log("ZAF app registered. Backend:", backendBaseUrl);

    createRoot(document.getElementById("root")).render(
      <App client={client} backendBaseUrl={backendBaseUrl} />
    );
  } catch (err) {
    console.error("Failed to initialize app:", err);
  }
});
