# 数据平台集成图（DP integration）

**最适合**：数据平台的集成拓扑——哪些源系统接入、哪些消费面接出、各自走什么协议。中心辐射布局包在一个明确的**数据平台**层里；没有时间 / 阶段轴。

问题是「**这个平台暴露哪些面、走什么线**」而不是「数据怎么流过阶段」时用。

本类型是**参数化**的——同 type-high-level.md，每个坐标都由一个小输入 schema 推导。同一输入两次生成必须产出视觉一致的 SVG。

---

## 1. 输入——参数契约

```yaml
sources:                            # 左列，0..6 个节点
  - { name: "业务数据库", type: "db",   subtitle: "客户主数据",
      connects_to: [{to: "对象存储", label: "JDBC"}] }
  - { name: "POS 导出",  type: "sftp",  subtitle: "每日 CSV 批次",
      connects_to: [{to: "对象存储", label: "CSV"}] }
  - { name: "事件流",    type: "stream", subtitle: "近实时事件",
      connects_to: [{to: "对象存储", label: "EVENTS"}] }

platform:
  name: "数据平台"                   # 分区标签（顶部边框断口上的 paper 遮罩）
  rows:                             # 从上到下；bar 或 row
    - { kind: bar, name: "调度器", subtitle: "调度 · 重试 · 血缘", role: "DAG" }
    - { kind: row, nodes: [
        { name: "对象存储", role: "STORE", subtitle: "版本化数据对象", focal: true },
        { name: "查询引擎", role: "SQL",   subtitle: "联邦 SQL 访问",  focal: true }
      ]}

consumers:                          # 右列，0..6 个节点
  - { name: "BI 工具",   type: "chart",   subtitle: "看板 · 报表",
      connects_from: [{from: "查询引擎", label: "JDBC"}] }
  - { name: "笔记本",    type: "notebook", subtitle: "Python · 探索",
      connects_from: [{from: "查询引擎", label: "KERNEL"}] }
  - { name: "合作方 API", type: "api",    subtitle: "受控数据产品",
      connects_from: [{from: "查询引擎", label: "HTTPS"}] }

footer:                             # 0..N 条横切条，垫在分区下方（全宽）
  - { name: "统一身份", subtitle: "SSO · 服务身份 · 策略组",
      color: "#b85450" }            # 铁锈红——安全关切
  - { name: "集中日志", subtitle: "平台事件 · 审计追踪 · 留存",
      color: "#5a7d9a" }            # 岩蓝——可观测关切

internal_connections:               # 平台组件间的显式边
  - { from: "对象存储", to: "查询引擎", style: "primary", label: "READ" }
  - { from: "调度器",   to: ["对象存储", "查询引擎"], style: "trigger" }

dark: false
```

**`platform.rows` 的 `kind` 值：**

- `bar`——整分区宽的横条。默认高 44px（焦点条 56px）。必填 `name`；可选 `subtitle` / `role` / `color` / `focal`。
- `row`——N 个节点沿分区宽均布。必填 `nodes` 列表；每个节点有 `name`，可选 `role` / `subtitle` / `color` / `focal`。

**源 / 消费 `type` → 图标映射**（延伸自 primitive-icons.md，点名才上图标）：`db` 圆柱、`sftp` 折角文件夹、`stream` 波形线、`mail` 信封、`mainframe` 通风机柜、`monitor` 显示器、`notebook` 笔记本、`chart` 柱形、`globe` 地球、`api` 花括号、`key` 钥匙。也接受 primitive-icons.md 里的显式图标名。底条图标见 §8。

**逐组件 `color: "#hex"`** 可选，加在任何节点 / 横条 / 底条上，见 §4。

---

## 2. 布局公式——确定性几何

