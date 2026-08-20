# 数据平台安全矩阵（DP security matrix）

**最适合**：记录数据平台的逐角色 / 逐组件访问权限——一个网格：每行一个平台组件（Keycloak、MinIO 桶、Trino 目录、JupyterHub、NiFi……），每列一个角色 / AD 组（数据管理员、数据工程师、数据科学家、数据消费者……）。交叉格放权限值（管理 / 完全 / 读写 / 只读 / SELECT / 登录 / 无访问）并配与权限等级匹配的视觉类。至多一格可标焦点，标记关键访问规则（如「数据消费者对指标目录**只有** SELECT——唯一消费出口」）。

干系人要审计**谁能干什么**时用。问题是**谁能连谁**（拓扑 / 协议）→ 用数据平台集成图。

本类型是**参数化**的——§1 输入 schema 经 §2 公式驱动每个坐标。规则形状对齐 type-medallion / process / data-flow：焦点规则、颜色覆盖、深色档、复现清单跨类型读法一致。

---

## 1. 输入——参数契约

```yaml
title:    "平台访问矩阵"
subtitle: "四个标准组 × 平台组件"

roles:                                  # 2..6 列，从左到右
  - { name: "数据管理员", code: "DL-DataAdmins"      }
  - { name: "数据工程师", code: "DL-DataEngineers"   }
  - { name: "数据科学家", code: "DL-DataScientists"  }
  - { name: "数据消费者", code: "DL-DataConsumers"   }

components:                             # 2..14 行，从上到下
  - { name: "Keycloak",                    hint: "SSO" }   # hint = 标签格内右对齐旁注
  - { name: "MinIO · raw 桶" }
  - { name: "MinIO · 脱敏 · staging · 指标" }
  - { name: "Trino · raw 目录" }
  - { name: "Trino · 脱敏-staging" }
  - { name: "Trino · 指标" }
  - { name: "JupyterHub" }
  - { name: "NiFi" }

cells:                                  # 显式 (行, 列) 条目；缺省 → "none"
  # value = 显示文本（自由）
  # level = 视觉类：full | rw | read | none（封闭词表，驱动样式）
  # focal: true（至多 1）——把 level 覆写为焦点样式
  # sub: "第二行文字"     ——焦点格内用
  # color: "#hex"         ——可选逐格颜色覆盖（§4）
  - { row: 0, col: 0, value: "管理", level: "full" }
  - { row: 0, col: 1, value: "登录", level: "read" }
  # ……按行铺满……

  - { row: 5, col: 0, value: "完全",   level: "full" }
  - { row: 5, col: 1, value: "读写",   level: "rw"   }
  - { row: 5, col: 2, value: "SELECT", level: "read" }
  - { row: 5, col: 3, value: "仅 SELECT", sub: "唯一消费出口", focal: true }

none_label: "无访问"                     # 缺格时渲染的默认文本
dark: false
```

**字段语义：**

- `roles[j].name`——主角色标签（`node-name` 角色 sans 12px、墨色横幅上的白字）。
- `roles[j].code`——AD 组标识副标（mono 9px、白字 0.85 透明度）。
- `components[i].hint`——标签格内可选的右对齐旁标（mono 9px `muted`，如 `"SSO"`、`"S3 API"`）。
- `cells[k].level`——封闭词表 `full | rw | read | none`，驱动填充 / 描边 / 文字色（§2.4）。
- `cells[k].value`——自由显示文本。领域标签（`"读写"`、`"SELECT"`、`"登录"`）不用发明新 level。
- `cells[k].focal: true`——全图**至多一格**。把 `level` 覆写为焦点样式。
- `cells[k].sub`——可选第二行（配焦点用）。中文子标 12px · 焦点行下方。
- `cells[k].color: "#hex"`——可选逐格颜色覆盖（§4）。

---

## 2. 布局公式——确定性几何

```
# 常量
left_pad         = 12
right_pad        = 48
comp_col_w       = 208
comp_role_gap    = 12
role_col_w       = 148
role_col_gap     = 16
header_h         = 52
row_h            = 36
row_stride       = 40

# 计数
n_roles          = len(roles)        # 2..6
n_components     = len(components)   # 2..14

# 画布
viewBox_w        = left_pad + comp_col_w + comp_role_gap
                   + n_roles * role_col_w + (n_roles - 1) * role_col_gap
                   + right_pad
                   # 4 角色 → 12 + 208 + 12 + 592 + 48 + 48 = 920

header_y         = 72
row_y(k)         = 140 + k * 40                  # 140, 180, 220, ...
rows_bottom      = row_y(n_components - 1) + row_h       # 8 行 → 456
legend_y_top     = rows_bottom + 20                      # 476
viewBox_h        = legend_y_top + 44                     # 520

# 列位置
comp_col_x       = 12
role_col_x(j)    = 12 + 208 + 12 + j * (148 + 16)        # 232, 396, 560, 724
role_col_cx(j)   = role_col_x(j) + 74                    # 306, 470, 634, 798
```

