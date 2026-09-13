/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        /* ── Themed via CSS Variables ── */
        "accent-teal": "rgb(var(--accent) / <alpha-value>)",
        "primary": {
          DEFAULT: "rgb(var(--accent) / <alpha-value>)",
          foreground: "rgb(var(--surface-deep) / <alpha-value>)"
        },
        "primary-container": "rgb(var(--accent) / <alpha-value>)",
        "primary-fixed": "rgb(var(--accent) / <alpha-value>)",
        "primary-fixed-dim": "rgb(var(--accent-hover) / <alpha-value>)",
        "surface-main": "rgb(var(--surface-deep) / <alpha-value>)",
        "surface": "rgb(var(--surface-card) / <alpha-value>)",
        "surface-container": "rgb(var(--surface-raised) / <alpha-value>)",
        "on-surface": "rgb(var(--on-surface) / <alpha-value>)",
        "on-surface-variant": "rgb(var(--on-surface-muted) / <alpha-value>)",
        "text-dim": "rgb(var(--text-muted) / <alpha-value>)",
        "on-background": "rgb(var(--on-surface) / <alpha-value>)",
        "background": "rgb(var(--surface-deep) / <alpha-value>)",
        "foreground": "rgb(var(--on-surface) / <alpha-value>)",
        "card": {
          DEFAULT: "rgb(var(--surface-card) / <alpha-value>)",
          foreground: "rgb(var(--on-surface) / <alpha-value>)"
        },
        "popover": {
          DEFAULT: "rgb(var(--surface-card) / <alpha-value>)",
          foreground: "rgb(var(--on-surface) / <alpha-value>)"
        },
        "secondary": {
          DEFAULT: "rgb(var(--surface-raised) / <alpha-value>)",
          foreground: "rgb(var(--on-surface) / <alpha-value>)"
        },
        "muted": {
          DEFAULT: "rgb(var(--surface-raised) / <alpha-value>)",
          foreground: "rgb(var(--text-muted) / <alpha-value>)"
        },
        "accent": {
          DEFAULT: "rgb(var(--surface-raised) / <alpha-value>)",
          foreground: "rgb(var(--on-surface) / <alpha-value>)"
        },
        "destructive": {
          DEFAULT: "#ffb4ab",
          foreground: "#690005"
        },
        "border": "rgb(var(--border) / <alpha-value>)",
        "input": "rgb(var(--border) / <alpha-value>)",
        "ring": "rgb(var(--ring) / <alpha-value>)",

        /* ── Static Colors (unchanged across themes) ── */
        "outline": "#85948e",
        "on-secondary-container": "#b8b6d0",
        "on-error-container": "#ffdad6",
        "status-success": "#4ADE80",
        "on-tertiary-fixed-variant": "#793100",
        "on-primary": "#00382d",
        "tertiary-container": "#ff9862",
        "tertiary-fixed-dim": "#ffb692",
        "tertiary-fixed": "#ffdbcb",
        "on-secondary-fixed-variant": "#45455b",
        "error": "#ffb4ab",
        "inverse-primary": "#006b58",
        "surface-variant": "#343440",
        "on-secondary-fixed": "#1a1a2e",
        "surface-dim": "#12121d",
        "on-secondary": "#2f2e43",
        "surface-container-lowest": "#0d0d18",
        "on-primary-fixed": "#002019",
        "on-primary-fixed-variant": "#005142",
        "surface-container-highest": "#343440",
        "surface-container-low": "#1b1a26",
        "secondary-container": "#47475d",
        "surface-bright": "#383845",
        "on-primary-container": "#004e40",
        "status-warning": "#FF6B35",
        "outline-variant": "#3c4a45",
        "secondary-fixed": "#e2e0fc",
        "status-info": "#3B82F6",
        "inverse-surface": "#e3e0f1",
        "tertiary": "#ffc0a1",
        "on-error": "#690005",
        "secondary": "#c6c4df",
        "inverse-on-surface": "#302f3b",
        "surface-secondary": "#1A1A2E",
        "on-tertiary": "#552000",
        "on-tertiary-container": "#762f00",
        "on-tertiary-fixed": "#341100",
        "secondary-fixed-dim": "#c6c4df",
      },
      borderRadius: {
        lg: `0.5rem`,
        md: `calc(0.5rem - 2px)`,
        sm: `calc(0.5rem - 4px)`,
      },
      fontFamily: {
        "inter": ["Inter", "sans-serif"],
        "jetbrains-mono": ["JetBrains Mono", "monospace"]
      }
    },
  },
  plugins: [
    require('tailwindcss-animate'),
    require('@tailwindcss/forms'),
    require('@tailwindcss/container-queries')
  ],
}
