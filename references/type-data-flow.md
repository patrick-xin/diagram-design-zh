# 数据流（Data Flow）

**最适合**：数据如何**跨组织角色**流过一条管道——谁发起、谁加工、谁发布、谁消费。原型用例是多角色数据平台（管理员 → 工程师 → 分析师 → 使用者）配 4–6 个步骤列。读者要的是"每个阶段**谁在做什么**"，而不只是技术组件。

主体是跨部门**业务流程**（HR 审批、工单流转）时用**泳道**。主体是带类型化载荷（原始文件、表、报表）与角色边界的**数据管道**时才用数据流。

本类型是**参数化**的——§1 的输入 schema 经 §2 公式驱动每个坐标。相同输入的两次产出必须视觉一致。

> **中文重标定**：本类型硬规则：**含汉字 ≥10px**（9px 只留给纯拉丁技术串）。因此全套网格放大：节点 100×64 → **124×80**，列距 112 → **136**，道槽高 80 → **104**（容器 96 + 缝），表头带 36 → **40**。**不许**为迁就小字号把网格缩回去。

---

## 1. 输入——参数契约

```yaml
lanes:                              # 1..4 横向泳道（上→下）
  - { name: ["管理员"],   key: "ADM" }
  - { name: ["工程师"],   key: "ENG" }
  - { name: ["分析师"],   key: "SCI" }
  - { name: ["使用者"],   key: "CON" }

steps:                              # 1..6 步骤列（左→右）
  - { number: "01", label: "采集" }
  - { number: "02", label: "存储" }
  - { number: "03", label: "加工" }
  - { number: "04", label: "分析",  focal: true }   # 焦点步骤头芯片——accent 填充
  - { number: "05", label: "发布" }

nodes:                              # 显式逐格；空格不渲染任何东西
  - { lane: "ADM", step: 0, title: "项目启动",  sub: "建 bucket · 配权限",  tool: "MinIO · LDAP" }
  - { lane: "ADM", step: 1, title: "权限管控",  sub: "桶策略 · 目录同步",   tool: "LDAP 控制台",
      color: "#b85450" }            # 锈红 tint——治理 / 身份关注点
  - { lane: "ENG", step: 0, title: "源头接入",  sub: "外部源 → 原始层",     tool: "NiFi · Kafka",
      chips: {in: "LS", out: "DB"} }                # 实时流入，数据集出
  - { lane: "ENG", step: 1, title: "原始落地",  sub: "原始数据入湖",        tool: "MinIO",
      chips: {in: "DB", out: "DB"} }
  - { lane: "ENG", step: 2, title: "清洗加工",  sub: "原始 → 分析表",       tool: "NiFi · Trino",
      chips: {in: "DB", out: "TB"} }
  - { lane: "SCI", step: 3, title: "探索建模",  sub: "匿名数据 → 洞察",     tool: "JupyterHub",
      chips: {in: "TB", out: "FL"}, focal: true }   # 焦点节点
  - { lane: "SCI", step: 4, title: "发布洞察",  sub: "模型 → 看板",         tool: "Superset",
      chips: {in: "FL", out: "FL"} }
  - { lane: "CON", step: 4, title: "查询消费",  sub: "聚合视图 · 只读",     tool: "Trino",
      chips: {in: "TB", out: "WB"} }                # 分析表入，网页视图出

arrows:                             # 显式边；样式绑定拓扑（见 §3）
  - { from: {lane: "ADM", step: 0}, to: {lane: "ADM", step: 1}, style: "muted" }     # 同道相邻
  - { from: {lane: "ADM", step: 0}, to: {lane: "ENG", step: 0}, style: "trigger" }   # 虚线治理触发
  - { from: {lane: "ADM", step: 1}, to: {lane: "ENG", step: 1}, style: "trigger" }
  - { from: {lane: "ENG", step: 0}, to: {lane: "ENG", step: 1}, style: "muted" }
  - { from: {lane: "ENG", step: 1}, to: {lane: "ENG", step: 2}, style: "muted" }
  - { from: {lane: "ENG", step: 2}, to: {lane: "SCI", step: 3}, style: "accent",     # 焦点跨角色
      label: "匿名数据" }
  - { from: {lane: "SCI", step: 3}, to: {lane: "SCI", step: 4}, style: "muted" }
  - { from: {lane: "SCI", step: 4}, to: {lane: "CON", step: 4}, style: "link" }     # 蓝：已发布

dark: false
```

