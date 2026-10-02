# 组件实现

shadcn 是项目拥有的组件源码。先读本地 Button/Dialog/Select/Form 等文件，确认实际 prop、variant 和底层行为，再组合。上游示例只是模式，不保证当前项目 API 相同。

## 常见组合

- 主操作用 Button 或语义 button；页面导航用链接。图标按钮提供可访问名称，旁边有等价文字的装饰图标对读屏隐藏。
- 表单保留项目使用的库与 schema。Label、description、error 对应字段 id；失败时保留用户输入，有多个错误时提供可定位摘要或项目既有焦点策略。
- 弹层采用本地实现的 Trigger/Content/Title 等结构，检查可访问名称、Escape、焦点捕获和返回。`asChild` 只在本地 API 实际支持时使用，避免双重 button/link 嵌套。
- Select/Dropdown/Tabs 的 value、选择状态、键盘导航由实际 primitive 处理，不用 CSS class 代替状态语义。
- disabled 使用原生禁用或 primitive 的实际禁用语义，不能只降低 opacity。加载态防止重复提交并提供可辨识状态，不用全局 toast 替代字段错误。
- 大表格考虑语义表头、空/加载/错误状态和局部滚动。组件密度由任务决定，不把所有内容都改成三列卡片。

响应式布局按内容压力点选择断点。grid 可用 `minmax(0, 1fr)`、flex 子项可用 `min-w-0`；长 URL、长翻译文本与放大字号分别验证。需要表格横向滚动时提供清晰边界与操作方式，不全局隐藏 overflow。

## 增加组件

确认项目实际包管理器、组件 registry/alias、已锁定 CLI 版本和所需组件。使用已有项目命令或兼容的指定版本，仅增加目标组件。既有组件文件的修改和覆盖需纳入任务范围，不使用批量全量添加来替代代码阅读。

普通样式改动不需要额外安装 React Hook Form、Zod、next-themes、图标库或动画库；优先使用项目已有能力。
