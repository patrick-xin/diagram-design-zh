# 数据栈全景图（High-Level）

**最适合**：部署在容器编排器（Kubernetes、ECS、Nomad）上的端到端数据栈总览——采集 → 存储 → 查询 → 加工 → 可视化。组合了阶段 chevron 横幅、部署边界、调度条、身份底栏，以及（可选）右侧竖向 chevron 条承载横切关切（调度、安全、可观测）。

本类型是**参数化**的。整图由一小列输入（chevron、源、组件、连线）完全决定。给定输入，下面的公式告诉你每个形状落在哪——同一输入两次生成必须产出视觉一致的 SVG。

---

## 1. 输入——参数契约

画图前从用户处收齐（或接受一个 YAML/JSON 块）。本参考的一切都从这些输入推导，不现场发明几何。

```yaml
chevrons:                       # 从左到右有序；保留名自动升竖排
  - { name: "数据源",   columns: 1 }
  - { name: "采集",     columns: 1 }
  - { name: "存储",     columns: 1 }
  - { name: "加工",     columns: 1 }
  - { name: "可视化",   columns: 1 }
  - { name: "调度",     vertical: true }                     # 保留名 → 配调度条
  - { name: "安全",     vertical: true, color: "#b85450" }   # 染色配身份底栏
  - { name: "可观测",   vertical: true }                     # 保留名 → 配横切条 2

sources:                        # 外部；渲染在左侧虚线区
  - { name: "业务库",  type: "db",     connects_to: ["NiFi"] }
  - { name: "SFTP",   type: "ftp",    connects_to: ["NiFi"] }
  - { name: "网页表单", type: "web",   connects_to: ["NiFi"] }
  - { name: "遗留系统", type: "legacy", connects_to: ["NiFi"] }

components:                     # 集群内 + 横条 + 横切行
  - { name: "NiFi",      chevron: "采集",   kind: node,          role: "COLL"  }
  - { name: "MinIO",     chevron: "存储",   kind: node,          role: "STORE", focal: true }
  - { name: "Trino",     chevron: "存储",   kind: node,          role: "VIRT"  }
  - { name: "Notebook",  chevron: "加工",   kind: node,          role: "ANLZ"  }
  - { name: "Superset",  chevron: "可视化", kind: node,          role: "DASH"  }
  - { name: "DolphinScheduler", chevron: "调度", kind: bar,     subtitle: "定时补数 · 失败告警" }
  - { name: "身份",      chevron: "安全",   kind: cross-cutting, subtitle: "Keycloak · LDAP · OIDC", color: "#b85450" }
  - { name: "监控",      chevron: "可观测", kind: cross-cutting, subtitle: "Prometheus · Grafana · Loki" }

connections:                    # 显式边；触焦点的自动变 accent
  - { from: "NiFi",      to: "MinIO",       style: "primary"   }
  - { from: "MinIO",     to: "Notebook",    style: "primary"   }
  - { from: "Trino",     to: "MinIO",       style: "query" }   # 查询对·实线请求
  - { from: "MinIO",     to: "Trino",       style: "query" }   # 查询对·虚线回写
  - { from: "Notebook",  to: "Superset",    style: "secondary" }
  - { from: "Trino",     to: "Superset",    style: "secondary" }
  - { from: "Airflow",   to: ["NiFi", "Notebook", "Superset"], style: "trigger" }

focal: "MinIO"                  # 恰好一个；缺省 = 「存储」下首个 kind=node
dark: false
```

**保留 chevron 名**（即使不写 `vertical: true` 也恒竖排）：`调度`、`安全`、`可观测`、`治理`、`备份`。

**保留 `kind` 值：**

- `node`——集群内的标准盒（默认）。
- `bar`——横贯集群顶部的横条。通常一根（调度）；配对规则见 §5。
- `cross-cutting`——横贯主体宽度的横条（止于右条边距），垫在集群下方。**零或多根**；每根比上一根低 44px（§2.5），与竖向 chevron 1:1 配对（§5）。

**可选 `color`**（逐组件，hex 字符串）：染组件的容器与内容、不碰连线。见 §3.4。省着用——自定义色是语义旗（红 = 安全关切），不是装饰。

