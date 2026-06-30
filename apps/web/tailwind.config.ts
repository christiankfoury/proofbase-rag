import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17212b",
        paper: "#f5f7f2",
        moss: {
          DEFAULT: "#526c4f",
          soft: "#e3eddf",
          dark: "#314d35",
        },
        rust: {
          DEFAULT: "#a85732",
          soft: "#f9e6da",
          dark: "#8d3f21",
        },
        steel: {
          DEFAULT: "#486581",
          soft: "#e3eef7",
          dark: "#2f4f69",
        },
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(23 33 43 / 0.06), 0 1px 4px 0 rgb(23 33 43 / 0.1)",
      },
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "1rem" }],
      },
    },
  },
  plugins: [],
};

export default config;
