# IT 现状图（IT current-state）

**最适合**：记录现代化方案的**之前**画面——按阶段或部门分组的存量 IT 版图（采集 → 处理 → 分发，或前端 / 后端 / 存储），标注痛点、文件式交接（CSV / Excel / 邮件 / 拷贝）、平台化之前的工具。它是 type-dp-integration.md 的搭档：现状图展示数据平台方案要填的沟。

干系人要看到现行体系的摩擦——脚本孤岛、手工倒文件、没有版本控制、单点故障——以及从这些到目标平台拓扑的路径时用。

本类型是**参数化**的——§1 输入 schema 经 §2 公式驱动每个坐标。规则形状对齐 type-dp-integration.md（分区 + 横切底条）、type-process.md（正交圆角连线）、type-medallion.md（逐元素 `color` 覆盖）：焦点规则、颜色覆盖、深色档、复现清单跨类型读法一致。

---

## 1. 输入——参数契约

```yaml
title:    "现行 IT 版图"
subtitle: "数据平台建成之前的管道"
eyebrow:  "IT 版图 · 现状图"

orientation: horizontal      # horizontal（默认，分区从左到右）| vertical（分区从上到下）

zones:                       # 2..4 个分区，沿主轴排序
  - name: "采集"
    components:              # 每分区 1..5 个组件
      - id: pos
        name: "门店 POS"
        sub:  "零售流水 · MySQL"
        icon: postgres               # primitive-icons.md 里的任意 id（可选）
        kind: standard               # standard | focal | external（external → 虚线描边）
      - { id: dealer-portal, name: "经销商门户", sub: "B2B · 订单录入", icon: server }
      - { id: supplier-xlsx, name: "供应商报表", sub: "外部 · 手工报送", icon: database, kind: external }
  - name: "处理"
    components:
      - { id: shared-drive, name: "共享盘",     sub: "无版本控制 · Windows 文件共享", icon: file, kind: focal }
      - { id: analyst-pc,   name: "分析师工作站", sub: "SPSS · Excel · Python",        icon: desktop }
      - { id: sqlserver,    name: "SQL Server", sub: "本地部署 · 核心 RDBMS",          icon: sqlserver, color: "#7a8c47" }  # sem-governance（幸存系统，跨深浅恒定）
  - name: "分发"
    components:
      - { id: legacy-bi, name: "老报表门户",   sub: "手工瓶颈",       icon: cloud,    kind: focal }
      - { id: website,   name: "公司官网",     sub: "对外 · 静态页",   icon: internet }
      - { id: group-hq,  name: "集团兄弟单位", sub: "约 6 家",         icon: users,    kind: external }

connectors:                   # 有序列表；每条连接两个组件 id
  - { from: pos,           to: shared-drive, label: "表格",  icon: csv,  style: link }
  - { from: dealer-portal, to: shared-drive, label: "邮件",  icon: file, style: link }
  - { from: supplier-xlsx, to: shared-drive, label: "报表",  icon: excel, style: link, dashed: true }
  - { from: shared-drive,  to: analyst-pc,   label: "拷贝",              style: accent, dashed: true }
  - { from: analyst-pc,    to: sqlserver,    label: "入库",              style: neutral }
  - { from: analyst-pc,    to: legacy-bi,    label: "报表",  icon: excel, style: accent }
  - { from: legacy-bi,     to: website,      label: "网页",              style: neutral }
  - { from: website,       to: group-hq,     label: "下载",    icon: csv, style: link, dashed: true }

footer:                       # 0..3 条可选的全宽横条（横切关切）
  - { name: "身份管理", sub: "Active Directory · LDAP · SSO", icon: active-directory }
  - { name: "可观测",   sub: "日志 · 指标 · 告警",             icon: monitoring }

legend:                       # 按实际用到的样式自动生成；标签可改
  - { swatch: link,   label: "数据流" }
  - { swatch: accent, label: "痛点" }
  - { swatch: dashed, label: "外部" }
  - { swatch: focal,  label: "瓶颈" }

dark: false
```

**字段语义：**

