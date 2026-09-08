import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { crx } from "@crxjs/vite-plugin";
import baseManifest from "./manifest.json" with { type: "json" };

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiBaseUrl = env.VITE_API_BASE_URL || "http://localhost:8001";

  // host_permissions must match wherever the extension actually fetches the
  // backend from (src/api/apiClient.ts reads the same VITE_API_BASE_URL) —
  // otherwise a production build silently fails with a permission error.
  const manifest = {
    ...baseManifest,
    host_permissions: [`${apiBaseUrl}/*`],
  };

  return {
    plugins: [react(), crx({ manifest })],
    resolve: {
      alias: {
        "@": "/src",
        "@adapters": "/adapters",
      },
    },
    server: {
      port: 5173,
      strictPort: true,
      hmr: { port: 5173 },
    },
  };
});
