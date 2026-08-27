# 流程（Process）

**最适合**：多角色 / 多部门的顺序业务流程，读者要一眼看到**谁**做**什么**、每步进出**什么数据**、用**什么工具**——而不只是步骤顺序。覆盖职责审计、数据质量门审、跨部门交接图、端到端工作流文档。

数据类型和工具不重要时用**泳道**（更简单）。每步的输入 / 输出载荷与责任团队必须一眼可读时用流程。

本类型是**参数化**的——§1 输入 schema 经 §2 公式驱动每个坐标，相同输入两次产出必须视觉一致。规则结构与 [type-data-flow.md](type-data-flow.md) 互为镜像：配色覆盖、入 / 出芯片语义、复现清单跨类型同读。

> **中文重标定**：硬规则**含汉字 ≥10px**。网格放大为：节点 100×64 → **124×80**，列距 112 → **136**，道高 80 → **96**，表头带 36 → **40**。**不许**为迁就小字号把网格缩回去。

---

## 1. 输入——参数契约

```yaml
lanes:                              # 1..6 横向泳道（上→下）
  - { name: ["研究设计"], key: "RDE" }
  - { name: ["数据工程"], key: "ENG" }
  - { name: ["现场执行"], key: "FLD" }
  - { name: ["质控审核"], key: "QC"  }
  - { name: ["内容发布"], key: "COM" }

steps:                              # 1..7 步骤列（左→右；画布定宽约束）
  - { number: "1", label: "设计" }
  - { number: "2", label: "分配" }
  - { number: "3", label: "采集", focal: true }       # 焦点步骤头芯片——accent 填充
  - { number: "4", label: "审核" }
  - { number: "5", label: "清洗" }
  - { number: "6", label: "制表" }
  - { number: "7", label: "发布" }

nodes:                              # 显式逐格；空格不渲染任何东西
  - { lane: "RDE", step: 0, title: "问卷设计", sub: "抽样 · 题目设计",  tool: "Excel",
      chips: {in: null, out: "LS"} }              # 首步无入芯片
  - { lane: "ENG", step: 1, title: "任务分配", sub: "样本 → 外勤任务",  tool: "调度平台",
      chips: {in: "LS", out: "LS"} }
  - { lane: "FLD", step: 2, title: "数据采集", sub: "→ 10464 户",       tool: "平板 · App",
      chips: {in: "LS", out: "DB"}, focal: true } # 焦点节点
  - { lane: "QC",  step: 3, title: "总部审核", sub: "提交 → 审核通过",  tool: "质控系统",
      chips: {in: "DB", out: "DB"} }
  - { lane: "ENG", step: 4, title: "错误校验", sub: "通过 → 清洁数据",  tool: "SAS · 脚本",
      chips: {in: "DB", out: "DB"} }
  - { lane: "QC",  step: 5, title: "报表制作", sub: "清洁 → 汇总报表",  tool: "Excel · SAS",
      chips: {in: "DB", out: "FL"} }
  - { lane: "COM", step: 6, title: "对外发布", sub: "报表 → 公开发布",  tool: "发布会",
      chips: {in: "FL", out: "WB"} }               # 末步无出芯片也可（对外即终点）

arrows:                             # 显式边；样式绑定拓扑（见 §3）
  - { from: {lane: "RDE", step: 0}, to: {lane: "ENG", step: 1}, style: "normal"    }
  - { from: {lane: "ENG", step: 1}, to: {lane: "FLD", step: 2}, style: "focal-in"  }   # → 焦点
  - { from: {lane: "FLD", step: 2}, to: {lane: "QC",  step: 3}, style: "focal-out" }   # ← 焦点
  - { from: {lane: "QC",  step: 3}, to: {lane: "ENG", step: 4}, style: "normal"    }   # 上行
  - { from: {lane: "ENG", step: 4}, to: {lane: "QC",  step: 5}, style: "normal"    }
  - { from: {lane: "QC",  step: 5}, to: {lane: "COM", step: 6}, style: "normal"    }
  - { from: {lane: "FLD", step: 2}, to: {lane: "ENG", step: 1}, style: "trigger"   }   # 虚线：现场异常上报

dark: false
```

**保留字段语义：**
- `lanes[k].key`——3 字母角色徽标，显示在该道每个节点内。
- `lanes[k].name`——1–2 行道标签；中文走 eyebrow-zh（sans 10px · 500 · 0.3em）。
- `steps[j].focal: true`——恰好**一个**步骤可声明。头芯片 accent。
- `nodes[i].focal: true`——恰好**一个**节点可声明。accent 描边（§5）。
- `nodes[i].chips`——`{in: "<CODE>", out: "<CODE>"}`，任一侧 `null` 省略。编码见 §8。首步节点**省入芯片**，末步节点**省出芯片**。
- `nodes[i].color`——可选逐节点配色覆盖；推荐 §4.5 色板。

