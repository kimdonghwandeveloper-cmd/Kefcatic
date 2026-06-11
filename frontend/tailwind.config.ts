import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Kefcatic design tokens
        black: "#0A0A0A",
        white: "#FAFAFA",
        gray: {
          50: "#F5F5F5",
          100: "#E8E8E8",
          200: "#D1D1D1",
          400: "#9A9A9A",
          600: "#5C5C5C",
          800: "#2A2A2A",
          950: "#111111",
        },
      },
      fontFamily: {
        sans: ["Pretendard", "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      fontSize: {
        display: ["28px", { fontWeight: "700", letterSpacing: "-0.5px" }],
        title: ["20px", { fontWeight: "600", letterSpacing: "-0.3px" }],
        body: ["14px", { fontWeight: "400", letterSpacing: "0px" }],
        caption: ["12px", { fontWeight: "400", letterSpacing: "0.2px" }],
        label: ["12px", { fontWeight: "500", letterSpacing: "0.4px" }],
      },
      spacing: {
        // 4px base unit
        1: "4px",
        2: "8px",
        3: "12px",
        4: "16px",
        6: "24px",
        8: "32px",
        12: "48px",
        16: "64px",
      },
      borderRadius: {
        card: "8px",
        badge: "4px",
        button: "6px",
        modal: "12px",
      },
    },
  },
  plugins: [],
};

export default config;