**保留字段语义：**
- `lanes[k].key`——3 字母角色芯片文（`ADM`、`ENG`……），在该道每个节点内显示。
- `lanes[k].name`——道标签，中文走 eyebrow-zh（sans 12px · 0.3em）。
- `steps[j].focal: true`——恰好**一个**步骤可声明。头芯片 accent 填充。
- `nodes[i].focal: true`——恰好**一个**节点可声明。accent 描边（§5）。
- `nodes[i].chips`——节点数据类型芯片，对象式 `{in: "<CODE>", out: "<CODE>"}`（任一侧可省）。编码取自 §8（`WB`/`DB`/`TB`/`FL`/`LS`）。**位置固定**：入芯片在节点**左下**，出芯片在**右下**。
- `nodes[i].color`——可选**逐节点配色覆盖**，任意 `"#hex"`；跨图一致性推荐 §4.5 色板。

---

## 2. 布局公式——确定性几何

```
lane_pad         = 24                                  # 行容器左右外距
label_col_w      = 160
step_slot_w      = 136                                # 124 节点 + 12 走廊
right_pad        = 32
n_steps          = len(steps)
n_lanes          = len(lanes)

# 画布
viewBox_w        = label_col_w + n_steps * step_slot_w + right_pad   # 5 步 → 872
header_h         = 40
lane_h           = 104                                 # 道槽：容器 96 + 上下缝各 4（道间白缝 8）
has_color_row    = any(node.color or step.color or lane.color in inputs)
legend_h         = 148 if has_color_row else 124      # 有配色时 4 行（行距 30 + 图表间距 32）
viewBox_h        = header_h + n_lanes * lane_h + legend_h            # 4 道 + 配色 → 604

# 步骤表头带（顶部）
step_chip_y      = 8                                   # 20×16 芯片（两位数 24 宽）
step_label_y     = 36                                  # 芯片下方的步骤名

# 道位置与角色行容器
lane_y_top(k)    = header_h + k * lane_h               # 40, 144, 248, 352
lane_box(k)      = rect(lane_pad, lane_y_top+4, viewBox_w−2·lane_pad, 96)   # rx=8
                                                       # 标签区与节点区连体同色
lane_y_mid(k)    = lane_y_top(k) + lane_h/2            # 92, 196, 300, 404
lane_label_x     = (lane_pad + label_col_w) / 2        # 92

# 步骤 / 节点中心 x
step_cx(j)       = label_col_w + 8 + j * step_slot_w + node_w/2      # 230, 366, 502, 638, 774
                                                                      #（内容区 8px 内沟）

# 节点
node_w           = 124
node_h           = 80
node_x(j)        = step_cx(j) - node_w/2               # 168, 304, 440, 576, 712
node_y(k)        = lane_y_top(k) + 12                  # 52, 156, 260, 364

# 图例带（底部）
legend_y_top     = header_h + n_lanes * lane_h         # 456（图表底 → 首行 32px 间距）
legend_row_y     = [legend_y_top + 40, +70, +100, +130] # 文字基线 496, 526, 556, 586
legend_label_x   = lane_pad                            # 24；行内首元素 x = 100
```

### 2.1 背景结构

- 全画布 `paper` 填充。
- **角色行容器**：每条道一个整行矩形 `lane_box(k)`（§2 公式），`rx=8`，`fill ink@0.03`——标签区与节点区连体同色、一体成型，道与道之间靠 8px 白缝分隔。**不画**道分隔横线、标签列竖线、图例顶线（容器边缘自己承担），**不铺**背景点阵（点纹理是 dev/editorial 主题预留，默认不画）。

### 2.2 步骤头芯片 + 步骤名

每步 `j`：芯片（`step_cx±chip_w/2`，y=8，高 16，`rx=8` 药丸），数字锚点 `(step_cx, 19)`，步骤名锚点 `(step_cx, 36)`。

