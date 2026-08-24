# 样式指南（中文版唯一权威）

色板、字距、描边、间距的唯一事实来源，产出时色值以此为准。

排版层为中文优先：字体栈、字号下限、字距、混排规则全部按 CJK 设计。

---

## 字体栈

```css
:root {
  --font-sans:  'MiSans', 'Noto Sans SC', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', system-ui, sans-serif;
  --font-serif: 'Noto Serif SC', 'Songti SC', 'SimSun', serif;
  --font-mono:  'Sarasa Mono SC', 'Noto Sans SC', ui-monospace, 'SF Mono', Menlo, monospace;
}
```

```html
<!-- 不外链字体。默认系统三栈；跨机一致时按需内嵌子集（SKILL.md §7.1）：
     python3 <技能目录>/scripts/embed_fonts.py 产出.html -->
```

**默认字体选型**：

| 栈 | 首选 | 缺字体时 |
|---|---|---|
| serif（标题） | Noto Serif SC / 思源宋体 | 系统宋体兜底 |
| sans（节点/正文） | MiSans | Noto Sans SC / 苹方 / 雅黑 |
| mono（技术标签） | Sarasa Mono SC（2:1 中英等宽） | 退 sans 栈 |

三栈首选字体均可免费商用（思源两族 SIL OFL，随包再分发见 `fonts/OFL.txt`）。

- 思源两族已自托管（`fonts/` 内 GB2312 级 woff2 子集），**不外链 Google Fonts**——外链破坏单文件契约。字体由系统三栈渲染（**兜底项不许删**）；**每张产出交付前固定跑 embed_fonts.py 内嵌用字子集**（图是拿来分发的——无字库、断网机器也要像素级正确；SKILL.md §7.1）。
- MiSans / Sarasa Mono SC 不随包分发，属可选自托管升级（放 `fonts/` 目录用 `@font-face`），不是前提。
- mono 栈中的 CJK 兜底（Noto Sans SC）是有意的：中文出现在技术标签里时退回 sans，可读性优先。

## 排版角色表

| 角色 | 字体栈 | 字号 | 字重 | 字距 | 用途 |
|---|---|---|---|---|---|
| `title` | serif | 1.75rem | 400 | 0 | 页面 H1 |
| `node-name` | sans | 14px | 600 | 0 | 节点名（含汉字与混排） |
| `sublabel-tech` | mono | 9px | 400 | 0.04em | 纯拉丁技术串：协议、端口、URL |
| `sublabel-zh` | sans | 12px | 400 | 0 | 中文子标签 |
| `eyebrow-latin` | mono | 7–8px | 500 | 0.18em + uppercase | 拉丁角标（PROD、API） |
| `eyebrow-zh` | sans | 12px | 500 | 0.3em | 中文角标（生产环境、核心区） |
| `arrow-label-latin` | mono | 8px | 400 | 0.06em | 拉丁箭头标签 |
| `arrow-label-zh` | sans | 12px | 500 | 0.12em | 中文箭头标签 |
| `callout` | serif italic | 16px | 400 | 0 | 编辑旁注（少用） |
| `legend` | sans | 10px | 400 | 0 | 图例项文字 |
| `legend-label` | mono | 10px | 400 | 0.1em | 图例标签（「图例」、图例行类目） |

**含汉字 → 用 zh 行；纯 ASCII → 用 latin 行。** `letter-spacing` 的原理：0.18em 是给大写拉丁字母的视觉节奏；汉字方块字形自带密度，要么 0（正文），要么放大到 0.3em 制造疏朗的"角标感"，中间值最丑。

## 字号下限（硬规则）

- **含汉字的文本 ≥10px**（self_check 强制的违法下限）。9px 汉字笔画糊，8.5px 更不行。10px 不是设计默认——默认按上面角色表（节点名 14px、中文小字 12px 起），只有空间极限才压到 10–11px。
- 9px 只允许纯拉丁技术串。
- 标题下限 1.5rem；节点名下限 12px、默认 14px。