**源 `type` → 图标映射**（用 primitive-icons.md；点名才上）：`db`→database、`ftp`→bucket 或上传箭头、`web`→internet、`legacy`→server、`api`→api。也接受目录里的显式图标名。

---

## 2. 布局公式——确定性几何

下面每个坐标都从输入推导。**示例里不许有无出处的硬编码数字。**

### 2.1 画布

```
has_vertical       = 任一 chevron 带 vertical 或命中保留名
right_strip_w      = 28  if has_vertical else 0
strip_margin       = 8   if has_vertical else 0   # 主体与右条的间隙
effective_w        = 1000 - right_strip_w - strip_margin     # 1000 或 964

n_cross            = kind == "cross-cutting" 的组件数
strip_y_bot        = max(428, 388 + n_cross * 44 - 4)
viewBox_h          = max(540, strip_y_bot + 112)             # 112 留给图例
viewBox            = "0 0 1000 {viewBox_h}"
```

一切横向元素（chevron 横幅、集群、调度条、身份 / 横切条）止于 `effective_w`。右条在 `x = 1000 - right_strip_w`（=972）。中间 8px 是呼吸带——**不放内容**。

横切条多于一条时 `viewBox_h` 变高：1 条 → 540、2 条 → 600（规则取 20 的倍数圆整）。

### 2.2 横向 chevron 横幅

```
y_banner           = 4
h_banner           = 28
horizontals        = 非竖排、非保留名的 chevron
sum_columns        = Σ c.columns
base_unit          = floor_to_4(effective_w / sum_columns)        # 4 的倍数
widths             = [max(120, base_unit * c.columns) for c]
widths[-1]        += effective_w - sum(widths)                   # 尾部吸收余数
x_boundaries       = [0] + widths 的累计和
chevron_cx(C)      = (x_boundaries[i] + x_boundaries[i+1]) / 2
```

**多边形形状：**

- 首（最左）：`(x0,4) (x1-12,4) (x1,18) (x1-12,32) (x0,32)`
- 中间：`(x0,4) (x1-12,4) (x1,18) (x1-12,32) (x0,32) (x0+12,18)`
- 末（最右）：`(x0,4) (effective_w,4) (effective_w,32) (x0,32) (x0+12,18)`

填充交替 `ink` / `muted`（浅色档）或 `paper-dark@0.18` / `paper-dark@0.12`（深色档，纸色基梯子）。标签：纸色——纯拉丁走 eyebrow 规格（mono 7–8px · 0.18em + uppercase）；**中文 sans 12px**（竖排条上随条旋转 −90°）。`text-anchor="middle"`、居中 `chevron_cx, 21`。

**颜色覆盖**（逐 chevron，横竖皆可）：可选 `color: "#hex"` 替换该 chevron 的交替填充。用来给与自定义色组件配对的阶段做旗（身份条用 `sem-security` 时「安全」chevron 同色）。规则：

- 覆盖只作用于多边形填充。标签保持纸色——**绝不重染 chevron 标签**。
- 交替序号不挪；邻条保持自然填充，哪怕出现两条相邻同色。不「修」这个——覆盖本来就稀有（每图 ≤ 2）。
- 深色档同 hex，除非对纸色标签对比吃亏；吃亏就在该 chevron 上记 `color_dark` 换深档色。
- chevron 覆盖独立于配对组件的色，但配对同 hex（chevron + 条同色）是让这一列读作一个关切的习惯做法。

### 2.3 源区（虚线，外部）

```
sources_x / sources_y = 4 / 40
sources_w             = x_boundaries[1] - 8        # 首 chevron 宽，两侧各让 4px
sources_h             = 336
```

描边 `ink@0.20`、宽 0.8、`stroke-dasharray=6,3`、`rx=6`；区填充 `ink@0.02`。

### 2.4 集群边界（实线）

```
cluster_x            = x_boundaries[1] + 4         # 源区右缘 + 4px 泳道
cluster_y            = 40
cluster_w            = effective_w - cluster_x
cluster_h            = 336
```

描边 `ink@0.18`、宽 1.2、`rx=8`；填充 `ink@0.02`。集群标签（如「Kubernetes 集群」）在 `(cluster_x + 16, 356)`，中文 sans 12px `muted`。

### 2.5 横切条（身份、可观测……）