- `orientation`——`horizontal`（分区分左→右排，组件在分区内竖排）或 `vertical`（分区分上→下排，组件横排）。
- `zones[i].name`——短标签（中文 ≤ 6 字）。渲染在分区框左上角的边框断口上，paper 色遮罩垫底，分区标签规格（sans 10px · 500 · 0.3em · muted）。
- `components[i][k].id`——全局唯一 slug，供 `connectors[].from/to` 引用。
- `components[i][k].name`——`node-name` 角色（sans 14px 600）。
- `components[i][k].sub`——中文子标 sans 12px · muted（组件高升到 72 时可两行）。
- `components[i][k].icon`——primitive-icons.md 里的任意 id，可选；缺省则无图标、名字左移。目录缺 `mail` 图标时邮件交接用 `icon: file` 兜底。
- `components[i][k].kind`——`standard | focal | external`。`focal` 触发 accent 色板（§5）；`external` 换 4,3 虚线描边 + muted 墨，标记「不在我们范围内」。
- `components[i][k].color`——可选逐组件颜色覆盖（§4）。`kind: focal` 上被忽略（accent 赢）。
- `connectors[k].label`——短文本（中文 ≤ 4 字），**一律中文**（协议 / 格式名也译：CSV→表格、EXCEL→报表、下载类→下载）。规格 sans 10px · 500 · 0.12em · muted（accent 边随线色），白底遮罩骑线居中。
- `connectors[k].icon`——可选，标签文字左侧的内联图标，同组件图标目录。
- `connectors[k].style`——`neutral | link | accent`，驱动描边色 + 箭头。
- `connectors[k].dashed`——`true | false`。
- `footer[k]`——可选横切条。全宽（去边距）。横条不发连线。
- `legend[k].swatch`——`link | accent | dashed | focal | neutral`，按图内实际使用的自动策展。

---

## 2. 布局公式——确定性几何

```
# 水平朝向（默认）
left_pad        = 0
right_pad       = 16
zone_gap        = 48
zone_y          = 8
zone_h          = 360
n_zones         = len(zones)

# 分区宽：按组件名与两行副标的实际宽度定（标准示例 3/3/3 组件 = 256 / 360 / 272），
# 精确宽度由 §10 走例给定；右缘合计 984、留 16。画布宽 1000 定死，
# 标题对齐见 style-guide「容器对齐与画布基线」。
zone_w(i)       = 走例给定（256 / 360 / 272）
viewBox_w       = 1000

# 分区内组件摆放——行顶跨区对齐（三列同一行同 y），行间净空恒 56
comp_pad_x      = 20
comp_h          = 56                     # focal 68（两行副标）
row_gap         = 56
row_top(0)      = zone_y + 28            # 36；首行让出分区名断口
row_top(k+1)    = row_top(k) + max_comp_h(k) + row_gap   # 示例 36 / 160 / 272

# 组件中线（连线路由用）
comp_x(i)       = zone_x(i) + comp_pad_x          # 20 / 324 / 732
comp_w(i)       = zone_w(i) - 2 * comp_pad_x      # 216 / 320 / 232
comp_cx(i)      = comp_x(i) + comp_w(i)/2
comp_cy(i, k)   = comp_y(i, k) + comp_h/2

# 底条（若有）
footer_bar_h    = 56
footer_gap      = 8
footer_top      = zone_y + zone_h + 24
footer_y(k)     = footer_top + k * (footer_bar_h + footer_gap)

# 画布总高
content_bottom  = N_footer > 0 ? footer_bottom : zone_y + zone_h   # 368
legend_line_y   = content_bottom + 56    # 424；线贯通 0→1000
legend_baseline = legend_line_y + 18     # 442
viewBox_h       = ceil40(legend_baseline + 10)   # 480
```

### 2.1 背景与分区框

整个 viewBox 铺纸色实底，无纹理。每个分区框：

```svg
<rect x="{zone_x}" y="{zone_y}" width="{zone_w}" height="{zone_h}"
      fill="rgba(41,49,79,0.02)" stroke="rgba(41,49,79,0.10)" stroke-width="0.8" rx="8"/>
<!-- 分区名遮罩断口 -->
<rect x="{zone_x+20}" y="{zone_y-8}" width="{label_w}" height="16" fill="#ffffff"/>
<text x="{zone_x+24}" y="{zone_y+4}" fill="rgba(41,49,79,0.60)"
      font-size="12" font-weight="500" letter-spacing="0.3em">分区名</text>
```

### 2.2 组件盒

三种视觉 kind：

| `kind` | 填充 | 描边 | 描边宽 | 虚线 | 名 ink | 副 ink |
|---|---|---|---|---|---|---|
| `standard` | `paper` | `ink @ 0.40` | 1 | — | `ink` | `muted` |
| `focal` | `accent @ 0.08` | `accent` | 1.4 | — | `ink` | `accent`（行 1）+ `muted`（行 2） |
| `external` | `paper` | `muted` | 1 | `4,3` | `ink` | `muted` |

