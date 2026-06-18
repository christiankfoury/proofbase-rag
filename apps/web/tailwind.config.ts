import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1f2933",
        paper: "#f7f8f5",
        moss: {
          DEFAULT: "#526c4f",
          soft: "#eaf0e8",
          dark: "#3f5440",
        },
        rust: {
          DEFAULT: "#a85732",
          soft: "#fbece2",
          dark: "#8a4527",
        },
        steel: {
          DEFAULT: "#486581",
          soft: "#e9f0f6",
          dark: "#37516a",
        },
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(31 41 51 / 0.04), 0 1px 3px 0 rgb(31 41 51 / 0.06)",
      },
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "1rem" }],
      },
    },
  },
  plugins: [],
};

export default config;