### 2.1 背景

整个 viewBox 铺纸色实底，无纹理。

### 2.2 表头行（y = 72，h = 52）

**组件列表头格**：rect `(12, 72, 208, 52)` 白底、`ink @ 0.12` 描边 0.8、`rx=6`。两行居中标签：行 1「组件」（`node-name` sans 12px · ink）；行 2「× AD 组」（mono 9px `muted`）。

**角色横幅（每角色一条）**：rect `(role_col_x(j), 72, 148, 52)`、填充 `ink`、`rx=6`。两行居中：行 1 角色名（sans 12px · 白）；行 2 组代码（mono 9px · 白 · 0.85）。

### 2.3 数据行（y = row_y(k)，h = 36）

**组件标签格**：rect `(12, row_y(k), 208, 36)` 白底、`ink @ 0.12` 描边 0.8、`rx=4`。名字左对齐 `(24, row_y+24)`：sans 12px · ink。hint（若有）右对齐 `(196, row_y+24)`：mono 9px `muted`。

**值格（每角色 × 每组件一格）**：rect `(role_col_x(j), row_y(k), 148, 36)`、`rx=4`、`ink @ 0.12` 描边 0.6。填充与文字色看 `level`（或焦点标记）——§2.4。值文本居中 `(role_col_cx(j), row_y+24)`：sans 12px。焦点格主值上提到 y=row_y+20、副行 `sub` 在 y=row_y+32（12px）。

### 2.4 格样式表

| `level` | 填充 | 描边 | 文字色 | 字重 |
|---|---|---|---|---|
| `full` | `ink @ 0.08` | `ink @ 0.12` | `ink` | 600 |
| `rw` | `paper` | `ink @ 0.12` | `ink` | 400 |
| `read` | `muted @ 0.08` | `ink @ 0.12` | `muted` | 400 |
| `none` | `paper` | `ink @ 0.12` | `muted` | 400 |
| **focal** | `accent @ 0.08` | `accent`（1.4） | `accent` | 600 |

`none` 的文字用 `muted` 而不是 `soft`——12px 文字要过 AA，`soft` 在纸面上到不了（实测 3.48:1）。焦点格可带第二行（`sub:`）：accent · 12px · 0.85 透明度。

### 2.5 图例（y_top = legend_y_top，高约 30）

`legend_y_top` 处发丝分隔线。线下一行样式样本 + 标签——只出现图内实际用到的类。

- `LEGEND` 角标在 `(12, legend_y_top + 20)`：mono 9px · `muted` · 0.18em。
- 每类：样本 rect（14×12 `rx=2`）+ 中文标签 12px。
- 条目左→右约 120px 步长排表；`n_roles ≥ 6` 时才折第二行。

---

## 3. 格子，不是连线

矩阵图**没有连线**——格与格之间没有箭头、没有流线。图的信息全在格内容 + 格样式里。唯一「像连线」的元素是焦点格的 accent 边框，它「点名」某个交叉。

格子**不发边**。别往格里或格间加箭头——那是别的类型的事。

---

## 4. 颜色覆盖

三条独立的覆盖轴——逐格、逐组件（行）、逐角色（列）。全部可选、全用同一个 `color: "#hex"` 字段、全取同一套推荐色板。对齐 type-high-level §4 / type-process §4 / type-medallion §4。

### 4.1 逐格 `color`

| 元素 | 浅色 | 深色 |
|---|---|---|
| 格填充 | `C@0.08` | `C_light@0.12` |
| 格描边 | `C@0.45` 宽 1.0 | `C_light@0.55` 宽 1.0 |
| 值文本 | `C` | `C_light` |
| 副文本（若有） | `C@0.85` | `C_light@0.95` |

### 4.2 逐组件 `color`（`components[i].color`）

只染该行的**标签格**（左列）。行内数据格保持逐格 `level` 样式——行色标记这个组件**是什么**，不是里面有什么权限。

| 元素 | 浅色 | 深色 |
|---|---|---|
| 标签格填充 | `C@0.06` | `C_light@0.10` |
| 标签格描边 | `C@0.45` 宽 0.8 | `C_light@0.55` 宽 0.8 |
| 组件名 | `C` | `C_light` |
| hint 文本 | 不变（muted） | 不变（muted） |

### 4.3 逐角色 `color`（`roles[j].color`）

只染**列横幅**（顶行）。下面的格保持 `level` 样式。

