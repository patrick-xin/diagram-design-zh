# tonex 主题接入（单种子零 flag 路线）

> 状态（2026-08-18）：映射表已定稿并机器验证（12/12 角色对过 AA 门 + 浏览器逐位对账）。
> **技能接线 park 中**：SKILL.md 路由行与 style-guide.md「色板来源分流」注记都还没做，节点级角色未拍板（见 §8）——
> 接线完成前，本文档是唯一事实源，不与其他文档的色值混用。

## 1. 适用条件与命令

- **触发**：用户给出一个品牌/种子色（hex），要求整套配色随种子生成。
- **命令**（零 flag；cmf 是默认 variant，无需写）：

  ```
  tonex generate --seed '<hex>' --format hex
  ```

- 输出 JSON 含 `light` / `dark` 两套 scheme，**两套都要用**——深色档不是可选项，是同一条命令的另一半。
- 不用 `--second-color`、不用 `--contrast`、不用 `adjust/shift`。一切角色值从这条命令直出，或按 §3 的两条 α 派生式计算，没有第三种来源。

## 2. 角色 ↔ token 映射表（核心契约，不许改）

左列是本技能的语义角色名，与 style-guide.md 及各 type-*.md 使用的角色名一致——换主题只换值，不换名。

| 技能角色 | 来源（两模式各自取） | 说明 |
|---|---|---|
| `paper` | `surface` | CLI 主题不出现纯白；纯白纸只属于无 CLI 的默认模板 |
| `ink`（正文） | `on-surface` | 箭头、轴线同源（结构线跟正文同色） |
| `muted`（二级文字） | `on-surface-variant` | |
| `soft`（三级文字） | `on-surface @ 0.72` | 全表唯一 α 派生文字位，见 §3 |
| `accent`（主色/焦点） | `primary` | 文字位与焦点描边都用本档 |
| `accent-tint`（焦点容器底） | `primary @ 8%（浅）/ 10%（深）` | 焦点格 = 染色底 + primary 描边，双标记 |
| `rule`（容器描边/发丝线） | `outline-variant` | |
| 容器梯（三档） | `surface-container-low` / `surface-container` / `surface-container-high` | 三档制；lowest（白上白）与 highest（贴线聚集地）已砍，不复活 |
| 按钮激活文字 | `on-primary` | |

## 3. α 派生规则（全表仅两处）

- `soft` = `rgba(<on-surface 的 RGB>, 0.72)`——**0.72 是定死常数，两模式同 α**；深色档用深色 on-surface 的 RGB 配同一个 0.72（换 RGB 不换 α）。
- `accent-tint` = `rgba(<primary 的 RGB>, 0.08 浅 / 0.10 深)`（accent-tint 惯例档）。
- 常数的来历：四种极性/彩度不同的种子验证过，α 窗口逐位相同（scheme 把 on-surface 与 on-surface-variant 的明度关系钉死，属结构性而非运气）；0.72 取自「全背景过 AA ∧ 淡于二级」交集。
- **不可稀释**：primary/tertiary 当文字没有稀释空间（AA 下界 α ≥ 0.96）；on-surface 是唯一有真实稀释余量的 token。fill 位不受此限（non-text 角色）。

## 4. 铁律

1. **文字主色只用 primary/tertiary 本档**；`*-container` 永不当文字——它当文字是抽奖（实测：浅色档蓝 6.8 过 / 红 4.50 压线 / 绿 2.3 挂，深色档大多挂）。
2. **on-\* 只配自家的 X-container 用**：`on-secondary-container` 之类的落 surface 是越界使用，即使对比度碰巧过也不许。
3. **container ≈ 种子不是契约**：存在边界情况（实测 #ff5000 → primary-container #ff5d22），任何规则不许建立在「container 等于种子」上。
4. **CLI 主题一切颜色以 CLI 输出为准、含纸面**；纯白纸出现在 CLI 主题里是 bug。
5. **容器三档制**（low / container / high）。
6. **AA 由 scheme 自带保证**，§6 的门复核；agent 不自调任何值来「修」对比度。

## 5. 已知边界与代价（定版时接受，不是待修 bug）

- 深色 `container`/`high` 档上二级/三级微融合（反转 ≤ 0.4 个比）：那是 on-surface-variant 自身塌陷的压缩区，非 α 之过。
- 中性种子（白/黑/灰系）浅色二/三级近同值：层级靠排版（字距 0.3em / 500 字重）——这是四个保证 token 内的结构上限。
- `outline` 恒在 4.0–4.3：它是 non-text 角色（3:1 车道），只作边框，永远不上文字位。

## 6. 校验门（换算完成后必须跑，exit 0 才继续画图）

```
tonex check --seed '<hex>' --pairs '[
  ["on-surface","surface"],["on-surface-variant","surface"],["primary","surface"],
  ["on-surface","surface-container-low"],["on-surface-variant","surface-container-low"],["primary","surface-container-low"],
  ["on-surface","surface-container"],["on-surface-variant","surface-container"],["primary","surface-container"],
  ["on-surface","surface-container-high"],["on-surface-variant","surface-container-high"],["primary","surface-container-high"]]'
```

12 对 = 3 个直出文字角色 × 4 档背景，自动覆盖明暗两档。α 派生两项（0.72 / 8%）是定值，不需跑门。

## 7. 完整走例（种子 = 默认 accent #1a4dd9）

```
tonex generate --seed '#1a4dd9' --format hex
```

换算结果（照抄可复核）：

| 角色 | 浅色 | 深色 |
|---|---|---|
| `paper` | `#faf8ff` | `#0a0d1b` |
| `ink` | `#2a314f` · 12.1:1 | `#e0e4ff` · 15.4:1 |
| `muted` | `#565e7e` · 6.04 | `#a2a9ce` · 8.38 |
| `soft` | `rgba(42,49,79,0.72)` · 纸面 5.15 / high 档 4.76 | `rgba(224,228,255,0.72)` · 纸面 8.22 / high 档 7.40 |
| `accent` | `#0040ca` · 7.71 | `#7d98ff` · 7.19 |
| `accent-tint` | `rgba(0,64,202,0.08)` | `rgba(125,152,255,0.10)` |
| `rule` | `#a9b0d5` | `#3f4665` |
| 容器 low / container / high | `#f3f2ff` / `#ebedff` / `#e4e7ff` | `#0d1225` / `#13182e` / `#181e37` |
| 按钮激活文字 | `#d7ddff` | `#00185c` |

## 8. 未覆盖角色（park——v1 明确不管，沿用 style-guide 现行规则）

- **节点级填充梯**：store@5% / external@3% / optional@2%（默认皮肤的 ink 基透明度）→ 待逐角色拍板。现成原则：ink 基 → `on-surface @ 同 α`，深色自动翻转；未走验证门。
- **描边角色**：backend `ink@0.40`、store `muted@0.60` → 挂 on-surface 还是 outline-variant，待拍。
- **input 填充** `muted@8%`、**security** `primary@5% + 虚线`（方向已定，未走门）。
- **link**（HTTP/API 箭头）、**rule-solid**、**series-1..5**（图表系列色，tonex 无对应，需种子派生方案）。
- **双种子路线**（`--second-color` → accent 挂 tertiary）：已验证存在，但不在零 flag 契约内，另行定档。
- **深色档导出/交付流程**。
- **技能接线**：SKILL.md 路由一行 + style-guide.md 顶部「色板来源分流」注记——等节点级全部定了再做（2026-08-18 用户指示：全部搞定后再写 skill）。
