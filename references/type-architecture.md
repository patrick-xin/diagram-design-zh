# 架构图

**最适合**：系统总览、数据流、集成关系、基础设施拓扑。

## 布局约定

- 按 tier 或信任边界分组：前端 → 后端 → 数据；公网 → 内网。
- 主流程单一方向：左→右 或 上→下，选定后整图不变。
- **先画线后画盒**。z-order：背景 → 分区 → 连接线 → 节点 → 文字。
- 焦点节点 1–2 个（accent）：主集成点 / 主存储 / 关键决策。

## 连接线

**正交圆角肘线 r=8 是强制的**——对角斜线是硬伤（SKILL.md §8 全文适用）：

```svg
<!-- right+down: from (x1,y1) to (x2,y2), mid = (x1+x2)/2 -->
<path d="M x1,y1 H mid-8 Q mid,y1 mid,y1+8 V y2-8 Q mid,y2 mid+8,y2 H x2"
      fill="none" stroke="…" stroke-width="1.2" marker-end="url(#arrow)"/>
```

右+上翻转纵向符号。两端同 x 或同 y 时用 `<line>`。

**箭头标签**：`paper` 遮罩 + 6–10px 净空；中文标签 sans 12px / 0.12em，短嵌线标签可用 10px / 0.12em；纯拉丁技术串 mono 8px / 0.06em。标签放竖段上（水平居中于 mid、垂直落在两弯角之间）或横段上方居中；短嵌线标签以遮罩压在线段中央。

**端口选择——纵向连接走上下边**。目标明显在源的上/下方时，从源的顶/底边出、目标的底/顶边入，单弯 L 路径：

```svg
<!-- enter from below (destination above source) -->
<path d="M x1,y_src H x2-8 Q x2,y_src x2,y_src-8 V y_dst"
      fill="none" stroke="…" stroke-width="1.2" marker-end="url(#arrow)"/>
```

左右侧口只留给横向主流程——主要纵向的路从侧面进节点，看着像箭头扎穿了节点正面。

**虚线路径同规则**：`stroke-dasharray="4,3"`、stroke-width 1；路由与端口规则和实线完全一致——dash 只表达语义权重，不是另一套路由语法。

## 交越跳线

两线必交时，给**次要的那条**加 8px 半圆跳线，只跳一条：

```svg
<!-- horizontal path hops over a vertical crossing at x=cx -->
<path d="M x1,y H cx-8 a 8,8 0 0,1 16,0 H x2" fill="none" stroke="…"/>
```

`a 8,8 0 0,1 16,0` 是 SVG 弧：rx=ry=8、large-arc=0、sweep=1（向上拱）、前进 16px——在交点上方拱出半径 8 的半圆。垂直路径跳水平线用 `a 8,8 0 0,0 0,16`（向下拱，改在竖线段上）。

挑哪条跳：语义更次要的（被动、回写）、或视觉更轻的（虚线、muted）。两条都跳等于没跳。

## 节点

- 填充与描边查 style-guide 节点表；节点 ≤9。
- 结构：`paper` 底衬 → 主题填充矩形（rx=6）→ 左上角标框 → 名称 → 子标签。字号坡道现值一律查 style-guide（含汉字 ≥10px 是硬线）。
- 链路编号：右下角大号序号水印（mono 32px）——backend 节点 `ink @ 5%`，focal 节点 `accent @ 8%`，序号按请求链路顺序递增。
- 节点宁宽勿挤：两端各留 ≥12px。

## 分区

同一 tier 或信任边界的 **2 个以上节点**用分区框圈起来——分区画在连接线与节点**之前**（z-order：背景 → 分区 → 连接线 → 节点 → 文字）：

```svg
<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8"
      fill="none" stroke="{rule}" stroke-width="0.8"/>
<rect x="{lx}" y="{y+4}" width="{lw}" height="14" rx="2" fill="{paper}"/>
<text x="{label_cx}" y="{y+14}" fill="{ink @ 0.40}" font-size="10"
      text-anchor="middle" letter-spacing="0.1em">生产环境</text>
```

颜色一律用角色占位（`rule` / `paper` / `ink @ 档`），现值查 style-guide——文档不维护颜色副本。

- 摆位：分区顶到首个节点留 ≥16px——分区标签就住在这条边距里；zone `y` = 首个节点 top − 32，标签遮罩 `y` = zone_y + 4（文字基线 = 遮罩 y + 10）。
- 分区不上底色——层级靠节点自身的填充与描边；分区只画发丝线（`rule`）。
- 分区 ≤3 个（再多就该用泳道图）。
- 标签用环境名 / 信任域（生产环境 / 内网区）；纯拉丁缩写（PROD / VPC）用 mono。

## 反模式

- 全员焦点色——层级崩塌。
- 语境已明还画双向箭头。
- 图例飘在绘图区里（图例放底部横条）。
- 斜线连接、无遮罩的箭头标签。

## 示例

- [`assets/example-architecture.html`](../assets/example-architecture.html) — 标准浅色
- [`assets/example-architecture-dark.html`](../assets/example-architecture-dark.html) — 深色档
- [`assets/example-architecture-full.html`](../assets/example-architecture-full.html) — 页面级
