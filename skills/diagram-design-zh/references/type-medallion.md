# 奖章架构（Medallion）

**最适合**：记录多层存储布局，其中每层是**同一数据集的不同质量 / 访问等级**——典型为原始落地层、脱敏层、暂存 / 清洗层、聚合指标层、冷归档层。读者要一眼看清**每层装什么、谁写入、用什么工具与格式、数据如何在层间晋升**时用。

题材是带角色泳道的工作流 → 用**流程**；题材是集群架构而非存储分层 → 用**数据栈全景图**。

本类型是**参数化**的——§1 的输入 schema 经 §2 的公式驱动每个坐标。同一输入两次生成必须产出视觉一致的 SVG。规则形状对齐 type-process.md 与 type-data-flow.md：颜色覆盖、焦点规则、复现清单跨类型读法一致。

---

## 1. 输入——参数契约

```yaml
title:    "五层奖章架构"
subtitle: "季度调研数据：原始 → 脱敏 → 暂存 → 指标 → 归档"

tiers:                                # 3..6 层，从左到右
  - { name: "原始",   bucket: "raw-bucket",       style: "outer",
      fields: { tool: "NiFi · 原始写入",       format: "CSV · Parquet · JSON", writer: "数据工程师",
                example: ["Q1 全量导出 · 含 PII", "CAPI 原始记录"] } }
  - { name: "脱敏",   bucket: "anon-bucket",       style: "default",
      fields: { tool: "Trino INSERT",           format: "Iceberg · 分区",       writer: "数据工程师",
                example: ["去姓名 · 去地址", "稳定家庭 ID"] } }
  - { name: "暂存",   bucket: "staging-bucket",   style: "default",  color: "#c9a23a",   # 语义色族 sem-workspace——分析 / 工作区
      fields: { tool: "Trino · JupyterHub",     format: "Iceberg · 清洗",       writer: "数据科学家",
                example: ["加权记录", "口径对齐"] } }
  - { name: "指标",   bucket: "aggregated-bucket", style: "focal",  focal: true,
      fields: { tool: "Trino INSERT · JDBC",    format: "Iceberg · 指标",       writer: "数据科学家",
                example: ["失业率", "劳动参与率"] } }
  - { name: "归档",   bucket: "archive-bucket",    style: "cold",
      fields: { tool: "MinIO lifecycle",        format: "冷层 · 不可变",        writer: "数据管理员",
                example: ["历史 Q1–Q4 数据集", "保留 5 年以上"] } }

example_label: "季度调研示例"          # 底部字段区标题（随领域变化）

promotions:                           # 相邻层箭头；len = 层数 - 1
  - { from: 0, to: 1, label: "去 PII",   style: "normal"    }
  - { from: 1, to: 2, label: "清洗加权", style: "normal"    }
  - { from: 2, to: 3, label: "汇聚",     style: "focal"     }   # 目标是焦点层 → 自动 accent
  - { from: 3, to: 4, label: "归档",     style: "lifecycle" }   # 虚线

paths:                                # 底部 0..2 张写入方式卡（可选）
  - { tag: "SQL 路径",   title: "Trino INSERT INTO … SELECT",
      sub: "过滤 · 整形 · 关联 · 聚合——集合式变换" }
  - { tag: "笔记本路径", title: "DuckDB + Python/R · JupyterHub",
      sub: "统计 · ML · 交互分析——逐行迭代" }

dark: false
```

**字段语义：**

- `tiers[i].style`——`outer` / `default` / `focal` / `cold` 四选一，驱动卡片色板（§2.3）。
- `tiers[i].focal: true`——全图**恰好一层**可声明。把 `style` 覆写为 `focal`，并把**进入**该层的晋升箭头自动升为 `focal`。
- `tiers[i].fields`——`{tool, format, writer, example}`；`example` 为 1–2 条；区块标题用 `example_label`。
- `tiers[i].color`——可选的逐层 `"#hex"` 覆盖，见 §4。
- `promotions[].style`——`normal | focal | lifecycle`，§3 连接规则把每种样式绑定到固定的描边 / 虚线 / 箭头。
- `paths`——0–2 条。0 条时省掉底行、`viewBox_h` 相应缩小。

---

## 2. 布局公式——确定性几何

