import { existsSync, promises as fs } from "node:fs";
import { fileURLToPath, URL } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";
import { VitePWA } from "vite-plugin-pwa";

const src = fileURLToPath(new URL("./src", import.meta.url));
const demoModule = (rel: string): string =>
    fileURLToPath(new URL(`./src/demo/${rel}`, import.meta.url));

/**
 * Copies the committed demo static assets (media, clips, audio) to the build's
 * `/api` root so the bundled `/api/...` URLs resolve. Demo builds only; the
 * assets live outside the shared `public/`, so production output is unaffected.
 */
function demoAssets(): Plugin {
    return {
        name: "mirumoji-demo-assets",
        apply: "build",
        async closeBundle() {
            const from = fileURLToPath(new URL("./src/demo/generated/assets/api", import.meta.url));
            const to = fileURLToPath(new URL("./dist/api", import.meta.url));
            if (existsSync(from)) await fs.cp(from, to, { recursive: true });
        },
    };
}

/**
 * The PWA plugin, enabled in both the real and demo builds so the demo is
 * installable too. useCredentials makes the manifest and icon fetches carry
 * credentials, which the Modal host Basic Auth requires and same-origin deploys
 * ignore. The /api matchers are base-agnostic so they hold under the root / and
 * the Pages /mirumoji/ base.
 */
function makePwa(demo: boolean): Plugin[] {
    return VitePWA({
        // Auto-update the service worker in the background -> no "reload?" prompt
        registerType: "autoUpdate",
        // Send credentials with the manifest + icon fetches so they pass the
        // Modal host Basic Auth (harmless same-origin on nginx / Pages)
        useCredentials: true,
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
                { src: "icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
                { src: "icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
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
            // Never precache the demo's static /api/* fixtures. The sample mp4
            // exceeds the precache size cap anyway, and they are runtime-cached
            // below.
            globIgnores: demo ? ["api/**"] : [],
            // Keep the SPA navigation fallback from swallowing requests for paths
            // served directly: API calls, the mkdocs site under /docs on the
            // Pages build, and the local CA download. The /api and /docs matchers
            // are unanchored so they also hold under the /mirumoji/ base.
            navigateFallbackDenylist: [/\/api\//, /\/docs(?:\/|$)/, /^\/mirumoji-ca\.crt$/],
            runtimeCaching: [
                {
                    // Base-agnostic: matches /api/ and /mirumoji/api/
                    urlPattern: ({ url }) => url.pathname.includes("/api/"),
                    // The demo /api/* are committed static fixtures, so cache
                    // them. The real app /api is a live backend, never cached.
                    handler: demo ? "CacheFirst" : "NetworkOnly",
                },
            ],
        },
    });
}

export default defineConfig(({ mode }) => {
    const demo = mode === "demo";
    return {
        // The PWA plugin runs before demoAssets so the service worker is
        // generated before the demo /api fixtures are copied into dist, keeping
        // them out of the precache manifest.
        plugins: [react(), makePwa(demo), ...(demo ? [demoAssets()] : [])],
        resolve: {
            // In demo mode, the network layer and a few components are swapped
            // for fixture-backed variants under src/demo/. The `@real/*` channel
            // lets a variant re-import the original it wraps. Order matters: the
            // specific ids come before the `@` catch-all.
            alias: demo
                ? [
                      { find: /^@real(?=\/)/, replacement: src },
                      { find: "@/shared/api/client", replacement: demoModule("api/client.ts") },
                      { find: "@/shared/api/sse", replacement: demoModule("api/sse.ts") },
                      { find: "@/shared/dict/api", replacement: demoModule("api/dict.ts") },
                      {
                          find: "@/contexts/ProfileContext",
                          replacement: demoModule("ProfileContext.tsx"),
                      },
                      {
                          find: "@/contexts/PlayerContext",
                          replacement: demoModule("PlayerContext.tsx"),
                      },
                      {
                          find: "@/features/dictionary/DictionaryPage",
                          replacement: demoModule("components/DictionaryPage.tsx"),
                      },
                      {
                          find: "@/features/text/TextPage",
                          replacement: demoModule("components/TextPage.tsx"),
                      },
                      {
                          find: "@/app/shell/ProfileChip",
                          replacement: demoModule("components/ProfileChip.tsx"),
                      },
                      {
                          find: "@/features/profile/components/ProfilePanel",
                          replacement: demoModule("components/ProfilePanel.tsx"),
                      },
                      {
                          find: "@/features/player/components/LoadMediaPopover",
                          replacement: demoModule("components/LoadMediaPopover.tsx"),
                      },
                      {
                          find: "@/shared/components/DictDisplays",
                          replacement: demoModule("components/DictDisplays.tsx"),
                      },
                      { find: "@", replacement: src },
                  ]
                : { "@": src },
        },
        server: {
            port: 5173,
            // The demo is fully static and serves its own /api/* assets from the
            // bundle, so it needs no backend proxy. This config also applies to
            // `vite preview`, where a /api proxy would shadow those bundled
            // /api/media assets with 502s from an absent backend.
            proxy: demo
                ? undefined
                : {
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
            // Rolldown-native chunking (Vite 8). Keeps React in its own vendor
            // chunk, the same split the old rollup `manualChunks` produced.
            rolldownOptions: {
                output: {
                    codeSplitting: {
                        groups: [{ name: "vendor", test: /\/react(?:-dom)?/ }],
                    },
                },
            },
        },
    };
});
