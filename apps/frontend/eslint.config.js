// ESLint 9 flat config
import js from "@eslint/js";
import tsPlugin from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import reactPlugin from "eslint-plugin-react";
import reactHooksPlugin from "eslint-plugin-react-hooks";

export default [
  // Base JS rules
  js.configs.recommended,

  // TypeScript + React source files
  {
    files: ["src/**/*.{ts,tsx}"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: { jsx: true },
      },
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
      react: reactPlugin,
      "react-hooks": reactHooksPlugin,
    },
    settings: {
      react: { version: "detect" },
    },
    rules: {
      // TypeScript recommended rules (subset — start permissive, tighten in 3.x)
      ...tsPlugin.configs.recommended.rules,

      // React rules
      ...reactPlugin.configs.recommended.rules,
      "react/react-in-jsx-scope": "off", // Not needed with React 17+ JSX transform
      "react/prop-types": "off",         // TypeScript handles this

      // React hooks
      ...reactHooksPlugin.configs.recommended.rules,

      // Relax some rules that produce too much noise on an existing codebase
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
    },
  },

  // Ignore generated / build output
  {
    ignores: ["dist/**", "node_modules/**", "*.config.js", "*.config.ts"],
  },
];