## 图例条（底部横条）

- 标签「图例」：`legend-label` 角色，与图例项**同一基线**；标签 → 首个元素 72px。
- 图例项：`legend` 角色；色块 16×12（块底 = 基线 +2，即 y = 基线−10）；块 → 文字 8px；线样长 28、y = 基线−4，带对应箭头 marker。样块填充与线宽**与图内实物一致**（复刻芯片按芯片实际尺寸）。
- 顶部分隔线：`rule @0.10`、宽 0.8，位于基线上方 18px。
- **整条锚位**：图例分隔线距图内最下内容元素的底 **56 单位**（±4 容差）——量内容底，不量轴线 / 网格（见「容器对齐与画布基线」）。
- 多行图例：行距 30，行类目标签用 `legend-label` 角色，行内首元素同一列对齐。

## 容器对齐与画布基线

**container 四件套**——标题与图表同线，画图零对齐计算：

1. `.frame { max-width: 1200px; width: 100%; padding-left: 4% }`——容器统一缩进 = 标题线；
2. `svg { width: 100% }`——画布铺满容器内容区，左缘即标题线；
3. **SVG 内容 x=0 起排**——eyebrow / h1 不写任何 margin-left，三层一线（标题、图内容、图例区）由容器保证；
4. `svg { overflow: visible }`——描边贴边不被裁。

**画布基线**：

- **宽 = 1000 定死**：全家族渲染字号一致性的锚点（viewBox 宽不同则同字号渲染大小不同）。
- **内容四贴**：x 左贴 0、y 顶贴 0（顶部留白归 HTML margin 管）。绘图区按类型对齐家族惯例：bar 系 80..960；散点左三列式（竖排轴题贴 x=0 → 刻度数字右对齐 → 轴线）；无轴图型（矩形树图等）格区直接铺满 0→1000。
- **高 = 内容底向上取整到 40 的倍数**，行 / 区块节奏 40。
- **宽高比护栏 1.5 ~ 2.2**：落出区间不是画布问题，是图该拆或该换类型。
- **内容多寡由间距消化**：加宽 / 收窄只动列距与 gap，节点尺寸与字号永不缩放；坐标一律 4 的倍数。
- **图例横线贯通 0→1000**：图例线 = 图块边界，绘图区右缘按图型家族惯例。

**标准页内间距**：

- h1 → 图表 **3rem**；带可见副题时沿用 full 同款（h1 → 副题 1.5rem、副题 → 图 4rem），不另立档。
- **图表 → 图例横条 = 图内最下内容元素的底 + 56**：分区图量分区底，带轴图表量轴下刻度标签底——轴线与发丝网格是 chrome 不算内容；画布底部余量可收到 ~10 单位。
- 图例口径注右锚 x=1000（`text-anchor="end"`）。

**full 页面级版式**（三层结构 = 标题组 → 图表 → 卡片区 → 页脚；画布紧、页面松，允许滚动不强制一屏）：

- 层间：副题 → 图表 4rem；图表 → 卡片区 2rem；卡区 → 页脚 1rem + padding-top 1.5rem。组内：h1 → 副题 1.5rem；卡内 padding 1.25rem、卡距 1rem；页面四周 3rem / 2rem。
- 无图框：`.diagram-container { overflow-x: auto; padding: 2px 0; }`——**padding 2px 必须有**：overflow-x:auto 会把容器变纵向裁剪上下文，吃掉 svg overflow:visible 的贴边描边。
- 卡片三张写图内真实数据 + 绘制要点——**卡片是对 agent 的重复强调**：full 是带讲解的完整页，焦点 / 读法 / 口径三卡把这张图的绘制决策在成品里再讲一遍，与 type 文档同一套话。
- footer 图题 + 年月；`:root` 九角色 token。

**竖排轴标题基线补偿要连带整片右移**：rotate(-90) 标题基线 x = 容器线 + 字号，同时标签列 / 轴线 / 数据区同步右移同量——只补标题会把间距吃掉。

