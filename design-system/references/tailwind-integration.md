# Tailwind Integration

Map design system tokens to Tailwind CSS configuration.

## CSS Variables Setup

### Base Layer

```css
/* globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* Primitives */
    --color-blue-600: 37 99 235;  /* HSL: 217 91% 60% */

    /* Semantic */
    --background: 0 0% 100%;
    --foreground: 222 47% 11%;
    --primary: 217 91% 60%;
    --primary-foreground: 0 0% 100%;
    --secondary: 220 14% 96%;
    --secondary-foreground: 222 47% 11%;
    --muted: 220 14% 96%;
    --muted-foreground: 220 9% 46%;
    --accent: 220 14% 96%;
    --accent-foreground: 222 47% 11%;
    --destructive: 0 84% 60%;
    --destructive-foreground: 0 0% 100%;
    --border: 220 13% 91%;
    --input: 220 13% 91%;
    --ring: 217 91% 60%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222 47% 4%;
    --foreground: 210 40% 98%;
    --primary: 217 91% 60%;
    --primary-foreground: 0 0% 100%;
    --secondary: 217 33% 17%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217 33% 17%;
    --muted-foreground: 215 20% 65%;
    --accent: 217 33% 17%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62% 30%;
    --destructive-foreground: 0 0% 100%;
    --border: 217 33% 17%;
    --input: 217 33% 17%;
    --ring: 217 91% 60%;
  }
}
```

## Tailwind Config

### tailwind.config.ts

```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [],
}

export default config
```

## HSL Format Benefits

Using HSL without function allows opacity modifiers:

```tsx
// With HSL format (space-separated)
<div className="bg-primary/50">   // 50% opacity
<div className="text-primary/80"> // 80% opacity

// CSS output
background-color: hsl(217 91% 60% / 0.5);
```

## Component Classes

### Button Example

需要具体演示时按需读取 [案例](../example/tailwind-button.md)。

## Spacing Integration

```typescript
// tailwind.config.ts
theme: {
  extend: {
    spacing: {
      // Map to CSS variables if needed
      'section': 'var(--spacing-section)',
      'component': 'var(--spacing-component)',
    }
  }
}
```

## Animation Tokens

```typescript
// tailwind.config.ts
theme: {
  extend: {
    transitionDuration: {
      fast: '150ms',
      normal: '200ms',
      slow: '300ms',
    },
    keyframes: {
      'accordion-down': {
        from: { height: '0' },
        to: { height: 'var(--radix-accordion-content-height)' },
      },
      'accordion-up': {
        from: { height: 'var(--radix-accordion-content-height)' },
        to: { height: '0' },
      },
    },
    animation: {
      'accordion-down': 'accordion-down 0.2s ease-out',
      'accordion-up': 'accordion-up 0.2s ease-out',
    },
  }
}
```

## Dark Mode Toggle

```typescript
// Toggle dark mode
function toggleDarkMode() {
  document.documentElement.classList.toggle('dark')
}

// System preference
if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
  document.documentElement.classList.add('dark')
}
```

## shadcn/ui Alignment

This configuration aligns with shadcn/ui conventions:

- Same CSS variable naming
- Same HSL format
- Same color scale structure
- Compatible with `npx shadcn@latest add` commands

### Using with shadcn/ui

```bash
# Initialize (uses same token structure)
npx shadcn@latest init

# Add components (styled with these tokens)
npx shadcn@latest add button card input
```

Components will automatically use your design system tokens.