- 默认：芯片填 `ink@0.12`，数字 ink，步骤名 muted。
- 焦点：芯片填 `accent-dark@0.20`，数字与步骤名 accent。
- 步骤名中文 12px · 500 · 0.12em；纯拉丁步骤名走 mono 8px · 0.12em。步骤名 ≤4 字，超长缩写。

### 2.3 道标签

单行中文，eyebrow-zh（sans 12px · 0.3em），fill muted，居中于 `(lane_label_x, lane_y_mid(k) + 4)`——即容器左段（标签区）的中心。逐道 `color` 覆盖（§4）时标签 fill 换 `C`、该道行容器填充换 `C@0.04`。

### 2.4 节点内容（124×80 矩形内）

```
role_chip          rect 20×12 @ (node_x+4,   node_y+4),  rx=2
role_chip_text     居中 (node_x+14, node_y+13)，mono 7px · 600（lane key，纯拉丁）
title              居中 (step_cx,   node_y+30)，node-name 12px · 600（节点名，含汉字）
sub                居中 (step_cx,   node_y+47)，含汉字 sans 12px；纯拉丁 mono 9px
tool               居中 (step_cx,   node_y+62)，同上按语言选行
data chip IN       rect 20×10 @ (node_x+4,   node_y+66)，rx=2      # 入载荷类型
data chip OUT      rect 20×10 @ (node_x+100, node_y+66)，rx=2      # 出载荷类型
```

**角色芯片规则**：节点内徽标显示该节点所属道的 `lanes[k].key`，**不是**步骤号（步骤号在列表头 §2.2）。单个节点被截取出来看时，"谁"仍然自洽。

空格（无节点条目）**什么都不画**——无占位矩形、无芯片、无标签。

---

## 3. 箭头规则（强制）

四种样式，绑定拓扑。连接线画在**所有**节点矩形**之前**（z 序规则）。

| `style` | 描边 | 宽 | 虚线 | marker | 何时必用 |
|---|---|---|---|---|---|
| `muted` | `muted` | 1.0 | — | `arr-muted` | 步骤间 / 道内标准数据交接 |
| `trigger` | `muted` | 1.0 | `4,3` | `arr-muted` | 治理触发——管理员动作启用下游。无标注 |
| `accent` | `accent` | 1.2 | — | `arr-accent` | 焦点跨角色交接。**每图恰好一条**，带标注 |
| `link` | `link` | 1.0 | — | `arr-link` | 已发布 / 对外消费的输出 |

**Defs 块**（必需，三 marker）：

```svg
<defs>
  <!-- dots pattern: reserved for dev/editorial theme, unused by default -->
  <marker id="arr-muted"  markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#565e7e"/></marker>
  <marker id="arr-accent" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#1a4dd9"/></marker>
  <marker id="arr-link"   markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#bf7f0f"/></marker>
</defs>
```

### 3.1 路由规则（不许商量）

- **单拐角路由**：先横后纵。从源节点**右缘**出发；目标同道横向进**左缘**，跨道纵向进**上/下缘**。
- **禁斜线。** 拐角用 8px Q 贝塞尔。
- **同步骤跨道（竖向）**：`(step_cx, 源节点底)` 到 `(step_cx, 目标节点顶)` 直线。
- **跨道跨步骤（焦点）**：右缘出，横走到目标列前 8px，再垂落。
- **标注**：只有 `accent` 箭头带标注。中文 12px · 0.12em，背后垫不透明 `paper` 遮罩 rect。其余箭头一律无标注。
- **z 序**：所有箭头先于任何节点矩形发射（矩形填充盖住线头）。

---

## 4. 组件配色覆盖

节点、道、步骤都可声明可选 `color: "#hex"`。与 process / high-level 同规，跨类型读法一致。

### 4.1 逐节点 `color`

作用于：容器填充 `C@0.06`、容器描边 `C@0.35`、角色芯片填充 `C@0.18`、芯片文字 `C`、节点名 `C`。**子标注与工具行不变**（muted / soft），**数据芯片不变**，**相邻箭头不变**（拓扑驱动）。

### 4.2 逐步骤 `color`

