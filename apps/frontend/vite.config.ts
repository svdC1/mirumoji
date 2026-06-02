import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            // Proxy requests in the dev server to /api
            "/api": {
                target: "http://localhost:8000",
                changeOrigin: true,
                secure: false,
                rewrite: (path) => path.replace(/^\/api/, ""),
            },
            "/openapi.json": {
                target: "http://localhost:8000/",
                changeOrigin: true,
                secure: false,
            },
        },
    },
    build: {
        rollupOptions: {
            output: {
                manualChunks(id) {
                    if (/\/react(?:-dom)?/.test(id)) {
                        return "vendor";
                    }
                },
            },
        },
    },
});