零或多根 `kind: cross-cutting` 垫在集群下方，每根一条 40px 行、4px 间隙：

```
cross_x        = 4
cross_y(k)     = 388 + k * 44                  # 388, 432, 476, …
cross_w        = effective_w - 4               # 横贯主体宽、止于右条边距
cross_h        = 40
```

描边 `ink@0.20`、宽 0.8、`rx=6`；填充 `ink@0.05`。名字居中 `(effective_w/2, cross_y+18)`（sans 12px 600），副标 `(effective_w/2, cross_y+33)`（mono 9px 或中文 sans 12px `muted`）。

**每根横切条与右条里的一根竖向 chevron 1:1 配对**（§5）。

### 2.6 调度条组件（集群内）

```
bar_x / bar_y   = cluster_x + 12 / 52
bar_w           = cluster_w - 24
bar_h           = 44
```

描边 `ink@0.18`、宽 0.8、`rx=4`；填充 `ink@0.05`。名字居中 `(bar_x + bar_w/2, 71)`、副标 `(bar_x + bar_w/2, 84)`。

### 2.7 组件节点（集群内）

```
node_w          = 152
node_h          = 80                            # 焦点同高、accent 边
node_cx(N)      = chevron_cx(N.chevron)         # ← 不可谈判
node_x(N)       = node_cx(N) - node_w/2
```

chevron 名下挂 K 个节点时竖排：

```
first_top_y     = 120（该列有 bar 时）否则 64
gap             = 16；相邻两行间画查询对（§3.2）时放宽到 32
row_top(k)      = first_top_y + k * (node_h + gap)
```

**焦点节点**：`fill="accent@0.08"`、`stroke="accent"`、宽 1.2，名字文本 accent。其余节点：白底、`stroke="ink@0.40"`、宽 1（backend 描边梯）。角色角标在左上 `(node_x+8, node_y+6)`、高 12；名字居中 `(node_cx, node_y+46)` sans 14px 600；副标 `(node_cx, node_y+62)` mono 9px `muted`。

### 2.8 源节点（虚线区内）

```
src_node_w      = sources_w - 24
src_node_h      = 64                            # 统一；按 ≤4 源选高
src_node_x      = sources_x + 12
src_first_top_y = 56
src_gap         = 16
src_row_top(k)  = 56 + k * (64 + 16)
```

同集群节点的角标 / 名字 / 副标版式。角色角标文本：`EXT`。**上限 4 个源**；更多就拆图。源框与虚线区四周 ≥12px（本式为左右 12、上下 16）——框贴区边即反模式。

### 2.9 右条——竖向 chevron

```
strip_x         = 1000 - 28
verticals       = 竖排 chevron（显式 vertical 或保留名）
strip_y_top     = 40
strip_y_bot     = max(428, 388 + n_cross * 44 - 4)
strip_h_total   = strip_y_bot - strip_y_top
heights         = [floor_to_4(strip_h_total / len(verticals))] * n
heights[-1]    += strip_h_total - sum(heights)       # 末条吸收余数
```

例：2 竖条（调度 + 安全）+ 1 横切 → `heights = [192, 196]`、布局 `[40..232, 232..428]`。相邻边共享同一 y（无间隙）——同横向 chevron 共享 x。

**多边形形状**（自上而下，镜像 §2.2）：

- 首（最上）：平顶、下尖——`(x,y0) (x+28,y0) (x+28,y1-12) (x+14,y1) (x,y1-12)`
- 中间：上凹、下尖——`(x,y0) (x+14,y0+12) (x+28,y0) (x+28,y1-12) (x+14,y1) (x,y1-12)`
- 末（最下）：上凹、平底——`(x,y0) (x+14,y0+12) (x+28,y0) (x+28,y1) (x,y1)`

填充同横向交替（`ink` / `muted`）。标签：纸色中文 sans 12px，**旋转 −90°**，锚 `(strip_x+14, (y0+y1)/2)`。

竖向 chevron 同样吃 §2.2 的逐条 `color` 覆盖——hex 上多边形填充、旋转标签保持纸色。

### 2.10 图例