```
# 画布（宽 1000 定死；容器四件套与标题对齐见 style-guide「容器对齐与画布基线」）
viewBox_w        = 1000
n_sources / n_consumers / n_footer

# 两侧列（源在左、消费在右；内容 x=0 起排）
col_top          = 28
col_node_h       = 64
col_gap          = 24                    # 步长 = 64 + 24 = 88
left_x / left_w  = 0 / 160
right_x / right_w = 800 / 160
col_node_y(k)    = col_top + k * 88
col_node_cy(k)   = col_node_y(k) + 32    # 60, 148, 236
col_bottom       = col_node_y(n−1) + 64  # 3 节点 → 268

# 平台分区
zone_x / zone_w  = 220 / 536
zone_y           = 8
zone_h           = max(336, col_bottom + 8 − zone_y)
zone_cx          = 488
zone_pad_x       = 16                    # 横条在分区内的左右内缩
zone_label_y     = zone_y + 3            # 标签骑在顶边框上、居中于 zone_cx、paper 遮罩垫底

# 底条（分区下方——每条横切关切一行全宽条）
footer_top       = zone_y + zone_h + 52  # 分区下方 52px（标准 → 396）
footer_bar_h     = 56
footer_bar_x     = 0                     # 与源列左缘对齐
footer_bar_w     = 960                   # 与消费列右缘对齐
footer_gap       = 8

# 图例条（style-guide「图例条」规格）
content_bottom   = N_footer > 0 ? footer_bottom : zone_y + zone_h
legend_line_y    = content_bottom + 56   # 标准 → 516 + 56 = 572；线贯通 0→1000
legend_baseline  = legend_line_y + 18    # 590
viewBox_h        = ceil40(legend_baseline + 10)   # 600

# platform.rows 在分区内的高度
bar_h_focal      = 56
bar_h_default    = 44
row_h            = 72
row_gap          = 16
```

### 2.1 行摆放（游标算法）

`platform.rows` 自上而下分配。唯一 `row`（或首个 row）锚到侧列第 2 行、连线保持水平：

```
primary_row_idx  = 首个 kind=row 的下标
primary_row_top  = zone_y + 104          # 112——与侧列第 2 行（cy=148）连线水平

# 主行上方：倒序上堆
# 主行下方：依次下堆
# 约束：y <= zone_y + zone_h
```

标准形状（上条 / 双节点主行，即 shipped 示例）产出：调度器条 y=52 h=44（非焦点）、主行 y=112 h=72（两个焦点节点）。若再声明底部横条，按同一游标继续下堆；底部横条垫在分区下方（§2 footer 公式），与侧列末行同读一个 y 带，视觉上是侧列末行的兄弟。

### 2.2 `row` 内的节点摆放

```
N            = len(row.nodes)
node_w       = 160
node_x(j)    = zone_cx − (N·160 + (N−1)·16)/2 + j·176    # N=2 → 320, 496
```

节点 cx（400 / 576）沿分区中线对称，trigger 下扎线从条底落在 `node_cx(target)`。均布公式与固定 x 定制列位（连线走廊方便为准）**两种都合法**；公式是新图默认。偏差在渲染的 SVG 里加注释说明。

### 2.3 横条（整分区宽）

```
bar_x = zone_x + zone_pad_x      # 236
bar_w = zone_w - 2*zone_pad_x    # 504
```

`focal: true` 的条用 `bar_h_focal=56` + accent 样式（填充 `accent@0.08`、描边 accent）。非焦点条 `bar_h_default=44` + 中性样式（填充 `ink@0.05`、描边 `ink@0.30`）。

### 2.4 源 / 消费摆放（侧列）

固定 `w=160 h=64`，步长 88。填充 `muted@0.05`、描边 `soft` 1px。

### 2.5 图例条与页面标题

图例按 style-guide「图例条（底部横条）」规格：分隔线 `y = 最下内容底 + 56`（标准 516+56=572）、`x` 贯通 0→1000；「图例」标签 `legend-label` 角色（mono 10px · 0.1em）、fill muted、`x=0`——与源列左缘同一对齐轨、基线 = 线 +18；标签 → 首个元素 72px；图例项 `legend` 角色（sans 10px）与标签同基线，色块 16×12（`y = 基线−10`）、线样长 28（`y = 基线−4`）、带对应箭头 marker；色样填充 α 与图内实物一致。

页面层：eyebrow 格式「图内容语境 · 图类型」（如 数据平台 · 集成图），不带技能名；标题—图—图例标签的三层一线由容器四件套承担（`.frame padding-left 4%`、SVG 内容 x=0 起排、overflow visible，见 style-guide「容器对齐与画布基线」）。

---

## 3. 连线规则（强制）

