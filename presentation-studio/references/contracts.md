# PPT 栈统一契约

只保留影响决策的字段。未知值写 `unknown`，不要为填满表格而猜测。

## deck-brief

```yaml
objective: 观众看完后应发生的变化
audience: 角色、知识水平、主要顾虑
decision_or_action: 需要理解、批准、选择或执行的事项
mode: live | read | hybrid
duration_minutes: 20
slide_count: 12
language: zh-CN
depth: L0 | L1 | L2 | L3 | L4
evidence_cutoff: YYYY-MM-DD
source_scope: 用户资料、允许检索的来源
template: 路径或 none
brand_constraints: 字体、颜色、Logo、保密要求
editability: text | tables | charts | diagrams | full
speaker_support: none | notes | timing | q-and-a
```

## storyboard

每页只保留：`id`、`narrative_role`、`title`、`one_message`、`evidence_ids`、`visual_form`、`detail_destination`、`risk`。`detail_destination` 只能是 `slide`、`notes` 或 `appendix`。

## evidence-ledger

每条证据包含：`id`、`claim`、`source`、`as_of`、`unit`、`scope`、`confidence`、`limitations`。精确数值、产品规格、价格、供应和兼容性结论必须能回到该账本。

## asset-manifest

每个外部视觉素材记录：`id`、`slide`、`source_or_generator`、`license_or_permission`、`crop_intent`、`attribution_location`。

## qa-report

```yaml
- severity: P0 | P1 | P2 | P3
  slide: 7
  category: content | evidence | narrative | visual | accessibility | editability
  finding: 具体问题
  repair: 最小修复
  status: open | fixed | accepted
```

P0 阻止交付；P1 原则上修复；P2 可在不破坏模板时修复；P3 只做润色。