---

## 2. 布局公式——确定性几何

数据流同族的道网格，本类型用窄标签列：

```
label_col_w      = 80
step_slot_w      = 128                                # 124 节点 + 4 走廊
n_steps          = len(steps)                         # ≤7（画布定宽约束）
n_lanes          = len(lanes)

# 画布
viewBox_w        = 1000                               # 定死；标题对齐见 style-guide「容器对齐与画布基线」
header_h         = 32                                 # 芯片 0..16、步骤名基线 28
lane_h           = 96
lane_y_top(k)    = header_h + k * lane_h              # 32, 128, 224, 320, 416
lane_y_mid(k)    = lane_y_top(k) + 48                 # 80, 176, 272, 368, 464
lane_label_x     = label_col_w / 2                    # 40
has_color_row    = any(node.color or step.color or lane.color in inputs)
n_legend_rows    = 4 if has_color_row else 3

# 步骤表头带（顶部）
chip_y           = 0                                  # 单数字芯片 20×16（x = step_cx−10）
chip_h / chip_rx = 16 / 8                             # 药丸；双数字宽 24（x = step_cx−12）

# 步骤 / 节点中心 x
step_cx(j)       = label_col_w + 8 + j * step_slot_w + node_w/2   # 150, 278, ..., 918

# 节点
node_w           = 124
node_h           = 80
node_x(j)        = step_cx(j) - node_w/2              # 88, 216, ..., 856（右缘 980）
node_y(k)        = lane_y_top(k) + 8

# 图例带（底部，多行横条）
content_bottom   = header_h + n_lanes * lane_h        # 512（末道分隔线）
legend_line_y    = content_bottom + 56                # 568；贯通 0→1000
legend_row_y(i)  = legend_line_y + 18 + i * 30        # 文字基线 586, 616, 646（+配色行顺延）
legend_label_x   = 0                                  # 行类目标签（mono 10px · 0.1em）
legend_first_x   = 76
viewBox_h        = ceil40(末行基线 + 10)              # 3 行 → 680
```

### 2.1 背景结构

- 全画布 `paper` 实底，**不铺点阵**。
- **交替道染色**：偶数下标道 `ink@0.02`，rect `(80, lane_y_top(k), 920, 96)`——标签列右缘起、到内容右缘。
- **道分隔横线**：`ink@0.10` 宽 0.8，`x=80→1000`，落在每条道界（`header_h, header_h+96, …`）；末线即 `content_bottom`。
- **标签列右缘竖线**：`ink@0.20` 宽 1，`x=80`，`y=header_h..content_bottom`。
- 图例顶线独立锚 `content_bottom + 56`（不与末道分隔线共用）。

### 2.2 步骤头芯片 + 步骤名

每步 `j`：芯片居中 `step_cx`、y=0；数字锚点 `(step_cx, 11)` mono 7px；步骤名锚点 `(step_cx, 28)`，中文 10px · 500 · 0.12em（纯拉丁 mono 8px）。默认芯片 `ink@0.12` + ink 数字与步骤名；焦点芯片 `accent-dark@0.20` + accent 数字与步骤名。步骤名 ≤4 字。

### 2.3 道标签

单行中文 eyebrow-zh（sans 10px · 500 · 0.3em）fill muted，居中 `(40, lane_y_mid(k) + 4)`。逐道 `color` 覆盖时 fill 换 `C`、道染色换 `C@0.04`。

### 2.4 节点内容（124×80 内）

与数据流 §2.4 同一布局：角色芯片 20×12（mono 7px lane key）在左上；节点名 node-name 14px · 600 基线 `node_y+30`；子标注 `node_y+47`（汉字 12px / 拉丁 mono 9px）；工具行 `node_y+62`（同语言规则）；入芯片 `(node_x+4, node_y+66)`、出芯片 `(node_x+100, node_y+66)` 各 20×10。

**角色芯片规则**：徽标渲染所属道的 `lanes[k].key`，不是步骤号（步骤号在列表头）。节点被单独截取时"谁"仍自洽。

空格**什么都不画**。

**芯片与工具行碰撞规则**：芯片占 `node_y+66..76`，工具行基线 `node_y+62`。若节点名确需两行（罕见），`node_h` 加到 88 **或**该节点省芯片。默认行为：碰撞时省芯片。

