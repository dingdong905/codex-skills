# Button Example

来源：design-system/references/tailwind-integration.md；原许可保留。仅作演示，不能作为默认参数。

### Button Example

```css
@layer components {
  .btn {
    @apply inline-flex items-center justify-center
           rounded-md font-medium
           transition-colors
           focus-visible:outline-none focus-visible:ring-2
           focus-visible:ring-ring focus-visible:ring-offset-2
           disabled:pointer-events-none disabled:opacity-50;
  }

  .btn-default {
    @apply bg-primary text-primary-foreground
           hover:bg-primary/90;
  }

  .btn-secondary {
    @apply bg-secondary text-secondary-foreground
           hover:bg-secondary/80;
  }

  .btn-outline {
    @apply border border-input bg-background
           hover:bg-accent hover:text-accent-foreground;
  }

  .btn-ghost {
    @apply hover:bg-accent hover:text-accent-foreground;
  }

  .btn-destructive {
    @apply bg-destructive text-destructive-foreground
           hover:bg-destructive/90;
  }

  /* Sizes */
  .btn-sm { @apply h-8 px-3 text-xs; }
  .btn-md { @apply h-10 px-4 text-sm; }
  .btn-lg { @apply h-12 px-6 text-base; }
}
```
