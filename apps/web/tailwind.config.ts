import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1f2933",
        paper: "#f7f8f5",
        moss: "#526c4f",
        rust: "#a85732",
        steel: "#486581",
      },
    },
  },
  plugins: [],
};

export default config;