**图标摆放**（24×24，currentColor 单色——可选，点名才上；见 primitive-icons.md）：图标占 24×24 → 含 12px 左垫共 36px 横向足迹，名字与副标基线右移 40px。无图标时名字左移、盒宽不变。

**名 + 副标基线**（左对齐；shipped 示例无图标，名字贴 comp_x+16）：

```
name_x = comp_x + (icon ? 44 : 16)
name_y = comp_y + comp_h/2 - 2
sub_y  = comp_y + comp_h/2 + 14    # focal 68 时副标 y = comp_y + 50
```

### 2.3 连线几何（路由规则在 §3）

```
src_right / src_left / src_top / src_bot / src_cy   # 源组件四边与中线
dst_left / dst_right / dst_top / dst_bot / dst_cx / dst_cy
corridor_x = dst_cx                                  # 跨分区路由的走廊 x：落在目标水平中心，从上/下边进入
```

### 2.4 底条

```svg
<rect x="0" y="{footer_y}" width="984" height="56"
      fill="rgba(41,49,79,0.03)" stroke="rgba(41,49,79,0.18)" stroke-width="0.8" rx="8"/>
<text x="56" y="{footer_y+24}" font-size="14" font-weight="600" fill="#29314f">{name}</text>
<text x="56" y="{footer_y+40}" font-size="12" fill="#565e7e">{sub}</text>
```

底条是层内全体共享的服务。**不发任何连线。** 视觉上垫在分区下方，读者一眼扫到横切关切。

### 2.5 图例条

`y = content_bottom + 56` 发丝分隔线（贯通 0→1000），`y = content_bottom + 74` 一行样本 + 标签（与「图例」同基线）。只出现 `connectors[]` 实际用到的样式（外加 focal / external 组件 kind 若在图中出现）。

---

## 3. 连线规则（强制）

### 3.1 路径形状——正交圆角 Q 贝塞尔，r = 8

逐字复用 type-process.md §3.1。**永远没有斜线。**

```svg
<!-- 同分区相邻组件（同竖列）：单根竖线 -->
<line x1="{src_cx}" y1="{src_bot}" x2="{dst_cx}" y2="{dst_top}" stroke="…" marker-end="…"/>

<!-- 跨分区或跨行：右出 → H → Q 弯 → V → 从上（或下）边进 -->
<path d="M {src_right},{src_cy} H {dst_cx-8} Q {dst_cx},{src_cy} {dst_cx},{src_cy±8} V {dst_top_or_bottom}"
      fill="none" stroke="…" marker-end="…"/>
```

- 目标在源**下方** → `{src_cy+8}`、`V {dst_top}`。
- 目标在源**上方** → `{src_cy−8}`、`V {dst_bottom}`。

### 3.2 出 / 入边（可配置；缺省如下）

| 拓扑 | 源缺省出边 | 目标缺省入边 |
|---|---|---|
| 同分区、目标在下 | 下 | 上 |
| 同分区、目标在上 | 上 | 下 |
| 跨分区、水平流向 | 右 | 上（或下——离 src_cy 近者） |
| 竖排朝向的图 | 下 | 上 |

连线可经 `connectors[k].from_side` / `to_side`（`top | right | bottom | left`）覆写。**回向引用**（水平朝向里右→左）只允许在至少一端是 `kind: external` 时出现，且必须 `dashed: true`。

### 3.3 箭头必须贴到目标矩形

路径最后一条命令终止在目标矩形边线（`V {dst_top}` 或 `H {dst_left}`），**不是**质心。`refX=7` 下三角紧贴边框。线停在边线之前、或扎进质心把箭头埋进盒内——都是硬伤。

### 3.4 样式 → 描边 + 箭头

| `style` | 描边色 | 宽 | 箭头 |
|---|---|---|---|
| `neutral` | `muted` | 1.0 | `url(#arrow)` |
| `link` | `link` | 1.2 | `url(#arrow-link)` |
| `accent` | `accent` | 1.4 | `url(#arrow-accent)` |

`dashed: true` 时加 `stroke-dasharray="4 3"`。

```svg
<defs>
  <marker id="arrow"        markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#565e7e"/></marker>
  <marker id="arrow-link"   markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#1a4dd9"/></marker>
  <marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#1a4dd9"/></marker>
</defs>
```

### 3.5 连线标签 = 内联图标 + 文字，放连线**起点**、垂直于线偏移