五种样式，绑定拓扑。焦点触及、横条发出、Trino → 消费这三类边的样式**不许**用户覆写——规则定死。

| `style` | 描边 | 宽 | 虚线 | 箭头 | 何时必须 |
|---|---|---|---|---|---|
| `primary` | `accent` | 1.4 | — | `arrow-accent` | 任一端是 `focal: true` 组件的边。**外加**每条 Trino → 消费边（服务流规则）。 |
| `secondary` | `muted` | 1.2 | — | `arrow` | 平台内部组件间、不触焦点的源 → 平台边的默认。 |
| `federated` | `accent`（link） | 1.0 | `4,3` | `arrow-link` | 联邦查询（如源库 → Trino）。 |
| `trigger` | `muted` | 1.0 | `4,3` | `arrow-sm` | 每条从 `kind: bar` 组件发出的边（Airflow 下扎）。**无标签。** |
| `auth` | `accent` | 1.2 | `5,4` | `arrow-accent` | 每条从底条上行到分区下缘的边。**绝不指向具体组件。** |

**defs 块**（三支常备；用到 `federated` 样式时补 `arrow-link`——几何同 `arrow`、fill 同 accent；不预定义未用的箭头）：

```svg
<defs>
  <marker id="arrow"        markerWidth="8" markerHeight="6" refX="7" refY="3"   orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#565e7e"/></marker>
  <marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3"   orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#1a4dd9"/></marker>
  <marker id="arrow-sm"     markerWidth="6" markerHeight="5" refX="5" refY="2.5" orient="auto"><polygon points="0 0, 6 2.5, 0 5" fill="#565e7e"/></marker>
</defs>
```

### 3.1 出 / 入边（不可谈判）

| 边类 | 源出边 | 目标入边 |
|---|---|---|
| 源 → 平台组件 | 源**右** | 目标**左** |
| 平台 → 平台（同行） | **右** | **左** |
| 横条 → 行节点（竖直下扎） | 条**底**、在 `node_cx(target)` | 目标**顶** |
| 平台 → 消费 | 平台组件**右** | 消费**左** |
| 底条 → 分区 | 底条**顶**（`footer_auth_x(k)`） | 分区下缘 `y = zone_y + zone_h` |
| 底条 → 具体组件 | **禁止** | |

### 3.2 路由

- 正交肘线、每路径至多两弯；每个弯 Q 贝塞尔 r=8。
- **扇出错开**：一个节点向同侧 N 个目标扇出时，出边 y 沿节点边缘高均布错开（如查询引擎 → 3 个消费从 y=124, 148, 172 出）；竖直段走在分区缘与消费列之间的走廊（740..800）里，同样错 y。
- **z 序**：所有连线先于任何 rect（节点填充掩蔽线端）。分区框也在连线**之前**——线压过分区边框走，不被边框切断。
- **半透明节点垫纸色 mask**：淡染样式框掩不住线——每个可能被线经过的盒子（调度条、底条、横条）先输出同几何的 `paper` 色不透明矩形，再叠淡染框，线才真正「藏在框后」。穿越不为终点（如 AUTH 虚线穿过身份条）也靠这层 mask 隐去；跨盒穿越的 mask 要**延伸盖住盒间缝隙**，否则缝里露出的残段会读成一根不存在的假连线。
- **标签**：`primary` / `secondary` / `federated` / `auth` 每条都要协议标签（拉丁 mono 9px 或中文 sans 12px，paper 色遮罩、线上方 6–10px 净空）。源侧标签贴**源端**同一列（出源盒 12px），mask 不越过分区边框、不贴后画盒子的角。`trigger` 边无标签。

### 3.3 底条 → 分区干线

N=1 条底：单根竖线 `x = zone_cx`，从 `footer_y(0)` 到 `zone_y + zone_h`。

N≥2 条：AUTH 线错开免叠。底条 k：

```
footer_auth_x(k) = zone_cx + (k - (N-1)/2) * 32     # 每条 32px 步长
```

例：N=1 → 488；N=2 → 472, 504；N=3 → 456, 488, 520。每根 AUTH 线从 `(footer_auth_x(k), footer_y(k))` 上行到 `(footer_auth_x(k), zone_y + zone_h)`。AUTH 标签贴在箭头头上方、分区下缘处。

### 3.4 交越

