import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        obsidian: "#0B0B0B",
        sun: "#FF5722"
      },
      boxShadow: {
        glass: "0 8px 40px rgba(0, 0, 0, 0.4)"
      }
    }
  },
  plugins: []
};

export default config;