标签贴**源端**（不在中段），并沿**垂直于线**的方向偏移，绝不压线。图标（若设）在标签 paper 色遮罩内、文字左侧。

```svg
<g transform="translate({label_cx}, {label_cy})">
  <rect x="-{w/2}" y="-9" width="{w}" height="18" rx="3" fill="#ffffff" stroke="none"/>
  <text x="0" y="4" text-anchor="middle" font-size="12" font-weight="500"
        letter-spacing="0.12em" fill="{stroke_color}">{label}</text>
</g>
```

**摆放公式**（标签盒 18px 高 × `w` 宽，中心 `{label_cx, label_cy}`）：

| 源出段 | `label_cx` | `label_cy` | 效果 |
|---|---|---|---|
| 水平（右出） | `src_right + 6 + w/2` | `src_cy − 14` | 过源 6px、线上方留净空 |
| 水平（左出、回向） | `src_left − 6 − w/2` | `src_cy − 14` | 源前 6px、线上方留净空 |
| 竖直（下出） | `src_cx + 6 + w/2` | `src_bot + 14` | 线右侧 6px、源下缘下 5px |
| 竖直（上出、回向） | `src_cx + 6 + w/2` | `src_top − 14` | 线右侧 6px、源上缘上 5px |

跨分区 H+Q+V 路由的标签绑在**水平段**（该段锚在源上）。标签放水平段靠前位置——不放 Q 弯、不放竖直尾段。

- `w = 文字宽 + 12`（有图标再 +30）——自适应。
- 遮罩 `fill` 浅色档取 `paper`、深色档取墨色。遮罩保留作安全垫——标签虽不压线，仍可能蹭到分区底与组件填充。
- `stroke_color` 跟 §3.4（文字与图标继承连线的 accent / link / neutral 色）。

### 3.6 z 序

所有连线（path + line + 标签底）先于任何组件 rect 输出，节点填充掩蔽线端。连线**标签**是唯一例外——它后于自己的线绘制，遮罩盖在线上。

---

## 4. 组件颜色覆盖（逐组件 `color: "#hex"`）

| 元素 | 浅色 | 深色 |
|---|---|---|
| 容器填充 | `C@0.06` | `C_light@0.10` |
| 容器描边 | `C@0.45`（宽 1） | `C_light@0.55` |
| 组件名文本 | `C` | `C_light` |
| 副标 | muted（不变） | muted（不变） |
| 触达该组件的连线 | **不变**——拓扑驱动 | **不变** |

`C_light` = 同 hex 提亮 ~15%（如 `sem-governance`、`sem-security` 基各提亮 ~15%）。

**规则：**

- **焦点组件上禁用。** `kind: focal` 恒渲染 accent；`color` 静默忽略。
- **连接线上禁用。** 连线样式由拓扑驱动；想要彩边就去挑 `style: accent / link / neutral`，不是给组件上色。
- 上限：每图自定义色组件 **≤ 3**（焦点组件之外）。超过 3 视觉信号就碎。

**推荐跨类型色板**（同 type-medallion / process / dp-integration / dp-security-matrix）：`sem-security` 铁锈红（安全 / 治理 / 非头条痛点）、`sem-observability` 岩蓝（可观测 / 质量 / 监控闸）、`sem-governance` 橄榄绿（幸存系统——新平台会保留的那个工具）、`sem-workspace` 暖黄（沙盒 / 开发）、`sem-backup` 暖棕（归档 / 冷存 / 灾备）。

---

## 5. 焦点规则

- `kind: focal` 组件：每图 **≤ 2**（没有单一主导痛点时 0 个也合法）。
- 自动样式：accent 描边 1.4、accent-tint 填充 8%、ink 粗体 `node-name`、副标行 1 accent。
- 任一端是焦点的连线**默认**渲染 `style: accent`；输入为这条边显式声明了更轻的 `style`（如 `link`）时尊重声明——痛点叙事需要层次时用轻样式，别让全图泡在焦点色里。
- 焦点组件上的自定义 `color: "#hex"` 静默忽略——accent 恒赢。

图需要超过 2 个焦点组件 = 两条叙事被压进一张图。拆：一张「采集痛点」+ 一张「分发痛点」。

---

## 6. 深色档

