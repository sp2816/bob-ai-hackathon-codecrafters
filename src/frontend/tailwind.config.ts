import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: ["class", '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        // Brand — Dark mode: magenta/pink, Light mode: purple
        brand: {
          50:  "var(--brand-50)",
          100: "var(--brand-100)",
          200: "var(--brand-200)",
          300: "var(--brand-300)",
          400: "var(--brand-400)",
          500: "var(--brand-500)",
          600: "var(--brand-600)",
          700: "var(--brand-700)",
          800: "var(--brand-800)",
          900: "var(--brand-900)",
        },
        // Surface layers
        surface: {
          base:     "var(--surface-base)",
          card:     "var(--surface-card)",
          elevated: "var(--surface-elevated)",
          overlay:  "var(--surface-overlay)",
        },
        // Border
        border: {
          DEFAULT: "var(--border-default)",
          subtle:  "var(--border-subtle)",
          strong:  "var(--border-strong)",
        },
        // Text
        text: {
          primary:   "var(--text-primary)",
          secondary: "var(--text-secondary)",
          muted:     "var(--text-muted)",
          inverse:   "var(--text-inverse)",
          brand:     "var(--text-brand)",
        },
        // Semantic
        success: {
          DEFAULT: "var(--success)",
          bg:      "var(--success-bg)",
          border:  "var(--success-border)",
          text:    "var(--success-text)",
        },
        warning: {
          DEFAULT: "var(--warning)",
          bg:      "var(--warning-bg)",
          border:  "var(--warning-border)",
          text:    "var(--warning-text)",
        },
        danger: {
          DEFAULT: "var(--danger)",
          bg:      "var(--danger-bg)",
          border:  "var(--danger-border)",
          text:    "var(--danger-text)",
        },
        info: {
          DEFAULT: "var(--info)",
          bg:      "var(--info-bg)",
          border:  "var(--info-border)",
          text:    "var(--info-text)",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "sans-serif",
        ],
        mono: [
          '"JetBrains Mono"',
          '"Fira Code"',
          "ui-monospace",
          '"Cascadia Code"',
          "monospace",
        ],
      },
      fontSize: {
        "2xs": ["0.65rem", { lineHeight: "1rem" }],
        xs:   ["0.75rem", { lineHeight: "1.125rem" }],
        sm:   ["0.8125rem", { lineHeight: "1.25rem" }],
        base: ["0.875rem", { lineHeight: "1.5rem" }],
        md:   ["0.9375rem", { lineHeight: "1.5rem" }],
        lg:   ["1rem", { lineHeight: "1.625rem" }],
        xl:   ["1.125rem", { lineHeight: "1.75rem" }],
        "2xl": ["1.25rem", { lineHeight: "1.875rem" }],
        "3xl": ["1.5rem", { lineHeight: "2rem" }],
        "4xl": ["1.875rem", { lineHeight: "2.25rem" }],
        "5xl": ["2.25rem", { lineHeight: "2.5rem" }],
        "6xl": ["3rem", { lineHeight: "3.25rem" }],
      },
      boxShadow: {
        "card":        "0 1px 3px rgba(0,0,0,0.25), 0 4px 16px rgba(0,0,0,0.2)",
        "card-hover":  "0 2px 8px rgba(0,0,0,0.35), 0 8px 32px rgba(0,0,0,0.28)",
        "brand-glow":  "0 0 20px rgba(175,23,99,0.18), 0 0 40px rgba(175,23,99,0.1)",
        "danger-glow": "0 0 16px rgba(171,46,60,0.2)",
        "soft":        "0 1px 4px rgba(0,0,0,0.15), 0 4px 12px rgba(0,0,0,0.12)",
        "none":        "none",
      },
      borderRadius: {
        DEFAULT: "0.5rem",
        sm: "0.375rem",
        md: "0.625rem",
        lg: "0.75rem",
        xl: "1rem",
        "2xl": "1.25rem",
        "3xl": "1.5rem",
      },
      transitionDuration: {
        DEFAULT: "150ms",
        fast: "100ms",
        slow: "250ms",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-up": "slideUp 0.2s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
} satisfies Config;