import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";

import App from "./App";
import { InvestigationProvider } from "./state/InvestigationContext";
import "./styles/index.css";

// One query client for the app. Retries are kept low because a slow free-tier
// backend should surface the ErrorBanner with a manual Retry instead.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
    mutations: { retry: 0 },
  },
});

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element #root is missing from index.html.");
}

createRoot(rootElement).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <InvestigationProvider>
          <App />
        </InvestigationProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