---

## 3. 连接线规则（强制）

三种样式，绑定拓扑。连接线画在**所有**节点矩形**之前**（z 序规则）。

| `style` | 描边 | 宽 | 虚线 | marker | 何时必用 |
|---|---|---|---|---|---|
| `normal` | `muted` | 1.0 | — | `arrow` | 步骤 / 角色间标准交接。无标注 |
| `focal-in` / `focal-out` | `accent` | 1.2 | — | `arrow-accent` | 终点是焦点节点（in）或起点是焦点节点（out）的每条边 |
| `trigger` | `muted` | 1.0 | `4,3` | `arrow-sm` | 编排触发（调度 → 工具、人工干预 → 上游）。无标注 |

**Defs 块**（必需，三 marker）：

```svg
<defs>
  <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">
    <circle cx="11" cy="11" r="0.8" fill="rgba(41,49,79,0.10)"/>
  </pattern>
  <marker id="arrow"        markerWidth="8" markerHeight="6" refX="7" refY="3"   orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#565e7e"/></marker>
  <marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3"   orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#1a4dd9"/></marker>
  <marker id="arrow-sm"     markerWidth="6" markerHeight="5" refX="5" refY="2.5" orient="auto"><polygon points="0 0, 6 2.5, 0 5" fill="#565e7e"/></marker>
</defs>
```

### 3.1 路由规则（不许商量）

**单拐角直角**：右缘出 → 走廊 → 目标在下进**顶**、在上进**底**。

- 源侧：`(node_x + 124, lane_y_mid(src))`——节点右缘、纵向中点。
- 目标侧：下行进 `(step_cx(dst), node_y(dst))`；上行进 `(step_cx(dst), node_y(dst) + 80)`。
- 拐角 8px Q 贝塞尔。
- 同道相邻步骤（罕见）：源右到目标左的横 `<line>`。
- **禁斜线。禁左缘进入。禁从节点顶 / 底出发。**

```svg
<!-- 下行（目标道在源道下方） -->
<path d="M {右缘x},{src_cy} H {dst_cx - 8} Q {dst_cx},{src_cy} {dst_cx},{src_cy + 8} V {dst_top}"
      fill="none" stroke="…" stroke-width="…" marker-end="…"/>

<!-- 上行（目标道在源道上方） -->
<path d="M {右缘x},{src_cy} H {dst_cx - 8} Q {dst_cx},{src_cy} {dst_cx},{src_cy - 8} V {dst_bottom}"
      fill="none" stroke="…" stroke-width="…" marker-end="…"/>

<!-- 同道（相邻步骤） -->
<line x1="{src右}" y1="{lane_cy}" x2="{dst左}" y2="{lane_cy}" stroke="…" stroke-width="…" marker-end="…"/>
```

- **z 序**：所有 `<path>` / `<line>` 连接线先于任何节点 `<rect>`。
- **marker**：每条路径恰好一个 `marker-end`，绝不用 `marker-start`。
- **标注**：流程箭头默认全部无标注——步骤号 + 角色道已承载语义，每条箭头都挂标签是噪音。只有表达**非步骤概念**（返工回路、升级上报）的箭头才标注：中文 12px + paper 遮罩。

### 3.2 交叉

避免。走廊 x（目标节点前 8px）是唯一路由列——两条箭头会在那交叉时，**换步骤分配**或**拆两张图**，不绕行。交叉会掩盖真实控制流。

---

## 4. 组件配色覆盖

与 [type-data-flow.md](type-data-flow.md) §4 逐条同规：逐节点 / 逐步骤 / 逐道 `color: "#hex"`；作用面（容器填充 0.06 / 描边 0.35 / 角色芯片 0.18 / 节点名着色，子标注工具行不变）；焦点元素禁用；箭头禁用；每图 ≤3 个自定义配色元素；语义色板统一：

- `sem-security` 锈红——安全 / 身份 / 治理（权限、培训、审批）
- `sem-observability` 蓝灰——可观测 / 质量（质量门禁、校验、监控）
- `sem-governance` 橄榄绿——数据产品 / 发布（成品输出、上线）
- `sem-backup` 暖棕——备份 / 容灾 / 归档

---

## 5. 焦点规则

三个焦点槽，各恰好一条：

- **一个焦点步骤**——通常是分析或判定枢纽（测试、审批、校验）。头芯片与图例芯片 accent。
- **一个焦点节点**——**接收**关键交接的节点。accent 描边 + accent 角色芯片 + ink 节点名（节点名保持 ink 保可读；accent 只走描边与芯片）。
- **一组焦点箭头**——进出焦点节点的边（`focal-in` / `focal-out`）。accent 实线。

