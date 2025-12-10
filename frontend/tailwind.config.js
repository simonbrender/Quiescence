/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Celerio-inspired color palette
        border: "hsl(220, 13%, 18%)",
        input: "hsl(220, 13%, 18%)",
        ring: "hsl(217, 91%, 60%)",
        background: "hsl(220, 20%, 8%)",
        foreground: "hsl(210, 20%, 98%)",
        primary: {
          DEFAULT: "hsl(217, 91%, 60%)",
          foreground: "hsl(220, 20%, 8%)",
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
          DEFAULT: "hsl(217, 91%, 60%)",
          foreground: "hsl(220, 20%, 8%)",
        },
        card: {
          DEFAULT: "hsl(220, 13%, 12%)",
          foreground: "hsl(210, 20%, 98%)",
        },
      },
      fontFamily: {
        sans: ['Inter: ['Inter', 'system-ui', 'sans-serif'],
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