避免。先试走廊 x 重路由再接受交越。实在免不了，后画的线加 6px 弧跳。

---

## 4. 组件颜色覆盖（对齐 type-high-level.md §4）

任何源、消费、平台组件（节点或条）、底条都可带可选 `color: "#hex"`。

| 元素 | 浅色 | 深色 |
|---|---|---|
| 容器填充 | `C@0.06` | `C_light@0.10` |
| 容器描边 | `C@0.35`（节点宽 1、条 0.8） | `C_light@0.45` |
| 角标芯片描边 / 文字 | `C@0.40` / `C@0.85` | `C_light@0.55` / `C_light` |
| 名字文本 | `C` | `C_light` |
| 副标文本 | **不变**（muted） | **不变**（muted） |
| 触达该组件的连线 | **不变**——拓扑驱动 | **不变** |

`C_light` = 同 hex 提亮 ~15%。

**规则：**

- **焦点组件上禁用。** accent 恒赢——焦点上的 `color` 被忽略。
- **连接线上禁用。** 想要彩边去挑 §3 的 `style`，不是颜色覆盖。
- 自定义色组件每图 **≤ 2**（焦点对之外）。

**语义色板**：`sem-security` 铁锈红（安全 / 身份）、`sem-observability` 岩蓝（可观测）、`sem-governance` 橄榄绿（治理 / 血缘）、`sem-backup` 暖棕（备份 / 灾备）。

---

## 5. 焦点规则

**恰好两个焦点组件。** 缺省：存储枢纽（MinIO / S3 之流）与联邦引擎（Trino / Dremio 之流）。这两个面把「平台」和「一堆工具」区分开。其余一切（NiFi、Jupyter、Airflow、AD、全部源、全部消费）保持 ink / muted。

- 组件条目标 `focal: true`。
- 焦点 `kind: bar` 用 `bar_h_focal=56`（更高）+ accent 样式。
- 焦点 `kind: row` 节点保持 `row_h=72` 但上 accent 样式。
- **Trino → 全部消费**的边恒为 `primary`（accent），不看各消费的焦点标记——这是服务流规则。
- `focal: true` 组件少于 / 多于 2 个 → 停下来问用户。

---

## 6. 深色档

| Token | 浅色 | 深色 |
|---|---|---|
| 纸面 / 墨色 | `paper` / `ink` | `ink` / `paper` |
| muted / accent / link | 同名 token | 同名 token（深色列） |
| 侧列填充 | `muted@0.05` | `paper-dark@0.05` |
| 侧列描边 | `soft` | `paper-dark@0.30` |
| 分区填充 | `ink@0.02` | `paper-dark@0.05` |
| 分区描边 | `ink@0.30` | `paper-dark@0.30` |
| 非焦点条填充 | `ink@0.05` | `paper-dark@0.05` |
| 焦点填充 / 描边 | `accent@0.08` / `accent` | `accent-dark@0.12` / `accent-dark` |
| 自定义色 | `C` | `C_light`（提亮 ~15%） |

---

## 7. 复现清单（质量门）

出 SVG 前逐项核：

1. `viewBox = "0 0 1000 {viewBox_h}"`，`viewBox_h = ceil40(图例基线 + 10)`（标准 600）。
2. 平台分区 `x=220 y=8 w=536 h=zone_h`；标签骑顶边框、居中于 `zone_cx=488`、paper 遮罩。
3. 左列 `x=0..160`、右列 `x=800..960`——都 160 宽。
4. 源 / 消费行顶 y=28、步长 88px。
5. `platform.rows` 经 §2.1 游标算法在分区内堆叠；总跨 ≤ `zone_h`。
6. 每个 `kind: row` 内节点 cx 沿分区宽均布（§2.2）。
7. **恰好 2** 个焦点组件（`focal: true`）。
8. 每条从 `kind: bar` 发出的边用 `style: trigger`（虚线、无标签）。
9. 每条 Trino → 消费边用 `style: primary`（服务流规则）。
10. 底条只经 `auth` 样式连到分区下缘。**没有**底条到具体组件的边。
11. 自定义色组件 ≤ 2（焦点对之外）。组件 `color` 绝不改连线色。
12. 所有连线先于任何节点 rect 输出（z 序）。
13. 图例条按 §2.5 规格；可选图标按 §8 挂点。

