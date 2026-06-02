import preset from "./src/shared/theme/tailwind-preset.ts";

/** @type {import('tailwindcss').Config} */
export default {
    content: ["./index.html", "./src/**/*.{ts,tsx}"],
    presets: [preset],
    theme: {
        extend: {},
    },
    plugins: [],
};