| 角色 | 浅色 | 深色 |
|---|---|---|
| paper / ink / muted / accent | token 值 | 深色列反转值（对称换基） |
| 一切 `ink@X`（分区底 0.02 / 分区框 0.10 / 组件描边 0.40 / 图例线） | `ink @ X` | 深色基 `@X`（**α 不动**） |
| focal 填充 / 描边 | `accent @ 0.08` / `accent` | 深色基 `@0.10`（提档）/ 深色 accent |
| external 描边 | `muted`（虚线） | `muted` 深色档（虚线） |
| 标签遮罩 / 白底节点填充 | `paper` | `#0a0d1b` 纸面同色（描边成型） |
| 语义色组件（如 SQL Server 幸存系统） | `sem-*` 浅档 | 语义色深浅两档恒定（sem-governance `#7a8c47` 两档同值） |

---

## 7. 复现清单（质量门）

出 SVG 前逐项核：

1. eyebrow / 标题跟容器线（frame 统一缩进，不写 margin-left）；标题 → 图表 3rem。
2. 2..4 个分区；每个分区的短标签在分区框左上、边框断口上、paper 遮罩垫底。
3. 每个组件有 `id`、`name`；`sub` / `icon` / `kind` / `color` 可选。
4. `kind: focal` 组件 ≤ 2；焦点样式自动上（accent 填充 8%、描边 1.4、副标行 1 accent）。
5. 每条连线从源的右（或下）边出、从目标的左（或上）边进；每个弯正交圆角 Q 贝塞尔 r=8；箭头三角可见地贴在目标矩形边线上。
6. 连线标签一律中文，白底遮罩**骑线居中**（长竖线放中段，短水平线放起点侧）；规格见 §字段语义 `connectors[k].label`；图标（若设）在遮罩内文字左侧。
7. 自定义色组件 ≤ 3；焦点上没有。
8. 底条 ≤ 3；每条跨 `viewBox_w − 2×left_pad`；任何底条不发连线。
9. 底部图例按 bar 规格：「图例」mono 10px · 0.1em 与项同基线（基线 = 分隔线 +18）、块 16×12、线样长 28；分隔线距最下内容元素 56、贯通 0→1000。
10. 连线标签与分区名按 §字段语义规格；组件名 `node-name`（sans 14px · 600）；技术副标按语言走中文 12px / mono 9px。
11. 箭头 `#arrow` / `#arrow-link` / `#arrow-accent` 在 `<defs>` 定义一次；无内联箭头定义。
12. 深色变体：每个语义 token 走深色档取值；自定义色提亮 ~15%。

---

## 8. 反模式

- **斜箭头。** 永远正交圆角 Q 贝塞尔。
- **箭头不贴目标。** 路径终点停在质心或边线之前。
- **无遮罩的内联连线标签。** 线从文字里渗过去，没法读。
- **标签压在线上、放中段。** 标签属于连线起点、带垂直净空（§3.5）——埋在中段既藏住方向又逼读者的眼睛跟遮罩打架。
- **拿小字徽章当图标。** 组件图标用 24px 目录图标（可选）；文字徽章只当标签文字用。
- **焦点组件上自定义色。** 焦点恒赢；`kind: focal` 上的 `color` 静默忽略。
- **底条接某一个组件。** 底条 = 层内横切关切；从底条到具体工具的连线是范畴错误（只有当底条服务真的认证**所有**组件时才用 dp-integration 的 AUTH 线画法，且线落在分区底边上，不落到具体工具）。
- **组件总数 > 16 或单分区 > 5。** 密度上限；拆两张。
- **一张图里混朝向。** 选一种——`horizontal` 或 `vertical`——贯彻到每个分区。
- **拿 `kind: focal` 标记所有疼的东西。** 焦点留给 ≤ 2 个头条痛点；「不好但不是头条」给 `color` 覆盖 `sem-security` 铁锈红。

---

## 9. 示例

- [`assets/example-it-state.html`](../assets/example-it-state.html) — 浅色标准版（3 分区、9 组件、8 连线、SQL Server 橄榄绿）

---

## 10. 走例 YAML——`example-it-state.html` 的完整输入