```
# 层卡尺寸
tier_w           = 172
tier_h           = 368
tier_gap         = 16
left_pad         = 0                                # 内容四贴：x=0 起排
n_tiers          = len(tiers)

# 画布
viewBox_w        = 1000                             # 画布宽定死；层数增减由右余量消化，宽度与字号不缩放
arc_band_h       = 80                               # 层卡上方留给晋升弧
path_h           = 56
path_gap         = 56                             # 与图例锚同款：层卡底 + 56
bottom_pad       = 16
viewBox_h        = ceil_40(arc_band_h + tier_h + (path_gap + path_h if paths else 0) + bottom_pad)
                                                   # 有路径卡 → 80+368+56+56 = 560 整；无路径卡 → 80+368+16 = 464 → 480

# 层位置
tier_x(i)        = i * (tier_w + tier_gap)          # 0, 188, 376, 564, 752
tier_y           = arc_band_h                       # 80
tier_cx(i)       = tier_x(i) + tier_w/2             # 86, 274, 462, 650, 838

# 晋升弧（相邻层之间——从头顶跨过，锚在层卡顶部中心）
arc_src_x(i)     = tier_cx(i)                       # 层 i 顶部中心
arc_dst_x(i)     = tier_cx(i+1)
arc_peak_x(i)    = (arc_src_x(i) + arc_dst_x(i)) / 2    # 180, 368, 556, 744
arc_label_y      = 50

# 路径卡行（底部）
path_y           = tier_y + tier_h + path_gap       # 448 + 56 = 504
path_w           = 460                              # 常量；两张卡 x = 0 与 476
```

### 2.1 背景

整个 viewBox 铺纸色实底，无纹理。

### 2.2 层卡（172 × 368）

每层是一张圆角卡：淡染色带头、居中的 bucket 名、四行带标签字段、底部隔开的 `example_label` 区。

```
tier_x(i), tier_y       =  卡片左上角（tier_y = 80）
header_band_h           = 40            # 色带 y 从 tier_y 到 tier_y+40
header_band_extra       = 8             # 色带下缘同色再延 8px（补 rx 圆角下的直边）

# 卡内（绝对 y；tier_y = 80）：
title_text            at (tier_cx(i), 106)      # 层名：sans 14px 600 · ink（容器级元素）
bucket_text           at (tier_cx(i), 144)      # bucket：mono 9px · muted（焦点层 accent）

field_x               = tier_x(i) + 16          # 字段区左缩进
字段行（40px 步进，绝对 y）：
  tool 标签     at 180，值 at 198
  format 标签   at 220，值 at 238
  writer 标签   at 260，值 at 278
example 标题 at 360，行 0 at 378，行 1 at 396
```

字段标签 sans 12px · 600 · ink；字段值与 example 行 sans 12px · muted。bucket 与字段值可被 `color` 覆盖重染（§4）。字段值超宽时优先缩短文案；确需两行就拆 `<tspan>` 手工断行——全 SVG 纯文本，字体内嵌与自检管线才看得见每个字。

### 2.3 层样式

四种规范样式，经 `tiers[i].style` 逐层选。未声明时的缺省：第 0 层 → `outer`、末层 → `cold`、焦点层（若有）→ `focal`、其余 → `default`。

| `style` | 卡片填充 | 卡片描边 | 色带填充 | bucket 文本 | example 值文本 |
|---|---|---|---|---|---|
| `outer` | `paper` | `muted @ 0.60` 1px | `muted @ 0.10` | `muted` | `muted` |
| `default` | `paper` | `ink @ 0.40` 1px | `ink @ 0.05` | `muted` | `muted` |
| `focal` | `accent @ 0.08` | `accent` 1.4px | `accent @ 0.15` | `accent` | `accent` |
| `cold` | `ink @ 0.02` | `muted @ 0.60` 虚线 `4,3` | `muted @ 0.18` | `muted` | `muted` |

所有卡片 rect `rx = 6`。

**焦点样式注**：焦点层的 accent 处理是级联的——bucket 文本与 example 值行用 accent；其余字段值（tool/format/writer）保持 muted。只有 bucket 名与 example 载荷承载焦点信号，整卡不至于泡在焦点色里。

### 2.4 晋升弧（跨层卡头顶）

