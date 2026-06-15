import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#F8FBFF",
        foreground: "#27324A",
        primary: "#4F5DFF",
        secondary: "#7B8BFF",
        accent: "#FF4FA3",
        surface: "rgba(255,255,255,0.45)",
        "text-primary": "#27324A",
        "text-secondary": "#667085",
      },
      boxShadow: {
        'bubble': '0 10px 40px rgba(0,0,0,0.08)',
      },
    },
  },
  plugins: [],
};
export default config;