**内容居中型布局**（主干居中的流程图、环形图）：内容几何保持居中，容器线只约束标题与图例区。

## 混排与标点

- 汉字与拉丁/数字之间加空格：`对话 Agent`、`5 分钟`、`Q3 路线图`、`Redis 缓存`。
- 并列用间隔号 `·`（技术串内半角两侧空格，中文语境两侧不留空格亦可，全图统一）。
- 中文语句标点全角；技术串内部半角。行首不出标点。
- `text-transform: uppercase` 只写在使用拉丁 eyebrow 的元素上。

## 色板（语义角色）

| 角色 | 用途 | 默认值（浅色） | 深色档 |
|---|---|---|---|
| `paper` | 页面背景、节点底 | `#ffffff` | `#0a0d1b` |
| `paper-2` | 容器底（少用）；深色下与纸面同色 | `#f3f2ff` | `#0a0d1b` |
| `ink` | 主文本、主描边 | `#29314f` | `#e0e4ff` |
| `muted` | 次文本、默认箭头 | `#565e7e` | `#a2a9ce` |
| `soft` | 子标签、边界标签 | `#8f94ab` | `#787fa2` |
| `rule` | 发丝线 | `rgba(41,49,79,0.10)` | `rgba(224,228,255,0.12)` |
| `accent` | 焦点，≤2 处 | `#1a4dd9` | `#7d98ff` |
| `accent-tint` | 焦点底色 | `rgba(26,77,217,0.08)` | `rgba(125,152,255,0.10)` |
| `link` | HTTP/API 调用、对外消费线 | `#217e7b`（青） | `#55b8b4` |

### 深色换档规则（浅 → 深）

浅色 **ink 基**的 `rgba(41,49,79, X)` → 深色 `rgba(224,228,255, X)`，**α 不动**；`muted` / `soft` / `accent` 换上表深色档值；深色纸面 `#0a0d1b`，backend 节点填充与纸面同色（描边成型，不再用 paper-2 垫底）；箭头标签遮罩、掩膜 rect 跟随纸面换档；焦点 tint 提一档（0.08 → 0.10）。深色档锚点：[`assets/example-architecture-dark.html`](../assets/example-architecture-dark.html) 等四张 `-dark` 资产（architecture / bar / data-flow / dp-integration）。

**深色是 opt-in 变体**：用户点名深色 / 暗色 / 夜间模式，或投放目标本身是深色站点 / 深色幻灯时启用，模板用 [`assets/template-dark.html`](../assets/template-dark.html)。默认仍是浅色。对比度约束（ink 对 paper 达 WCAG AA）两档同守。

### 系列色板（多系列图表专用）

取国内图表工具（ECharts / Excel / 商业 BI）读者最熟悉的色相——翠绿、暖橙、绛红、靛蓝、紫棠，饱和度压到与纯白纸面、ink 文字协调的中等档：一眼认得出「是什么颜色」，又不抢焦点的 accent。只给真正需要区分多个重叠实体的图表类型用（折线 / 雷达 / 分组柱状）。1-焦点规则仍然生效——`accent` 留给焦点系列，下表只覆盖其余系列，按序取用不跳档。

| Token | 浅色 | 深色 | 备注 |
|---|---|---|---|
| `series-1` | `#3ba272`（翠绿） | `#5fbf93` | 非焦点系列 |
| `series-2` | `#ed7d31`（暖橙） | `#f2a267` | 非焦点系列 |
| `series-3` | `#d9605b`（绛红） | `#e78c88` | 非焦点系列 |
| `series-4` | `#5470c6`（靛蓝） | `#8498dc` | 与 accent 同为蓝系；用作第 4 档时靠焦点自身的粗线 + 圆点 + 面积区分 |
| `series-5` | `#9a6fb8`（紫棠） | `#b795cf` | 非焦点系列 |

