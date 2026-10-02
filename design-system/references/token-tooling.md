# Token 工具契约

生成器支持本仓库示例 JSON 的 `primitive`、`semantic`、`component`、`dark.semantic` 分组；Token 是带 `$value` 的对象，值为 CSS 字符串或有限数值。可用 `$type` 和 `$description` 注释。此工具不是完整 DTCG 实现：阴影/字体/尺寸对象或数组需先转换为合法 CSS 字符串，主题仅支持 `.dark` 的语义覆盖。

引用形式为 `{semantic.color.primary}`，也支持完整值中的引用，如 `1px solid {semantic.color.border}`。生成前检查引用存在、引用循环和命名碰撞；不能把 CSS 声明、注释或闭合大括号塞进值。分号、花括号和 CSS 注释会被拒绝。每个引用输出为 `var(--...)`，而不是把语义值展开成常量。

命名兼容上游示例：primitive 前缀保留，semantic/component 前缀省略，例如 `primitive.color.blue.600` → `--primitive-color-blue-600`，`semantic.color.primary` → `--color-primary`，`component.button.bg` → `--button-bg`。暗色 semantic 使用与明色相同的变量名，组件继续引用它。

生成器只支持 `--format css`。Tailwind v4 在项目 CSS 中声明 `@theme inline` 并映射到语义变量；v3 将 `var(--color-primary)` 等加入已有配置。不要自动创建新的 Tailwind 配置文件来替换项目现有构建。

硬编码扫描仅报告候选；存在合理的边框、图表、坐标或断点常量时按项目规范处理。脚本检查不覆盖计算后的对比度、组件交互和视觉效果。
