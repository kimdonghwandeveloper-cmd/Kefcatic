import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#F5F4F2",
        surface: "#FFFFFF",
        border: "#E2E1DE",
        "text-primary": "#1A1918",
        "text-secondary": "#6B6966",
        "text-tertiary": "#A8A5A2",
        accent: "#2D2B29",
        hover: "#EFEFED",
        destructive: "#C0392B",
      },
      fontFamily: {
        heading: ["Plus Jakarta Sans", "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      fontSize: {
        "h1": ["40px", { lineHeight: "1.2", fontWeight: "700" }],
        "h2": ["28px", { lineHeight: "1.3", fontWeight: "600" }],
        "h3": ["20px", { lineHeight: "1.4", fontWeight: "600" }],
        "body": ["15px", { lineHeight: "1.6", fontWeight: "400" }],
        "body-sm": ["13px", { lineHeight: "1.5", fontWeight: "400" }],
        "label": ["11px", { lineHeight: "1.4", fontWeight: "500", letterSpacing: "0.04em" }],
      },
      spacing: {
        1: "4px",
        2: "8px",
        3: "12px",
        4: "16px",
        6: "24px",
        8: "32px",
        12: "48px",
        16: "64px",
        24: "96px",
      },
      borderRadius: {
        card: "10px",
        button: "6px",
        badge: "999px",
        modal: "12px",
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.08)",
      },
      transitionDuration: {
        fast: "150ms",
        base: "250ms",
        slow: "350ms",
      },
      screens: {
        md: "768px",
        lg: "1024px",
        xl: "1280px",
      },
    },
  },
  plugins: [],
};

export default config;