系列多边形 / 面积的填充用 0.18（浅）/ 0.22（深）透明度；折线描边用全色。**不许回填到非图表类型**——架构图、泳道图等继续用 ink / muted 变体。**唯一例外：分类芯片编码**——data-flow / process 的载荷芯片（WB/DB/TB/FL/LS）与系列色同职能（图例为准的分类编码），映射见 [type-data-flow.md](type-data-flow.md) §8，两类型共用。系列色板是「重叠形状确实需要可区分颜色」时的 opt-in，不是到处加色的许可证。

### 语义色族（领域角色专用）

跨类型**恒定语义**的五个实色，浅深两档、色相恒定。与系列色板的分工：系列色编码「分类」——映射任意、图例为准、跨皮肤写死；语义色编码「含义」——铁锈红在任何图里都读作安全。用于 dp-integration / it-state / data-flow 告警 / medallion staging 这类带领域角色的元素；普通装饰填充轮不到它们（那是 token / α 梯子的事）。

| Token | 浅色 | 深色档 | 语义 | 典型位置 |
|---|---|---|---|---|
| `sem-security` | `#b85450`（铁锈红） | `#bf6561` | 安全 / 身份 / 权限 / 审计 | dp 矩阵安全行、data-flow 告警芯片、统一身份底栏 |
| `sem-observability` | `#5a7d9a`（岩蓝） | `#5e83a1` | 可观测 / 质量 / 监控 | 集中日志、校验层、监控闸 |
| `sem-governance` | `#7a8c47`（橄榄绿） | `#7a8c47` | 治理 / 血缘 / 发布 | 治理条、血缘图、数据产品层 |
| `sem-backup` | `#8c6d3f`（暖棕） | `#9b7946` | 备份 / 归档 / 冷存 | 备份通道、冷层 |
| `sem-workspace` | `#c9a23a`（金） | `#c9a23a` | 分析 / 工作区 / 沙盒 | medallion staging 层 |

α 派生与 token 同规则（填充 @0.06、描边 @0.45，深色档 α 不动）。**语义色不吃换肤**——皮肤表换气质（token / α），语义五色与系列五色跨皮肤恒定；这是「语义化」的底线：换皮不换义。

### α 梯子标准档（透明度闭集）

token / 系列色 / 语义色的一切透明度派生**只取以下档位**——这是换肤值替换闭集的组成部分（reskin 映射整档搬移，不出现表外透明度）：

| 档 | 角色 |
|---|---|
| `@0.02` | 道底 / optional 填充 / 嵌套最外层底 |
| `@0.03` | external 填充 / 嵌套第二层底 / 角色行容器 |
| `@0.05` | store 填充 / security(accent) 填充 / 外部源卡 / backend 编号水印 |
| `@0.06` | 语义族填充（sem-* 专用） |
| `@0.08` | accent-tint / input 填充 / 装饰水印 |
| `@0.10` | 分区发丝 / 点阵 / 深色 tint |
| `@0.12` | 角色 / 步骤芯片 / pressed / 焦点头带 |
| `@0.15` | 柱体 / 甘特条体（muted） |
| `@0.18` | 系列面积 / 层头带 / 告警芯片 |
| `@0.20` | optional 描边（虚线）/ 分隔线 / 散点点阵（muted）/ **焦点步骤芯片**（accent 基，字用 accent 实色——深档 5.9:1） |
| `@0.30` | external 描边 / **图表轴线与网格** |
| `@0.40` | backend 描边 / 嵌套第二层描边 |
| `@0.45` | 语义族描边（sem-* 专用） |
| `@0.50` | security 描边 / 今日线 / 嵌套最内层描边 |
| `@0.60` | store 描边 |

**枚举闭合的图表特例**：treemap 深度坡道 = ink@`{0.04, 0.07, 0.09, 0.11, 0.13, 0.16}` 六档整组使用（值编码面积深度，不许单抽一档）；深色三级文字 = 纸色基 `@0.72`。深色档各基色沿用同一套档位，按深色换档规则换基。

**禁令**：不许发明表外透明度；不许为「再轻一点 / 再重一点」在相邻档间微调——要么换档，要么换角色。

