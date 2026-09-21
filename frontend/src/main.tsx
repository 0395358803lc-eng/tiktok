import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import AdminRoot from "./AdminRoot";
import { PrivacyPage, PublicHome, TermsPage } from "./PublicSite";
import "./styles.css";

function Route() {
  const path = window.location.pathname.replace(/\/+$/, "") || "/";

  if (path === "/terms") return <TermsPage />;
  if (path === "/privacy") return <PrivacyPage />;
  if (path === "/admin") return <AdminRoot />;
  return <PublicHome />;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Route />
  </StrictMode>,
);