---

## 8. 图标——词表与挂点

每个图标在 `<defs>` 里定义为 `<g id="ico-…">`：`fill="none" stroke="currentColor" stroke-width="1.2"`，引用走 `<use href="#ico-…" transform="translate(…)" style="color:…">`。常用：`ico-db`（圆柱）、`ico-sftp`（折角文件夹）、`ico-stream`（波形线）、`ico-mail`（信封）、`ico-mainframe`（机柜）、`ico-monitor`（显示器）、`ico-notebook`（笔记本）、`ico-chart`（柱形）、`ico-globe`（地球）、`ico-api`（花括号）、`ico-key`（钥匙）、`ico-log`（折线，日志 / 监控）。要更多就翻 `assets/icons.html` 对应 `<symbol>`。图标是可选项——默认无图标、名字占满。

**挂点（由本类型几何推导，不另行取位）**：

- 侧列（源 / 消费）：图标中心 `(node_x + 24, node_cy)`——左内缘 24px、垂直居中；色 muted；文字仍居中不动。
- 底条：图标中心 `(footer_bar_x + 32, 条中心线)`——落在文字左轨上；色 = 底条自己的语义色；名字 / 副标左缘 `footer_bar_x + 56`（图标右缘净空 12）。
- 平台分区（调度条、焦点节点）**不上图标**——DAG / STORE / SQL 角色芯片已承担身份。

---

## 9. 身份与公共服务 → 连到层，不连到组件

**统一身份**（AD、Keycloak、IAM、OPA、任何横切的身份 / 策略 / 密钥库）认证平台里的**每一个**组件。把它接到某一个工具上是低估了信任范围。正确画法：单箭头连到平台分区的**下缘**，标签 `AUTH`（§3.3）。

同一条规则适用于所有层内服务：集中日志、密钥库、可观测栈、审计汇、mTLS 根。各自进 `footer` 列表、各占一行、各出各的 AUTH 线上行到分区下缘（按 §3.3 错开）。视觉读法是「平台层委托给所有这些」——这才是架构事实。

---

## 10. 预算——本类型有意超默认

这是唯一一个**有意**超出默认 9 节点 / 12 箭头预算的类型。一个真实的平台集成要展示：

- 4–6 个源节点
- 5 个平台组件
- 4–6 个消费节点
- 1–3 个底条节点（身份、可观测、备份……）

合计 **14–20 节点**。复杂度就是论点——这张图主张的是**集成面的数量**。压缩它们等于推翻主张。

失控时的收缩手段：

- 合并明显同质的源行（四个 MySQL → 一个「业务数据库」节点 + 副标 `4 × MySQL`）
- 拆两张（按集成面：数据 vs 身份 vs 可观测）

---

## 11. 反模式

- **≥3 个不同条目却塌缩成一个源 / 消费节点**——推翻本类型的存在意义。想塌缩用架构图或全景图。
- **「源」到「平台」一根总线箭头**——每根线都要标协议；集成团队就是这么读图的。
- **分区内逐工具上色**（青 NiFi、洋红 MinIO、黄 Jupyter）——层级崩塌；只有两个焦点配 accent，横切组件至多再 2 个自定义色（§4 上限）。
- **超过 2 个焦点组件**——焦点用来区分「平台」和「工具堆」；>2 信号清零。
- **焦点组件上的 `color`**——被忽略，accent 恒赢。
- **底条接到某一个工具**（如 AD → 只连 Airflow）——除非该服务真的只保护那一个工具，否则错。默认连层。
- **底条或身份画进分区里**——身份从外面看住这一层。画进去就是歪曲信任模型。
- **顶部画阶段 chevron**——那是数据栈全景图的事。
- **自定义色连线**——连线拓扑驱动。样式选色；组件 `color` 不扩散到边。

---

## 12. 示例

- [`assets/example-dp-integration.html`](../assets/example-dp-integration.html) — 浅色标准版（两条底条：统一身份 + 集中日志）
- [`assets/example-dp-integration-dark.html`](../assets/example-dp-integration-dark.html) — 深色版
- [`assets/example-dp-integration-full.html`](../assets/example-dp-integration-full.html) — full 页面级
