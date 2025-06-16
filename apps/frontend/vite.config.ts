import { defineConfig, ViteDevServer, Connect, PreviewServer } from "vite";
import react from "@vitejs/plugin-react";

function addKuromojiMiddleware(mw: Connect.Server) {
    mw.use((req, res, next) => {
        if (
            req.url &&
            req.url.startsWith("/dict/") &&
            req.url.endsWith(".dat.gz")
        ) {
            // Store original methods from this specific response object
            const originalSetHeader = res.setHeader.bind(res);

            // Override setHeader for this response to catch and modify/prevent Content-Encoding
            res.setHeader = (
                name: string,
                value: number | string | string[]
            ) => {
                if (
                    name.toLowerCase() === "content-encoding" &&
                    value === "gzip"
                ) {
                    // Prevent browser form auto-unzipping and let Kuromoji handle unzipping the raw gzipped data.
                    return res;
                }
                return originalSetHeader(name, value);
            };

            // Explicitly set the Content-Type so Kuromoji knows it's gzipped binary data
            originalSetHeader("Content-Type", "application/gzip");
        }
        next();
    });
}

export default defineConfig({
    plugins: [
        react(),
        {
            name: "kuromoji-dic-serve-config",
            configureServer(server: ViteDevServer) {
                addKuromojiMiddleware(server.middlewares);
            },
        },
        {
            name: "kuromoji-dic-serve-preview-config",
            configurePreviewServer(server: PreviewServer) {
                addKuromojiMiddleware(server.middlewares);
            },
        },
    ],
    resolve: {
        alias: {
            path: "path-browserify",
            util: "rollup-plugin-node-polyfills/polyfills/util",
            process: "rollup-plugin-node-polyfills/polyfills/process-es6",
        },
    },
    define: {
        global: "window",
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
        },
    },
});