每条晋升是一支**三次贝塞尔弧**，锚在相邻两层的**顶部中心**——`(tier_cx(i), tier_y)` 到 `(tier_cx(i+1), tier_y)`，拱进层卡上方 80px 的 `arc_band`，峰约 y≈20。连线与标签全程可见——不垫遮罩、不压卡内容。

```svg
<path d="M {tier_cx(i)},{tier_y} C {tier_cx(i)},0 {tier_cx(i+1)},0 {tier_cx(i+1)},{tier_y}"
      fill="none" stroke="…" stroke-width="…" marker-end="…"/>
```

标准五层（`tier_y = 80`，层心 x = 86, 274, 462, 650, 838）：

- 0→1：`M 86,80 C 86,0 274,0 274,80`（首弧从层 0 顶中心起——无来箭）
- 1→2：`M 274,72 C 274,0 462,0 462,80`
- 2→3：`M 462,72 C 462,0 650,0 650,80`（焦点——accent）
- 3→4：`M 650,72 C 650,0 838,0 838,80`（归档——虚线）

**出发锚规则**：到站箭头仍锚在层顶中心（`tier_cx(i), tier_y`）；**出发锚从箭头顶起笔**——箭头 marker 长 9.6（8 单位 × 1.2 线宽）、尖超出终点 1.2，箭头尾在终点上方 ≈8.4 → 出发点 `y = tier_y − 8`（72）。线从箭头之上离开，与来箭在同一层顶交接而不穿箭头身体；首弧无来箭，仍从 `tier_y` 起。

三次曲线几何：锚点 y=80（层顶）、控制点 y=0（viewBox 顶）。t=0.5 处峰值为 `0.125·80 + 0.375·0 + 0.375·0 + 0.125·80 = 20`。每弧跨整整一个层距（标准布局 188px），连线的竖向起伏清晰可见。

**箭头朝向**：`marker-end` 配 `orient="auto"` 沿路径终点切线旋转。控制点在锚点正上方，落地切线笔直**向下**——箭头干净地扎进层 i+1 的顶部中心、指向色带。

**链式锚点**：相邻弧共享接点（弧 0→1 的终点 = 弧 1→2 的起点）。每层顶部中心是一个「关节」——数据从卡顶进来、卡内变换、再从卡顶出去。箭头下扎 + 下一弧直起的组合读作一次完整的载荷交接。

| `style` | 描边 | 宽度 | 虚线 | 箭头 |
|---|---|---|---|---|
| `normal` | `muted` | 1.2 | — | `arrow` |
| `focal` | `accent` | 1.4 | — | `arrow-accent` |
| `lifecycle` | `muted` | 1.2 | `4,3` | `arrow` |

**自动样式规则**：

- `promotions[k].to` 指向**焦点层** → 样式自动升 `focal`（accent、宽 1.4、`arrow-accent`）。
- `promotions[k].to` 指向带 **`color` 覆盖**的层（§4）→ 箭头继承该 hex——描边 = `C`、标签 = `C`、`marker-end` 用配色箭头（如 `arrow-yellow` 配 `sem-workspace`）。宽度保持 1.2——颜色覆盖是「关切」信号不是焦点晋升；lifecycle 虚线保留但换色。
- 两者同时成立时焦点赢（带色的焦点层仍用 accent）。

**弧内标签**：锚在 `(arc_peak_x(k), 50)`。中文箭头标签规格（sans 12px · 500 · 0.12em），颜色随弧描边。**无需遮罩**——曲线峰在 y≈20、标签在 y=50，落在弧围出的开放空间里，弧本身即视觉框架。

### 2.5 路径卡行（底部，可选）

至多 **2** 张写入方式卡。标准五层：`path_y = 504`（层卡底 448 + 56）、`path_h = 56`、两张卡各 460 宽（x=0 与 476）。

每卡内容：

- 容器 rect：白底、`ink @ 0.20` 描边 1px、`rx=6`。
- 角标芯片：`(path_x+8, path_y+6)`，高 18 `rx=2`，透明底 + `ink @ 0.30` 描边 0.8px；芯片文字中文角标规格（sans 12px · 500 · 0.3em）或纯拉丁 mono 9px · 0.18em，ink。
- 标题 `(path_x+96, path_y+22)`：sans 12px · 600 · ink。
- 副标 `(path_x+96, path_y+40)`：sans 12px · muted。