任一焦点槽 0 条或 >1 条：停下问用户。

---

## 6. 深色档

按 [style-guide.md](style-guide.md) 深色反转规则整体换档：ink 基 `ink@X` 各档 → 纸色基 `paper-dark@X`（同透明度）；`accent` → `accent-dark`；节点默认填充白 → `paper-dark@0.05`；焦点节点填充 `accent-dark@0.08` → `accent-dark@0.12`；自定义配色 `C` 提亮 ~15%。深色是 opt-in。

---

## 7. 复现清单（输出前逐条核对）

1. `viewBox = "0 0 1000 {viewBox_h}"` 由 §2 推出（高按 40 步进收口）。
2. 表头带 `y=0..32`（芯片 0..16、步骤名基线 28）；图例带 `y=legend_line_y..viewBox_h`。
3. 每个节点落在 `(step_cx(j)-62, lane_y_top(k)+8)`，尺寸 `124×80`。
4. 空格什么都不画。
5. 恰好一个焦点步骤、一个焦点节点。
6. 触到焦点的箭头用 `focal-in` / `focal-out`（accent）。
7. 其余箭头 `normal`（muted 实线）或 `trigger`（muted 虚线），默认无标注。
8. 所有箭头先于任何节点矩形。
9. 单拐角直角路由——右出、顶 / 底入；无斜线；拐角 Q 贝塞尔 r=8。
10. 自定义配色 ≤3；子标注与工具行永远 muted / soft；首步入芯片省、末步出芯片省。

---

## 8. 数据类型芯片（入 + 出）

与数据流共用同一目录（见 [type-data-flow.md](type-data-flow.md) §8 编码表：`WB` / `DB` / `TB` / `FL` / `LS`）。

- **入芯片** `(node_x+4, node_y+66)`——**左下**，进入节点的载荷。
- **出芯片** `(node_x+100, node_y+66)`——**右下**，离开节点的载荷。
- 任一侧可省（首末步、未知载荷）。芯片内文字白、mono 7px · 700。

芯片颜色是独立于 §4 逐节点配色的**第二条语义轴**：芯片说*载荷格式*，节点色说*关注点*。可以并存。

---

## 9. 图例（3 或 4 行横条）

与数据流 §9 同构：行 1 **步骤**（复刻表头芯片 20×16、数字基线 −1、步骤名距芯片 28）、行 2 **数据类型**（实际用到的芯片 + `左入 · 右出` 提示）、行 3 **关注点**（仅有配色时）、行 4 **流向**（实际用到的箭头样式各一段，线样 28 长、基线−4）。行类目标签 `legend-label` 角色（mono 10px · 0.1em）`x=0`、行内首元素一律 `x=76`、行距 30（§2 `legend_row_y`），行内横排不竖叠。

---

## 10. 复杂度预算

| 维度 | 上限 |
|---|---|
| 道（角色） | 6 |
| 步骤 | 7（画布 1000 定宽约束：末节点右缘 ≤980） |
| 每道节点数 | 只算活跃步骤——空格不可见 |
| 带标注箭头 | 默认 0（只给非步骤概念标注） |
| 每节点数据芯片 | 2（入 + 出） |
| 自定义配色元素 | 3（焦点对之外） |

超 6 道或 7 步：拆总览 + 细节两张。

---

## 11. 反模式

- **空格放占位盒**——角色不参与的步骤就留空。
- **斜线箭头**——跨道连接线必须恰好一个直角拐。
- **纵向主导的箭头从左右缘进入**——永远右出、顶 / 底入。
- **多个焦点步骤 / 焦点节点**——挑唯一最关键的那个操作。
- **道没有标签**——每条道必须标明角色。
- **所有箭头一个样式**——编排触发必须虚线，与数据交接区分。
- **焦点元素叠 `color`**——忽略，accent 赢。
- **节点配色传染箭头**——连接线拓扑驱动。
- **道染色铺满**——≤1 道。
- **两行节点名还硬塞芯片**——省芯片或缩成一行。
- **超过 7 步不拆图**——总览 + 细节成对（画布 1000 定宽，末节点右缘 ≤980）。

---

## 12. 示例

- [`assets/example-process.html`](../assets/example-process.html) — 季度入户调查端到端：5 角色 × 7 步接力（设计→分配→采集·焦点→审核→清洗→制表→发布），入 / 出芯片全程追踪载荷，现场异常上报为虚线触发。
