import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
    plugins: [
        react(),
        VitePWA({
            // Auto-update the service worker in the background -> no "reload?" prompt
            registerType: "autoUpdate",
            // public/ assets that should be precached alongside the build output
            includeAssets: ["favicon.ico", "icons/icon-192.png", "icons/icon-512.png"],
            // scope / start_url are left to the plugin so they track Vite's `base`
            // (`/` self-hosted, `/mirumoji/` on Pages). Icon/screenshot srcs are
            // relative so they resolve against the manifest URL under either base
            manifest: {
                name: "Mirumoji",
                short_name: "Mirumoji",
                description: "Japanese Immersion Toolkit",
                theme_color: "#15120F",
                background_color: "#15120F",
                display: "standalone",
                icons: [
                    {
                        src: "icons/icon-192.png",
                        sizes: "192x192",
                        type: "image/png",
                        purpose: "any",
                    },
                    {
                        src: "icons/icon-512.png",
                        sizes: "512x512",
                        type: "image/png",
                        purpose: "any",
                    },
                    {
                        src: "icons/icon-512.png",
                        sizes: "512x512",
                        type: "image/png",
                        purpose: "maskable",
                    },
                ],
                screenshots: [
                    {
                        src: "screenshots/desktop_screenshot.png",
                        sizes: "2869x1435",
                        type: "image/png",
                        form_factor: "wide",
                    },
                    {
                        src: "screenshots/mobile_screenshot.png",
                        sizes: "1290x2796",
                        type: "image/png",
                    },
                ],
            },
            workbox: {
                // API calls always need the live backend -> never serve them from
                // cache, and never let the SPA navigation fallback swallow them
                navigateFallbackDenylist: [/^\/api\//],
                runtimeCaching: [
                    {
                        urlPattern: ({ url }) => url.pathname.startsWith("/api/"),
                        handler: "NetworkOnly",
                    },
                ],
            },
        }),
    ],
    resolve: {
        alias: {
            "@": fileURLToPath(new URL("./src", import.meta.url)),
        },
    },
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