| 元素 | 浅深同值（横幅两档一致） |
|---|---|
| 横幅填充 | `C` |
| 角色名 + 代码文本 | `C` 深（亮度 ≤ 0.5）→ `paper`；浅 → `ink` |

选到中间亮度的 hex（如黄 `sem-workspace`）时文字自动翻 ink 保对比。`roles[j].text_color: "#hex"` 可覆写自动选择。

### 4.4 规则

- **焦点格赢。** 焦点格忽略 `color` 覆盖——accent 恒定。
- **逐格 `color` 覆盖该格的 `level` 样式。**
- **逐组件 / 逐角色的覆盖有作用域**：组件 → 只行标签；角色 → 只横幅。都**不**扩散进矩阵主体。要点名某个交叉就用逐格。
- 上限：全图自定义色实体（格 + 组件 + 角色）**≤ 5**。超过 5 矩阵读成彩色噪声——拆几张或重新想哪个颜色承载哪个关切。

### 4.5 推荐色板（同其他参数化类型）

- `sem-security` 铁锈红——安全提权 / 破玻璃 / 审计标记
- `sem-observability` 岩蓝——质量 / 监控 / 可观测闸
- `sem-governance` 橄榄绿——已批准 / 治理通过 / 可发布
- `sem-workspace` 暖黄——工作区 / 沙盒 / 科学家区
- `sem-backup` 暖棕——归档 / 冷存 / 灾备

---

## 5. 焦点规则

每图**恰好一个**焦点格（或零个）。焦点格：

- 焦点样式（accent 填充 + accent 描边 1.4 + accent 文字加粗）
- 可带两行内容：主 `value` 在 `row_y(k)+20`、`sub` 在 `row_y(k)+32`
- 点出全图的中心安全主张——把这张图的姿态与通用权限表区分开的那**一条**访问规则

`focal: true` 的格数为 0 或 >1 → 停下来问用户。

---

## 6. 深色档

| Token | 浅色 | 深色 |
|---|---|---|
| 纸面 / 墨色 | `paper` / `ink` | `ink` / `paper` |
| muted / soft | `muted` / `soft` | `soft` / `muted` |
| accent | `accent` | `accent` |
| 角色横幅填充 | `ink` | `ink`（不变——深色档横幅即纸色同族深块，白字照读） |
| 表头 / 行描边 | `ink @ 0.12` | `paper @ 0.18` |
| full 填充 | `ink @ 0.08` | `paper @ 0.10` |
| rw 填充 | `paper` | `paper @ 0.06` |
| read 填充 | `muted @ 0.08` | `soft @ 0.12` |
| none 填充 | `paper` | `paper @ 0.02` |
| 焦点填充 / 描边 | `accent @ 0.08` / `accent` | `accent @ 0.12` / `accent` |
| 自定义色 | `C` | `C_light`（提亮 ~15%） |

---

## 7. 复现清单（品味门）

出 SVG 前逐项核：

1. `viewBox = "0 0 {viewBox_w} {viewBox_h}"` 经 §2 推导（4 角色 × 8 组件 → 920 × 520）。
2. 表头行 y=72 h=52。组件表头白底两行「组件 / × AD 组」；角色横幅 ink 填充、白字名 + 组代码。
3. 数据行 y=140 起、步长 40、高 36；`rows_bottom = 140 + (n−1)·40 + 36`。
4. 组件标签格 `rx=4`、名字左对齐 x=24、hint 右对齐 x=196。
5. 每个值格 `rx=4`、描边 `ink @ 0.12` 0.6、填充与文字匹配 §2.4 的 `level`。
6. **恰好一个**焦点格（或零）。描边 `accent` 宽 1.4；主值 y=row_y+20；`sub`（若有）y=row_y+32。
7. `cells:` 里缺的格渲染为 `level: "none"` + `none_label` 文本（默认「无访问」）。
8. 自定义色格 ≤ 2（焦点格之外）。
9. 全 SVG 无任何连线元素。
10. 图例条在 `legend_y_top`、实际用到的每类一个样本、上方发丝线。
11. `viewBox_h` 随 `n_components` 长、`viewBox_w` 随 `n_roles` 宽。

---

## 8. 反模式

- **多个焦点格**——焦点标记**那条**关键访问规则；>1 信号清零。
- **任何地方出现连线**——矩阵是值驱动的；箭头属于集成图 / 流程图。
- **自由发挥的 `level`**——封闭词表 `full | rw | read | none`。自由文本进 `value`、任意染色进 `color`。
- **整行 / 整列染色**——`color` 逐格用。整行整列的高亮容易过度强调、把矩阵塌缩成清单。
- **拿 `none_label` 当「待定」占位**——`none` 是**无访问**。权限未知就留空并在别处说明；不渲染含糊状态。
- **角色 > 6**——拆两张矩阵（人类角色 vs 服务账号）再超过 6 列。
- **组件 > 14**——按域拆（存储 / 计算 / 可观测 / 治理）再超过 14 行。
- **用矩阵记录权限「怎么授予」**——那是流程图 / 时序图的事。矩阵展示每个角色**能做什么**，不是授予流。