---

## 3. 连接规则（强制）

三种样式，绑定拓扑。与 type-process.md §3 逐字对齐。

```svg
<defs>
  <marker id="arrow"        markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#565e7e"/></marker>
  <marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#1a4dd9"/></marker>
  <!-- 每个在用的自定义层色声明一支箭头，命名 arrow-{语义} -->
  <marker id="arrow-yellow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#c9a23a"/></marker>
</defs>
```

**z 序**：晋升弧先于任何层卡 rect 绘制——卡片盖在上面，弧的过冲被卡内掩蔽。

**弧形规则**：奖章晋升永远是**跨顶三次弧**，锚在源 / 目标层的顶部中心、控制点在 y=0 正上方。**没有**穿层间隙的水平线——跨顶弧才让连线与标签同时清楚可见。

---

## 4. 组件颜色覆盖

任何层或路径条目可带可选 `color: "#hex"`。对齐 type-process.md §4 / type-data-flow.md §4。

### 4.1 逐层 `color`

| 元素 | 浅色 | 深色 |
|---|---|---|
| 卡片填充 | `C@0.08` | `C_light@0.10` |
| 卡片描边 | `C`（宽 1.2） | `C_light`（宽 1.2） |
| 色带填充 | `C@0.15` | `C_light@0.18` |
| 层名文本 | ink（不变——层名永远可读） | ink（不变） |
| bucket 文本 | `C` | `C_light` |
| example 值 | `C` | `C_light` |
| 字段标签 / 字段值 | **不变**（ink / muted） | **不变** |
| 触达该层的连接线 | **不变**——拓扑驱动 | **不变** |

`C_light` = 同一 hex 提亮约 15% 保深色对比。

### 4.2 逐路径 `color`

路径卡描边换 `C@0.45`、角标芯片描边换 `C@0.55`；角标文字与标题用 `C`。副标保持 muted。

### 4.3 规则

- **焦点层上禁用。** accent 已经承载那个信号——焦点层上的 `color` 被忽略。
- **cold 层不与虚线叠加。** 虚线冷层或自定义色二选一。
- 每图自定义色元素（层或路径）**≤ 2**，焦点层之外。
- **晋升箭头继承目标层颜色**（§3 自动样式）。Staging 层给 `color` 覆盖 `sem-workspace`（金），落进 Staging 的「清洗加权」弧也渲染成黄——连线、标签、箭头一致，带色层与其入流读作同一个「关切」组。箭头**不**继承源层颜色——只看目标；离开带色层的弧回到 muted（或下一目标层的颜色 / 样式）。

### 4.4 语义色板（推荐）

与其他参数化类型同一套（style-guide「语义色族」，跨图同色同义、不吃换肤）：

- `sem-security` 铁锈红——安全 / 身份 / 审计（含 PII 层、审计层）
- `sem-observability` 岩蓝——可观测 / 质量（校验层、监控区）
- `sem-governance` 橄榄绿——治理 / 血缘 / 发布（面向消费的聚合层、公开层）
- `sem-workspace` 金——分析 / 工作区（暂存层、科学家沙盒、中间计算面）
- `sem-backup` 暖棕——备份 / 灾备 / 归档（冷层的替代配色）

---

## 5. 焦点规则

每图**恰好一个**焦点层。缺省取标了 `focal: true` 的层；没标则取分析枢纽层（通常是「指标」或下游消费者查询的那层）。

焦点层：

- 用 `style: focal`（accent 填充 + 描边 1.4 + accent 色带）。
- bucket 文本与 example 值行渲染为 accent。
- **进入**它的晋升箭头自动升为 `focal`（accent）。
- **离开**它的箭头（若有——通常是进冷归档）保持用户声明的样式（通常 `lifecycle` 虚线）。

`focal: true` 的层数为 0 或 >1 → 停下来问用户。

---

## 6. 深色档

照抄 [`assets/example-medallion-dark.html`](../assets/example-medallion-dark.html)：对称换基、α 不动——