```
legend_line_y  = 内容底 + 20        # 内容底 = 376（无横切条）或 strip_y_bot
line           = x4 → effective_w    # 与横幅 / 分区 / 底栏共享左右缘
LEGEND 标签    = (4, legend_line_y + 16)   mono 9px · 0.18em
条目行         = legend_line_y + 28 起；条目自 x4 起、组间 40px
```

图例横线与条目左缘**必须**对齐内容左右缘（4 与 effective_w）——内缩的图例线会让图例看起来浮在半空。

---

## 3. 连线规则（强制）

不可谈判。样式**自动**按拓扑挑——焦点触及、横条发出的边不许用户覆写样式。

| `style` | 描边 | 宽 | 虚线 | 箭头 | 何时必须 |
|---|---|---|---|---|---|
| `primary` | `accent` | 1.2 | — | `arrow-accent` | 任一端是 `focal` 节点的边。 |
| `secondary` | `muted` | 1.0 | — | `arrow` | 源→组件、组件→组件且两端都不是焦点的默认。 |
| `trigger` | `muted` | 1.0 | `4,3` | `arrow-sm` | 每根从 `kind: bar` 组件发出的边。 |
| `query` | `ink@0.30` | 1.0 | `4,3` | `arrow` | 回读边（如 Trino ↔ 存储枢纽）。 |

**defs 块**（必需，恰好四支）：

```svg
<defs>
  <marker id="arrow"        markerWidth="8" markerHeight="6" refX="7" refY="3"   orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#565e7e"/></marker>
  <marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3"   orient="auto"><polygon points="0 0, 8 3, 0 6" fill="#1a4dd9"/></marker>
  <marker id="arrow-sm"     markerWidth="6" markerHeight="5" refX="5" refY="2.5" orient="auto"><polygon points="0 0, 6 2.5, 0 5" fill="#565e7e"/></marker>
  <marker id="arrow-dim"    markerWidth="8" markerHeight="6" refX="7" refY="3"   orient="auto"><polygon points="0 0, 8 3, 0 6" fill="rgba(41,49,79,0.40)"/></marker>
</defs>
```

### 3.1 出 / 入边（不可谈判）

| 边类 | 源出边 | 目标入边 |
|---|---|---|
| 源 → 集群节点 | 源**右** | 目标**左** |
| 组件 → 组件（集群内） | **右** | **左** |
| 横条 → 节点 | 条**底** | 节点**顶** |
| 横切条 | ——（不发边） | —— |
| 竖向 chevron | ——（只有标签、不发边） | —— |

### 3.2 路由

- 正交肘线、每路径**至多两弯**；每个弯 Q 贝塞尔 8px 圆角。
- z 序：**所有连线先于任何节点 rect**（节点填充掩蔽线端）。
- 每 `<path>` / `<line>` 恰好一个 `marker-end`。绝无 `marker-start` + `marker-end` 并用。
- **端点压盒缘**：起止点必须落在盒的边缘线上。起点缩进盒内 = 整段线被后画的节点填充盖住，等于没画。
- 标签：**默认不逐边打标签**——chevron 横幅 + 图例承担语义。列间隙通常只有 ~48px，骑线遮罩会把线吃没。确需标注时仅限线段长 ≥72px 的边，遮罩与线留 6–10px 净空。`trigger` 与 `query` 永不标。
- **查询对**：存储枢纽与其查询引擎（如 Trino ⇄ MinIO 垂直相邻时）画 ±4px 平行双竖线——实线 = 请求（指向存储）、虚线 = 回写；对应 §2.7 的 32px 行距。

### 3.3 交越

- 避免。接受交越之前先改走 chevron 分隔干线（§4）。
- 实在免不了，后画的线加 6px 弧跳跨过先画的。

### 3.4 组件颜色覆盖

可选 `color: "#hex"`。**只**重染组件的容器与内容——连线永不变色，保持 §3 的拓扑驱动样式。

**落点**（`C = color`）：

| 元素 | 浅色 | 深色 |
|---|---|---|
| 容器填充 | `C@0.06` | `C@0.10` |
| 容器描边 | `C@0.35`（节点宽 1、条 0.8） | `C@0.45` |
| 角标描边 / 文字 | `C@0.40` / `C@0.85` | `C@0.55` / `C` |
| 名字文本 | `C` | 提亮 `C` |
| 副标文本 | **不变**（muted） | **不变**（muted） |
| 触达该组件的连线 | **不变** | **不变** |

