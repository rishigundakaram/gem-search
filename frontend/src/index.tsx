import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/retro.css";
import { RetroFlagsProvider } from "./context/RetroFlags";

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);
root.render(
  <React.StrictMode>
    <RetroFlagsProvider>
      <App />
    </RetroFlagsProvider>
  </React.StrictMode>
);