| 元素 | 浅色 | 深色 |
|---|---|---|
| 纸面 / 卡片底 / 路径卡底 | `paper` | `#0a0d1b`（卡与纸面同色，描边成型） |
| 层名 / 字段标签 / 路径标题 | `ink` | `ink` 深色档 |
| bucket / 字段值 / example 值 / 弧标签 / 副标 | `muted` | `muted` 深色档 |
| outer / cold 描边与色带 | `muted @ 0.60 / 0.10 / 0.18` | `muted` 深基同 α |
| default 描边与色带 | `ink @ 0.40 / 0.05` | `ink` 深基同 α |
| cold 垫底 | `ink @ 0.02` | `ink` 深基 @ 0.02 |
| 焦点层 | `accent @0.08` + `accent` 1.4 | `accent` 深基 @0.10（提档）+ `accent` 深色档 1.4；焦点色带 @0.15 换基 |
| **staging 语义金** | `#c9a23a`（卡底 @0.08、色带 @0.15、描边实色 1.2） | **两档恒定不变**——语义色不吃换肤（§4.4） |
| 晋升弧 | 常态 `muted` 1.2 / 焦点 `accent` 1.4 / lifecycle `4,3` 虚线 | 换基；宽度与虚线不动 |
| 路径卡描边 / 芯片描边 | `ink @ 0.20 / 0.30` | `ink` 深基同 α |

---

## 7. 复现清单（质量门）

出 SVG 前逐项核：

1. `viewBox = "0 0 {viewBox_w} {viewBox_h}"` 经 §2 推导（5 层 + 2 路径卡 → 1000 × 560；宽 1000 定死）。
2. 每张层卡在 `(tier_x(i), 80)`、172 × 368、`rx=6`。
3. 层色带填 `(tier_x(i), 80, 172, 40)` 加下方 10px 延伸。
4. **恰好一个**焦点层；进入它的弧自动 `focal`。
5. 晋升弧是跨顶三次贝塞尔；到站锚 `(tier_cx(i+1), 80)`、出发锚按 §2.4 从箭头顶（y=72）起笔；标签在弧内 `(arc_peak_x, 50)`、无遮罩。
6. 底部路径行只在 `len(paths) > 0` 时出现；卡在层卡底 + 56（504）、高 56。
7. 自定义色 ≤ 2（焦点层之外）；箭头上不用。
8. 所有晋升箭头先于任何层 rect 输出（z 序——卡片掩蔽线端）。
9. 焦点层的 bucket 文本与 example 值用 accent，其余 muted。
10. 层卡与路径卡 `rx=6`；角标芯片 `rx=2`。

---

## 8. 反模式

- **多于一个焦点层**——焦点标记的是核心分析面；>1 个信号清零。
- **冷样式上非归档层**——虚线雾面观感专留给留存 / 归档层。
- **双向晋升箭头**——晋升恒从左到右。回流（如聚合写回原始）对这个类型是错的；换图。
- **自定义色箭头**——连接线由拓扑驱动；层上的色绝不扩散到边。
- **路径卡解释层语义**——路径描述**写入方式**（数据怎么在层间移动），不是每层装什么。路径卡里写「原始层存储 …」时，内容属于原始层的字段。
- **缺 `example_label` 内容**——每层都该有具体示例载荷（季度调研行、客户记录、工单……）。没有它图就抽象化、挣不到自己的版面。
- **晋升标签超出弧内空间**——中文箭头标签 ≤ 6 字。长动词（「计算并汇总」）破坏节奏；缩成「汇聚」或拆两张图。

---

## 9. 示例

- [`assets/example-medallion.html`](../assets/example-medallion.html) — 浅色标准版（季度调研：5 层 + 2 路径卡，焦点 = 指标层）
- [`assets/example-medallion-dark.html`](../assets/example-medallion-dark.html) — 深色档（§6 换基；staging 语义金恒定）
- [`assets/example-medallion-full.html`](../assets/example-medallion-full.html) — full 页面级（副题 + 三卡 + 页脚）

---

## 10. 走例 YAML

§1 的 YAML 就是 shipped `example-medallion.html` 的**完整**输入定义——该文件 SVG 里的每个坐标都能由 §2 作用于这些输入推出。同一 YAML 也作为文件顶部的 HTML 注释内嵌在 `example-medallion.html` 里，源码视图打开 SVG 前先看到参数化输入。