### 终端皮肤（opt-in 第二皮肤）

终端窗口外壳的九 token 固定色板（见 [primitive-terminal.md](primitive-terminal.md)）。它**不**参与上面的浅/深反转，也**不**吃 onboarding 品牌化——每张终端图都用同一套：

| Token | 值 | 用途 |
|---|---|---|
| `terminal-page` | `#0a0a0a` | 窗外页面底 |
| `terminal-paper` | `#141414` | 窗体、节点底 |
| `terminal-bar` | `#1b1b1b` | 标题栏条 |
| `terminal-border` | `#2b2b2b` | 窗框、发丝线 |
| `terminal-ink` | `#faf8ff` | 主文本、主描边（与浅色 ink 同一白） |
| `terminal-muted` | `#9a9a9a` | 次文本、子标签、环描边 |
| `terminal-soft` | `#5c5c5c` | 三级——非活动圆点、辐条 |
| `terminal-accent` | `#7d98ff` | 唯一 accent——焦点站、提示符、活动圆点（焦点蓝深色档，黑底对比 6.8:1） |
| `terminal-accent-tint` | `rgba(125,152,255,0.12)` | accent 边框盒的填充 |

**1-accent 规则同样生效**：除 `terminal-ink` / `terminal-muted` / `terminal-soft` 之外的一切都应是 `terminal-accent`——绝不引入第二色相。

**可选皮肤「新中式」**（宣纸 / 玄墨 / 朱砂 / 黛蓝 + 钤印 / 题签 / 朱批）：见 [skin-xinzhongshi.md](skin-xinzhongshi.md)。token 整体替换，排版纪律不变。新中式只有浅色档——深色换档规则只适用于默认皮肤。

## 描边 / 圆角 / 间距

| Token | 值 | 用途 |
|---|---|---|
| `stroke-thin` | 0.8 | 角标框、叶子节点 |
| `stroke-default` | 1 | 大多数描边 |
| `stroke-strong` | 1.2 | 强调描边 |
| `radius-sm` | 4 | 小角标 |
| `radius-md` | 6 | 节点盒 |
| `radius-lg` | 8 | 容器、分区、肘线圆角 |
| `grid` | 4 | 所有坐标、尺寸、间距可被 4 整除（硬规则） |

## 节点类型 → 视觉处理

| 类型 | 填充 | 描边 |
|---|---|---|
| `focal`（≤2） | `accent-tint` | `accent` |
| `backend` | `#ffffff` | `ink @ 0.40` |
| `store` | `ink @ 0.05` | `muted @ 0.60` |
| `external` | `ink @ 0.03` | `ink @ 0.30` |
| `input` | `muted @ 0.08` | `soft` |
| `optional` | `ink @ 0.02` | `ink @ 0.20` 虚线 `4,3` |
| `security` | `accent @ 0.05` | `accent @ 0.50` 虚线 `4,4` |

## 自定义皮肤约束（不可破坏）

1. **对比度**：`ink` 对 `paper` 须达 WCAG AA；`muted` 对 `paper` 在 11px+ 文本上须达 AA。
2. **一个 accent**：换肤时 accent 只有一个。
3. **无彩虹**：品牌给 8 色也只取 paper / ink / accent 三色，其余降为 muted 变体。
4. **三栈纪律**：换字体只能换栈内的字体名（如 MiSans → HarmonyOS Sans），不能破坏 serif/sans/mono 三栈结构，不能删系统兜底。
5. **纸面纯白、容器靠描边**：页面背景 `#ffffff`；backend 节点同为 `#ffffff`，靠 `ink @ 0.40` 描边成型（store `muted @ 0.60`）——层级来自描边深浅与梯子填充，不靠底色对比。分区不上底色：遮罩才能统一纸色；若某皮肤给容器上底色，遮罩色必须跟垫底色。
6. **点状纹理可选非默认**：22×22 点阵（ink @ 10%）是 opt-in，默认无纹理。