副标保持 muted——它是括号性元数据；只有主身份（名 + 边框）承载颜色信号。

**规则：**

- **焦点节点上禁用。** 焦点已经 accent（§2.7）。焦点上的 `color` 被忽略——accent 赢。
- **源节点上禁用。** 源在集群外、保持中性。
- 自定义色组件每图 **≤ 2**（焦点之外）。三个以上带色的东西抹掉信号。
- **连接线上无色。** 想要彩边就去 §3 挑别的 `style`，不是覆盖。

**语义用法**（推荐）：`sem-security` 铁锈红（安全 / 身份）、`sem-observability` 岩蓝（可观测）、`sem-governance` 橄榄绿（治理 / 血缘）、`sem-backup` 暖棕（备份 / 灾备）。品牌没有硬要求就守这套。逐组件随机 hex 正是本技能规避的失败模式。

---

## 4. 块扇出规则

可复现性的最大坑。定死这些，图就可预测。

### 4.1 源扇出（一源 → N 组件）

```
exit_x   = source.right
trunk_x  = cluster_x - 8                     # 集群边框前 4px 泳道
```

每目标路径：`M exit_x,src_cy → H trunk_x → V target_cy → H target.left`，Q 角。

### 4.2 组件扇出（一组件 → N 组件）

```
exit_x   = node.right
trunk_x  = x_boundaries[源.chevron 序 + 1] + 4   # chevron 分隔线外 4px
```

每目标路径：`M exit_x,src_cy → H trunk_x → V target_cy → H target.left`。

### 4.3 扇出上限

**每节点出边 ≤ 3。** 超过 3 引入枢纽（通常是 `focal` 节点）。chevron 横幅就是图例；一个节点向四个下游扇出，它其实就是枢纽——明说。

### 4.4 横条下扎（调度 → N 节点）

```
drop_x(target) = target.cx
drop_y_start   = bar.bottom
drop_y_end     = target.top
```

笔直竖线、`style: trigger`。每目标一根。**无弯**——横条下扎永不拐肘。

### 4.5 源竖向错位

多源连同一目标（如四源 → NiFi）时，目标上的入边 y 错开：

```
entry_y(k) = target.cy - ((N - 1) / 2 - k) * 16     # 16px 等距、以中线对称
```

避免箭头在目标左缘叠成一摞。

---

## 5. 竖向 chevron——语义

保留名 `调度`、`安全`、`可观测`、`治理`、`备份` 恒渲染在右条（§2.9）。任何带 `vertical: true` 的 chevron 无论名字都按保留式竖排处理。规则：

- **配对规则（强制、1:1）**：每根竖向 chevron 恰好配一个横贯组件。反向放宽——横贯组件**可以**无竖向 chevron 单独存在（此时无右条、画布不收窄）——如一根孤立的 Identity Manager 底栏。可配对的两种组件：

  - `kind: bar`——住在集群内（顶行）。习惯配「调度」。
  - `kind: cross-cutting`——住在集群下方，每组件一行。配「安全」「可观测」「治理」等。

  输入里出现无配对的竖向 chevron → 停下来问用户——图不完整。无配对的横贯组件合法（见上）。

- **数量约束**：`len(verticals) ≤ len(bars) + len(crosscuts)`（竖条必须有配对；横贯组件可多出）。右条在全部竖条间均分（§2.9），chevron 与其条 / 行的 y 对齐只是近似——**标签**才是配对信号，不是 y 像素。
- **顺序惯例**：竖条自上而下先写配 bar 的（调度），再按横切条在集群下方出现的顺序写配 crosscut 的。视觉阅读顺序一致。
- **无连线**：竖向 chevron 自己不发连接线。它们是**横切关切的列标签**。
- **无节点**：`kind: node` 不许挂到竖向 chevron。节点永远属于横向阶段。
- **右条存在性**：有任何竖向 chevron 就保留右条（`effective_w = 964`）、**所有**横向 chevron 宽度与集群几何随之收窄。绝不把竖向 chevron 画在集群上面。

视觉契约：竖向 chevron 的列在近似 y 带上「拥有」它的条 / 横切行。调度（条顶）↔ 调度条（集群顶）。安全 ↔ 身份条。可观测 ↔ 监控条（身份下方）。以此类推。

