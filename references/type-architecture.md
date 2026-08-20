# 架构图（Architecture）

**最适合**：系统总览、数据流、集成关系、基础设施拓扑。

## 布局约定

- 按 tier 或信任边界分组：前端 → 后端 → 数据；公网 → 内网。
- 主流程单一方向：左→右 或 上→下，选定后整图不变。
- **先画线后画盒**。z-order：背景 → 分区 → 连接线 → 节点 → 文字。
- 焦点节点 1–2 个（accent）：主集成点 / 主存储 / 关键决策。
- 分区虚线框 ≤3 个（再多就该用泳道图）；分区标签压在 `paper` 色遮罩上，分区顶部到首个节点留 ≥16px。

## 连接线（强制）

**正交圆角肘线 r=8 是强制的**——对角斜线是硬伤（SKILL.md §8 全文适用）：

```svg
<!-- 右+下：从 (x1,y1) 到 (x2,y2)，mid = (x1+x2)/2；右+上翻转纵向符号 -->
<path d="M x1,y1 H mid-8 Q mid,y1 mid,y1+8 V y2-8 Q mid,y2 mid+8,y2 H x2"
      fill="none" stroke="…" stroke-width="1.2" marker-end="url(#arrow)"/>
```

两端同 x 或同 y 时用 `<line>`。

**端口选择——纵向连接走上下边**。目标明显在源的上/下方时，从源的顶/底边出、从目标的底/顶边入，单弯 L 路径：

```svg
<!-- 从下方进入目标（目标在源上方）：先横后竖 -->
<path d="M x1,y_src H x2-8 Q x2,y_src x2,y_src-8 V y_dst"
      fill="none" stroke="…" stroke-width="1.2" marker-end="url(#arrow)"/>
```

左右侧口只留给横向主流程——主要纵向的路从侧面进节点，看着像箭头扎穿了节点正面。

**虚线路径同规则**：`stroke-dasharray="4,3"`、stroke-width 1，路由与端口规则和实线完全一致。

**交越跳线**：两线必交时，给次要线（更轻语义、虚线、muted）加 8px 半圆跳线，只跳一条：

```svg
<!-- 水平路径在 x=cx 处跳过竖线 -->
<path d="M x1,y H cx-8 a 8,8 0 0,1 16,0 H x2" fill="none" stroke="…"/>
```

**箭头标签**：`paper` 遮罩 + 6–10px 净空；中文标签 sans 12px / 0.12em，拉丁 mono 8px / 0.06em。标签放竖段中点或横段上方居中。

## 节点

- 处理查 style-guide 节点表；节点 ≤9。
- 结构：纸色底衬 → 主题填充矩形（rx=6）→ 左上角标框（拉丁 mono 7–8px / 中文 sans 12px·0.3em）→ 名称（sans 14px·600）→ 子标签（技术串 mono 9px / 中文 sans 12px）。
- 焦点节点可加右上角大号序号（mono 32px，accent @ 10% 透明度）——最多一处。
- 节点宁宽勿挤：两端各留 ≥12px。

## 分区

```svg
<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8"
      fill="none" stroke="rgba(41,49,79,0.10)" stroke-width="0.8"/>
<rect x="{lx}" y="{y+4}" width="{lw}" height="12" rx="2" fill="#ffffff"/>
<text … fill="rgba(41,49,79,0.40)" letter-spacing="0.14em">PROD</text>
```

- 分区不上底色——层级靠节点自身的梯子填充与描边，且遮罩才能统一用纸色；分区只画发丝线（`rule`）。
- 分区标签：拉丁 mono（PROD / VPC），中文 sans 12px·0.3em（生产环境 / 内网区）。

## 反模式

- 全员焦点色——层级崩塌。
- 语境已明还画双向箭头。
- 图例飘在绘图区里（图例放底部横条）。
- 斜线连接、无遮罩的箭头标签。
- **中文文本用西文字体栈**（Geist / Inter / Roboto）——汉字全部掉系统默认，是本技能第一硬伤。
- 中文标签 <10px。

## 示例

- [`assets/example-architecture.html`](../assets/example-architecture.html) — AI 客服平台生产架构（中文锚点）
