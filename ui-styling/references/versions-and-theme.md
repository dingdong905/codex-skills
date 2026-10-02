# Tailwind 版本与主题映射

版本从锁文件和已安装包确定；package.json 的版本范围不能单独证明实际版本。主题依赖格式同样以项目样式和组件为准，不能把所有色值都套上 hsl()。

| 项目 | Tailwind v3 | Tailwind v4 |
| --- | --- | --- |
| 样式入口 | `@tailwind base/components/utilities` | `@import "tailwindcss"` |
| 主配置 | 现有 tailwind.config 中的 content/theme/plugins | CSS-first，`@theme` / `@theme inline`；仅在必要时使用兼容 JS 配置 |
| 构建插件 | 现有 PostCSS Tailwind 插件 | 项目选定的 `@tailwindcss/vite` 或 `@tailwindcss/postcss` |
| 自定义颜色 | theme.extend.colors 映射 CSS 变量 | `--color-*` 主题变量；映射其他 CSS 变量时采用 `@theme inline` |
| 扫描来源 | content 配置 | 自动检测及必要的 `@source`；按实际 monorepo/外部组件路径核对 |

不要同时添加 v3 directives、v3 PostCSS 插件和 v4 插件来“兼容”。局部样式任务不等于升级版本任务。

## 与 Token 集成

先用项目原有名称。下例只是映射方式，色值来自品牌或既有 Token：

v4（已有 `--color-primary` 是普通设计 Token 时，用不同名字避免自引用）：

```css
@import "tailwindcss";
@theme inline {
  --color-brand-primary: var(--color-primary);
  --color-brand-foreground: var(--color-primary-foreground);
}
```

使用 `bg-brand-primary text-brand-foreground`。如果项目 shadcn 已采用 `--primary` / `--primary-foreground`，沿用它们和既有 `--color-primary: var(--primary)` 映射，不创建平行系统。

v3：在已有配置中合并，不整体替换：

```js
// theme.extend.colors
{
  'brand-primary': 'var(--color-primary)',
  'brand-foreground': 'var(--color-primary-foreground)'
}
```

变量是完整 CSS color 时直接引用；只有项目存储 HSL channel 时才用 `hsl(var(--primary))`。透明度修饰是否可用取决于颜色格式和配置，必须按实际构建验证。

暗色模式使用项目已有 selector/provider 或媒体策略。只加 `.dark` 颜色但未接通主题状态不是完成主题切换。检查语义前景/背景、组件别名和继承边界；不能假设默认白字在品牌按钮上足够对比。