```yaml
title:    "现行 IT 版图"
subtitle: "数据平台建成之前的管道"
eyebrow:  "IT 版图 · 现状图"

orientation: horizontal

zones:
  - name: "采集"
    components:
      - { id: pos,           name: "门店 POS",     sub: "零售流水 · MySQL" }
      - { id: dealer-portal, name: "经销商门户",   sub: "B2B · 订单录入" }
      - { id: supplier-xlsx, name: "供应商报表",   sub: "外部 · 手工报送", kind: external }
  - name: "处理"
    components:
      - { id: shared-drive, name: "共享盘",       sub: "无版本控制 · Windows 文件共享", kind: focal }
      - { id: analyst-pc,   name: "分析师工作站", sub: "SPSS · Excel · Python" }
      - { id: sqlserver,    name: "SQL Server",   sub: "本地部署 · 核心 RDBMS", color: "#7a8c47" }
  - name: "分发"
    components:
      - { id: legacy-bi, name: "老报表门户",   sub: "手工瓶颈", kind: focal }
      - { id: website,   name: "公司官网",     sub: "对外 · 静态页" }
      - { id: group-hq,  name: "集团兄弟单位", sub: "约 6 家", kind: external }

connectors:
  - { from: pos,           to: shared-drive, label: "表格",   style: link }
  - { from: dealer-portal, to: shared-drive, label: "邮件",   style: link }
  - { from: supplier-xlsx, to: shared-drive, label: "报表",   style: link, dashed: true }
  - { from: shared-drive,  to: analyst-pc,   label: "拷贝",   style: accent, dashed: true }
  - { from: analyst-pc,    to: sqlserver,    label: "入库",   style: neutral }
  - { from: analyst-pc,    to: legacy-bi,    label: "报表",   style: accent }
  - { from: legacy-bi,     to: website,      label: "网页",   style: neutral }
  - { from: website,       to: group-hq,     label: "下载",   style: link, dashed: true }

dark: false
```

> 走例与 shipped 资产一致：组件**不带图标**（`icon` 字段是可选契约，点名才上；上了图标名字右移 §2.2）、连线标签全中文（CSV→表格、EXCEL→报表）。

### 10.1 这份 YAML 证明了什么

- `n_zones = 3`，每分区组件 `[3, 3, 3]`，自定义色 1 个（SQL Server），焦点 2 个（共享盘、老报表门户），external 2 个（供应商报表、集团兄弟单位）。
- 分区宽 256 / 360 / 272 ⇒ `viewBox_w = 0 + 256 + 48 + 360 + 48 + 272 + 16 = 1000`；`viewBox_h`：分区底 368 → 图例线 424、基线 442 → `ceil40(452) = 480`（无底条）。
- 共享盘（焦点）分区 2 行 0：`x=324, y=36, w=320, h=68`（焦点撑高装两行副标）。
- **三根采集侧 → 共享盘连线（C1/C2/C3）都进共享盘的左缘（x=324）。** 走上缘的话，箭头体（`refX=7` 下沿行进方向回退 7px）会落进目标盒内、被纸色填充掩蔽——只剩 1px 尖探出描边。左缘进入 + 向右路径让箭头体留在盒外、完整可见。三个左缘附着点扇开在 **y = 64 / 80 / 96**（16px 间距，远超 12px 最小值）。
- **C1**（门店 POS → 共享盘）源 y 与落点同高：单根水平线 (236,64)→(324,64)。
- **C2**（经销商门户 → 共享盘）从分区 2 背景上方绕行——竖直段 x=256（分区间隙 256..304 内）——落 `(324, 80)`。
- **C3**（供应商报表 → 共享盘）同样绕行——竖直段 x=288（避开 x=324 起步的分析师工作站）——末段 Q 弯落 `(324, 96)`。
- **C6**（分析师工作站 → 老报表门户）不能直插（不同行，直横线会穿过公司官网）——经分区间隙（664..712）绕行：竖直段 x=676、水平段 y=70、侧边进门户左缘 `(732, 70)`。侧边进入让箭头体留在盒外、完整可见。

**箭头可见性经验法则**：标准箭头（`markerWidth=8`、`refX=7`）的箭头体沿路径方向从终点向回伸 7px。要可见，这 7px 尾巴必须在目标盒**外**。翻译：

- 上行进**上边**（盒在下）→ 体在盒内，只见 1px。**避免。**
- 下行进**上边**（盒在下）→ 体在盒上方，约 7px 可见。✓
- 右行进**左缘** → 体在盒左，约 7px 可见。✓
- 左行进**右缘** → 体在盒右，约 7px 可见。✓
- 下行进**下边**（盒在上）→ 体在盒内，只见 1px。**避免。**
- 上行进**下边**（盒在上）→ 体在盒下方，约 7px 可见。✓

源行与目标行的 y 区间重叠时优先**侧边进入**——单根水平线、箭头完整可见。源行错位时，绕经目标最近的分区背景进侧边，别从错误一侧够上 / 下边。
