/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // ── Base ──
        bg: {
          DEFAULT: '#0d0d0d',
          surface: '#1e1e1e',
          surface2: '#252525',
          card: '#141414',
        },
        // ── Borders ──
        border: {
          DEFAULT: '#2a2a2a',
          strong: '#404040',
        },
        // ── Text — all AAA contrast on #0d0d0d ──
        text: {
          primary:   '#ffffff',  // 21:1 — headings, key values
          secondary: '#e8e8e8',  // 16:1 — body text, descriptions
          muted:     '#c0c0c0',  // 10:1 — labels, captions
          dim:       '#a0a0a0',  // 7.2:1 — hints, placeholders (AAA minimum)
          faint:     '#808080',  // 5.1:1 — decorative only, never body text
        },
        // ── Accent (indigo) ──
        accent: {
          DEFAULT: '#818cf8',
          hover: '#6366f1',
          muted: 'rgba(129,140,248,0.12)',
        },
        // ── Semantic ──
        success: '#4ade80',
        warning: '#fbbf24',
        danger: '#f87171',
        info: '#60a5fa',
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
      borderRadius: {
        DEFAULT: '8px',
        lg: '12px',
        xl: '16px',
      },
      animation: {
        'slide-in': 'slideIn 0.4s cubic-bezier(0.16,1,0.3,1)',
        'fade-in': 'fadeIn 0.2s ease',
        'pulse-once': 'pulseOnce 0.8s ease',
      },
      keyframes: {
        slideIn: {
          from: { transform: 'translateX(-20px)', opacity: '0' },
          to:   { transform: 'translateX(0)',     opacity: '1' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to:   { opacity: '1' },
        },
        pulseOnce: {
          '0%,100%': { opacity: '1' },
          '50%':     { opacity: '0.6' },
        },
      },
    },
  },
  plugins: [],
}