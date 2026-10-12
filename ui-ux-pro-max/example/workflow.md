# Example Workflow

来源：ui-ux-pro-max/references/ui-guidance.md；原许可保留。仅作演示，不能作为默认参数。

## Example Workflow

**User request:** "Make an AI search homepage。"

### Step 1: Analyze Requirements
- Product type: Tool (AI search engine)
- Target audience: C-end users looking for fast, intelligent search
- Style keywords: modern, minimal, content-first, dark mode
- Stack: Next.js, detected from the project

### Step 2: Generate Design System

```bash
python <skill-dir>/scripts/search.py "AI search tool modern minimal" --design-system -p "AI Search"
```

**Output:** Complete design system with pattern, style, colors, typography, effects, and anti-patterns.

### Step 3: Supplement with Detailed Searches (as needed)

```bash
# Get style options for a modern tool product
python <skill-dir>/scripts/search.py "minimalism dark mode" --domain style

# Get UX best practices for search interaction and loading
python <skill-dir>/scripts/search.py "search loading animation" --domain ux
```

### Step 4: Stack Guidelines

```bash
python <skill-dir>/scripts/search.py "streaming suspense" --stack nextjs
```

**Then:** Synthesize design system + detailed searches and implement the design.

---
