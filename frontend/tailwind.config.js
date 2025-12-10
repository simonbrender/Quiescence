/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Celerio color palette - matching website design
        border: "hsl(220, 13%, 18%)",
        input: "hsl(220, 13%, 18%)",
        ring: "hsl(160, 100%, 50%)", // Teal/light green accent
        background: "hsl(220, 20%, 8%)",
        foreground: "hsl(210, 20%, 98%)",
        primary: {
          DEFAULT: "hsl(160, 100%, 50%)", // Vibrant teal/light green
          foreground: "hsl(220, 20%, 8%)", // Dark text on light background
        },
        secondary: {
          DEFAULT: "hsl(220, 13%, 18%)",
          foreground: "hsl(210, 20%, 98%)",
        },
        muted: {
          DEFAULT: "hsl(220, 13%, 18%)",
          foreground: "hsl(215, 16%, 70%)",
        },
        accent: {
          DEFAULT: "hsl(160, 100%, 50%)", // Teal accent
          foreground: "hsl(220, 20%, 8%)",
        },
        card: {
          DEFAULT: "hsl(220, 13%, 12%)",
          foreground: "hsl(210, 20%, 98%)",
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        lg: "0.5rem",
        md: "calc(0.5rem - 2px)",
        sm: "calc(0.5rem - 4px)",
      },
    },
  },
  plugins: [],
}

