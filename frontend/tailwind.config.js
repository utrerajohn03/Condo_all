/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Argo UI reference tokens (docs/../argo-ui-reference)
        primary: '#2563EB',    // blue-600
        sidebar: '#0F172A',    // slate-900
        active: '#1E293B',     // slate-800
        canvas: '#F3F4F6',     // gray-100
        success: '#059669',    // emerald-600
        danger: '#E11D48',     // rose-600
        warn: '#D97706',       // amber-600
        ink: '#111827',        // gray-900
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
