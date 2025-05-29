// vite.config.js
import { defineConfig } from "vite";

export default defineConfig({
    // during `npm run dev`, vite’s server will forward these paths to FastAPI
    server: {
        proxy: {
            "/ws": {
                target: "ws://localhost:8000",
                ws: true                // proxy WebSocket
            },
            "/video_feed": {
                target: "http://localhost:8000",
                changeOrigin: true      // proxy MJPEG stream
            }
        }
    },

    // when you run `npm run build`, write into your existing static/ folder
    build: {
        outDir: "../static",         // <-- replace dist/ with your static/
        emptyOutDir: false,       // <-- keep any extra files (like index.html) you already have
        rollupOptions: {
            // if you want all your assets in a subfolder (e.g. static/assets)
            // uncomment and adjust:
            // output: { assetFileNames: "assets/[name]-[hash][extname]" }
        }, 
        minify: false
    }
});