---

## 6. 深色档

`dark: true` 时换这些 token：

| Token | 浅色 | 深色 |
|---|---|---|
| 纸面 | `paper` | 墨色深底（style-guide 深色列） |
| 墨色 / muted | `ink` / `muted` | 深色列反转值 |
| chevron 深填充 | `ink` | `paper-dark@0.18` |
| chevron 浅填充 | `muted` | `paper-dark@0.12` |
| chevron 标签 | 纸色 | 纸色（不变） |
| 虚线框 | `ink@0.20` | `paper-dark@0.20` |
| 集群框 | `ink@0.18` | `paper-dark@0.18` |
| 节点填充 | 白 | `paper-dark@0.05` |
| 节点描边 | `ink@0.40` | `paper-dark@0.20` |
| 焦点填充 / 描边 | `accent@0.08` / `accent` | `accent-dark@0.12` / `accent-dark` |
| primary 连线 | `accent` | `accent-dark` |

---

## 7. 复现清单（品味门）

出 SVG 前逐项核。任一失败 → 修，不交。

1. 每个集群 `node.cx` 等于其 chevron 的 `cx`（§2.2 + §2.7）。这是 chevron 横幅作为真图例的根本。
2. 每个 chevron 宽是 4 的倍数且 ≥ 120。
3. 保留右条（28px）**当且仅当**声明了竖向 chevron。有 → `effective_w = 964`；无 → 1000。
4. **恰好一个** `focal` 节点。输入未设则缺省「存储」下首个 `kind: node`。
5. 任一端是焦点节点的边用 `style: primary`（accent 描边 + `arrow-accent`）。
6. 每根从 `kind: bar` 发出的边用 `style: trigger`（虚线 + `arrow-sm`）。
7. 横切条（若有）**不发**边。
8. 没有节点出边 > 3；有也是声明的 `focal` / 枢纽。
9. 所有 `<path>` / `<line>` 先于任何节点 `<rect>`（z 序）。
10. 每根竖向 chevron 与恰好一个 `bar` / `cross-cutting` 组件配对（§5）；横贯组件可无竖条单独存在（`len(verticals) ≤ len(bars) + len(crosscuts)`）。
11. `viewBox_h = max(540, strip_y_bot + 112)`——多横切条时加高画布保图例。
12. 自定义色（§3.4）只上容器 + 名字；连线拓扑驱动。焦点之外自定义色组件 ≤ 2。
13. 过 SKILL.md §9（4px 网格；accent ≤2；mono 只给技术内容；发丝线；无阴影）。
14. 连线起止点全部压在盒缘上；每个 `kind: node` 至少一条入边或出边——**无孤岛节点**（终态消费端可以只有入边）。
15. 图例横线 x4 → effective_w、条目自 x4 起排（§2.10）——与整体内容左右缘齐平。

---

## 8. 反模式

- 省掉 chevron 横幅——它是视觉列到功能阶段的钥匙。
- 节点 x 中心偏离 chevron（§7 第 1 条）——破坏「横幅即图例」契约。
- 竖向 chevron 画在集群上（浮层）而不是保留右条里。
- 多于一个焦点节点——存储枢纽（MinIO / S3）就是**那个**焦点。
- 外部区用实线框——虚线框是「这些在集群外」的信号。
- 身份条画进集群边界内——它作用于所有组件、必须横贯全宽。
- 无配对条 / 横切组件的竖向 chevron——见 §5 配对规则。
- 横条发出的边画实线——调度触发必须虚线。
- 骑线标签塞进窄间隙（<72px）——白底遮罩把箭头吃没，只剩线头。
- 连线起点缩进盒子内部——被后画的节点填充盖掉，整段"消失"。
- 源框贴虚线区边缘——区内框与边框四周 ≥12px。
- 孤岛节点（无任何入/出边）——看板类终端也至少要有一条入边。
- 图例线内缩（40→960 那种）不与内容左右缘齐平——反模式。
- 源向 >3 组件扇出而无枢纽。

---

## 9. 示例

- [`assets/example-high-level.html`](../assets/example-high-level.html) — 纯横向、五阶段、调度条 + 统一身份底栏、浅色档