---

## 9. 示例

- [`assets/example-dp-security-matrix.html`](../assets/example-dp-security-matrix.html) — 浅色标准版（4 角色 × 8 组件，焦点 = 数据消费者 × Trino 指标）

---

## 10. 走例 YAML——`example-dp-security-matrix.html` 的完整输入

```yaml
title:    "平台访问矩阵"
subtitle: "四个标准组 × 平台组件"

roles:
  - { name: "数据管理员", code: "DL-DataAdmins"      }
  - { name: "数据工程师", code: "DL-DataEngineers"   }
  - { name: "数据科学家", code: "DL-DataScientists"  }
  - { name: "数据消费者", code: "DL-DataConsumers"   }

components:
  - { name: "Keycloak",                      hint: "SSO" }
  - { name: "MinIO · raw 桶" }
  - { name: "MinIO · 脱敏 · staging · 指标" }
  - { name: "Trino · raw 目录" }
  - { name: "Trino · 脱敏-staging" }
  - { name: "Trino · 指标" }
  - { name: "JupyterHub" }
  - { name: "NiFi" }

cells:
  # 行 0 — Keycloak
  - { row: 0, col: 0, value: "管理", level: "full" }
  - { row: 0, col: 1, value: "登录", level: "read" }
  - { row: 0, col: 2, value: "登录", level: "read" }
  - { row: 0, col: 3, value: "登录", level: "read" }
  # 行 1 — MinIO raw
  - { row: 1, col: 0, value: "完全",   level: "full" }
  - { row: 1, col: 1, value: "读写",   level: "rw"   }
  - { row: 1, col: 2, value: "无访问", level: "none" }
  - { row: 1, col: 3, value: "无访问", level: "none" }
  # 行 2 — MinIO 脱敏/staging/指标
  - { row: 2, col: 0, value: "完全",   level: "full" }
  - { row: 2, col: 1, value: "读写",   level: "rw"   }
  - { row: 2, col: 2, value: "只读",   level: "read" }
  - { row: 2, col: 3, value: "无访问", level: "none" }
  # 行 3 — Trino raw
  - { row: 3, col: 0, value: "完全",   level: "full" }
  - { row: 3, col: 1, value: "读写",   level: "rw"   }
  - { row: 3, col: 2, value: "无访问", level: "none" }
  - { row: 3, col: 3, value: "无访问", level: "none" }
  # 行 4 — Trino 脱敏-staging
  - { row: 4, col: 0, value: "完全",   level: "full" }
  - { row: 4, col: 1, value: "读写",   level: "rw"   }
  - { row: 4, col: 2, value: "SELECT", level: "read" }
  - { row: 4, col: 3, value: "无访问", level: "none" }
  # 行 5 — Trino 指标（焦点格在列 3）
  - { row: 5, col: 0, value: "完全",       level: "full" }
  - { row: 5, col: 1, value: "读写",       level: "rw"   }
  - { row: 5, col: 2, value: "SELECT",     level: "read" }
  - { row: 5, col: 3, value: "仅 SELECT", sub: "唯一消费出口", focal: true }
  # 行 6 — JupyterHub
  - { row: 6, col: 0, value: "管理",   level: "full" }
  - { row: 6, col: 1, value: "读写",   level: "rw"   }
  - { row: 6, col: 2, value: "读写",   level: "rw"   }
  - { row: 6, col: 3, value: "无访问", level: "none" }
  # 行 7 — NiFi
  - { row: 7, col: 0, value: "管理",   level: "full" }
  - { row: 7, col: 1, value: "读写",   level: "rw"   }
  - { row: 7, col: 2, value: "只读",   level: "read" }
  - { row: 7, col: 3, value: "无访问", level: "none" }

dark: false
```

### 10.1 这份 YAML 证明了什么

- `n_roles=4`、`n_components=8`、无颜色覆盖、一个焦点格。
- `viewBox_w = 12 + 208 + 12 + 4·148 + 3·16 + 48 = 920`。
- `row_y(k)` 产出 140, 180, 220, 260, 300, 340, 380, 420；`rows_bottom = 456`、`legend_y_top = 476`、`viewBox_h = 520`。
- `role_col_x(j) = [232, 396, 560, 724]`。
- 焦点格 `(row=5, col=3)` → rect `(724, 340, 148, 36)`、accent 描边 1.4。

同一 YAML 重新生成，产出与 shipped `example-dp-security-matrix.html` 视觉无异。
