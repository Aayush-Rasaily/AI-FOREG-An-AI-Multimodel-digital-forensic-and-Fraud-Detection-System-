import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const backendUrl = env.VITE_BACKEND_URL || "http://127.0.0.1:8000";
  const isProd = mode === "production";

  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: backendUrl,
          changeOrigin: true,
        },
      },
    },
    build: {
      target: "es2022",
      cssCodeSplit: true,
      sourcemap: !isProd,
      assetsInlineLimit: 4096,
      chunkSizeWarningLimit: 600,
      reportCompressedSize: true,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes("node_modules")) {
              return undefined;
            }
            if (id.includes("react-dom") || id.includes("/react/") || id.includes("\\react\\")) {
              return "vendor-react";
            }
            if (id.includes("@tanstack")) {
              return "vendor-query";
            }
            if (id.includes("lucide-react")) {
              return "vendor-icons";
            }
            return "vendor";
          },
        },
      },
    },
    // Vite serves precompressed assets when present; nginx also enables gzip.
    preview: {
      port: 4173,
    },
  };
});