替换步骤头芯片填充为 `C@0.20`、数字与步骤名 fill 为 `C`；图例对应条目同色。

### 4.3 逐道 `color`

替换该道行容器填充为 `C@0.04`、道标签 fill 为 `C`（其余道容器保持 `ink@0.03`）。慎用。

### 4.4 规则

- **焦点元素上禁用。** accent 已经承载焦点信号，焦点上的 `color` 被忽略。
- **箭头上禁用。** 想给边上色就换 §3 的 `style`，不是配色覆盖。
- **每图自定义配色元素 ≤3**（节点+道+步骤合计），焦点对（焦点节点+焦点步骤）之外。
- **子标注与工具行永远 muted/soft。** 只有主身份（描边+芯片+节点名）带色。

### 4.5 语义色板（推荐）

跨图一致——读者扫多张图看到同色同义：

- `sem-security` 锈红——安全 / 身份 / 治理（权限、目录、审批）
- `sem-observability` 蓝灰——可观测 / 质量（监控、质量门禁、血缘）
- `sem-governance` 橄榄绿——数据产品 / 发布（成品输出、上线）
- `sem-backup` 暖棕——备份 / 容灾 / 归档

---

## 5. 焦点规则

数据流图围绕**一条跨角色交接**构建中心论断。三个焦点槽，各恰好一条：

- **一个焦点步骤**（`steps[j].focal`）——通常是分析枢纽（分析、建模……）。头芯片与图例芯片 accent。
- **一个焦点节点**（`nodes[i].focal`）——**接收**焦点交接的节点。accent 描边 + accent 角色芯片 + ink 节点名。
- **一条焦点箭头**（`style: "accent"`）——进入焦点节点的跨角色交接。实线 accent + 短载荷标注（如 `匿名数据`）。

任一焦点槽声明 0 条或 >1 条：停下问用户。

---

## 6. 深色档

**对称换基，α 一律不动**（全套现值照抄 [`assets/example-data-flow-dark.html`](../assets/example-data-flow-dark.html)）：

- 纸 → `#0a0d1b`（页面底 / 行容器上节点底 / 标注遮罩同色成型）；ink 基 → `#e0e4ff` 基（`rgba(224,228,255,X)` 各档）；muted → `#a2a9ce`（连接线 `rgba(162,169,206,0.60)`）；soft → `#787fa2`；accent → `#7d98ff`（焦点 tint 档浅 0.08 → 深 **0.10**，芯片档 0.20 不动）；link 琥珀深色档 `#e8b45a`。
- 系列芯片换深色档（翠绿 `#5fbf93` 等，见 style-guide 系列表深色列），芯片内文字**深字**（`#0a0d1b`）。
- 自定义配色（§4）换对应语义色**深色档**基（如 `sem-security` 深色基 `#bf6561`），α 档不变；深色是 opt-in——用户点名才启用。

---

## 7. 复现清单（输出前逐条核对）

1. `viewBox = "0 0 {viewBox_w} {viewBox_h}"` 由 §2 从 `n_steps`/`n_lanes` 推出。
2. 表头带 `y=0..40`；图例带 `y=legend_y_top..viewBox_h`。
3. 每个节点落在 `(step_cx(j)-62, lane_y_top(k)+12)`，尺寸 `124×80`，上下各留 8px 呼吸空间，整体在 `lane_box(k)` 内。
4. 空格什么都不画。
5. 恰好一个焦点步骤、一个焦点节点、一条 accent 箭头（带 paper 遮罩标注）。
6. 其余箭头全部无标注。
7. 所有箭头先于任何节点矩形。
8. 单拐角路由——无斜线，拐角 Q 贝塞尔 r=8。
9. 自定义配色 ≤3；箭头永不被组件 `color` 传染。
10. 子标注与工具行无论配色如何保持 muted / soft。

---

## 8. 数据类型芯片（入 + 出）

节点底部一对 `20×10 rx=2` 徽标。位置**不可协商**：

- **入芯片** `(node_x+4, node_y+66)`——**左下**，进入节点的载荷格式。
- **出芯片** `(node_x+100, node_y+66)`——**右下**，离开节点的载荷格式。

