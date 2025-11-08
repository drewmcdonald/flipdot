/** @jsxImportSource https://esm.sh/react@18.2.0 */
import React from "https://esm.sh/react@18.2.0";
import { createRoot } from "https://esm.sh/react-dom@18.2.0/client";
import { App } from "./App.tsx";
import { QueryProvider } from "./providers/QueryProvider.tsx";

const root = createRoot(document.getElementById("root")!);
root.render(
  <QueryProvider>
    <App />
  </QueryProvider>
);