任一侧可省（源头节点只有出芯片，汇点只有入芯片）。读图变成载荷变换追踪：横扫一行，读每个节点的入 → 出，数据在每次交接时的形状一目了然。

### 芯片编码（与 process 共用同一目录）

| 编码 | 颜色 | 含义 |
|------|-------|---------|
| `WB` | `series-5`（紫棠） | 网页 / 公开数据 |
| `DB` | `series-4`（靛蓝） | 数据集 / 原始文件 |
| `TB` | `series-2`（暖橙） | 分析表 / 就绪数据 |
| `FL` | `series-3`（绛红） | 文件 / 报表 / 导出 |
| `LS` | `series-1`（翠绿） | 实时流 / 事件 / 任务单 |

芯片内文字：mono 7px · 700——浅色档白字，深色档深字（`#0a0d1b`，见 §6）。

芯片直映 style-guide 系列色（「不回填非图表类型」的唯一例外，见 style-guide 系列色板节）。映射锚点取惯例——蓝=库、绿=流，其余为任意但**全库恒定**的分配；调整映射必须同步图例与本目录的 process 侧。

芯片颜色是独立于 §4 逐节点配色的**第二条语义轴**：芯片说*载荷格式*，节点色说*关注点类型*。一个节点可以同时带 `out: TB` 暖橙芯片和锈红描边。

---

## 9. 图例（3 或 4 行横条）

规格按 style-guide「图例条」：顶部**画**分隔线（`rule @0.10`、宽 0.8，首行基线上方 18px）；行类目标签用 `legend-label` 角色（mono 10px · 0.1em），每行一个在 `x=24`（与行容器左缘同一对齐基线）；行内首元素一律 `x=100`；图例项文字用 `legend` 角色（sans 10px）；行距 30（§2 `legend_row_y`），横向单排不竖叠。默认 3 行（步骤 / 数据类型 / 流向）；有 §4 配色时加第 4 行（关注点），`legend_h` 124 → 148。

- **行 1 步骤**：复刻表头芯片与步骤名（芯片按图内实际尺寸 24×16 复刻；步骤名 10px）；焦点步骤保 accent。
- **行 2 数据类型**：图内实际用到的芯片各一枚（16×12 色块 + 编码文字在右侧，不加中文说明）；示例五色齐落（LS/DB/TB/FL/WB）。
- **行 3 关注点**（仅有配色时）：每个自定义色一枚 16×12 色块 + 语义标签（示意芯片的填充 α 与实物节点一致）；accent 焦点色也并排展示。
- **行 4 流向**：实际用到的每种箭头样式一段短线（长 28、基线−4）+ marker + 标签（10px）。

---

## 10. 复杂度预算

| 维度 | 上限 |
|---|---|
| 道（角色） | 4 |
| 步骤 | 6 |
| 每道节点数 | 只算活跃步骤——空格不可见 |
| 带标注箭头 | 1（仅焦点 accent） |
| 每节点数据芯片 | 2 |
| 自定义配色元素（§4） | 3（焦点对之外） |

超 4 道或 6 步：拆两张图（接入管道 / 分析管道）。

---

## 11. 反模式

- **空格放占位盒**——角色不参与的步骤就留空（无盒无字）。
- **多条带标注箭头**——只有焦点跨角色交接配标注。
- **斜线箭头**——永远先横后纵，单右角拐弯。
- **`title` 角色写节点名**——节点名走 `node-name`；`title` 只属于页面 `<h1>`。
- **accent 落在多个节点/步骤/箭头上**——焦点 = 一节点 + 一步骤 + 一箭头，封顶。
- **道标签用 node-name 排**——道标签是标识符，走 eyebrow（中文 eyebrow-zh）。
- **焦点元素上叠 `color`**——被忽略，accent 永远赢。
- **节点配色传染箭头**——连接线拓扑驱动。
- **道染色铺满每道**——染色是信号不是装饰，≤1 道。

---

## 12. 示例

- 浅色：[`assets/example-data-flow.html`](../assets/example-data-flow.html)
- 深色：[`assets/example-data-flow-dark.html`](../assets/example-data-flow-dark.html)
- 页面级：[`assets/example-data-flow-full.html`](../assets/example-data-flow-full.html)
