# diagram-design-zh：agent 零指令产出中文图表的技能

> 本项目 fork 自 [Cathryn Lavery](https://github.com/cathrynlavery) 的 [diagram-design](https://github.com/cathrynlavery/diagram-design)（MIT）。设计系统的品味来自原项目，本仓库负责中文排版层重写与本土化。

## 项目简介

对 agent 说一句「帮我画一张微服务架构图」，得到一张**单文件、断网可开、字号按中文惯例**的 standalone HTML 图表——中文字体、字号、字距、中英混排规则全部内置，不用再教 agent「换个中文字体」「字太小」「间距不对」。

适合谁：

- 用 Claude Code / ZCode 等编码 agent 干活的开发者，经常要画架构图、时序图、数据流
- 要把图贴进周报、汇报文档、公众号文章的工程师和写作者
- 有品牌色要求的乙方 / 多客户团队（品牌档案，多客户互不串色）

## 安装

方法一：克隆到技能目录（推荐，用户级全局可用）

```bash
git clone https://github.com/patrick-xin/diagram-design-zh ~/.claude/skills/diagram-design-zh
```

方法二：项目级（随仓库走，不污染其他项目）

```bash
git clone https://github.com/patrick-xin/diagram-design-zh <你的项目>/.claude/skills/diagram-design-zh
```

验证安装：对 agent 说「帮我画一张微服务架构图」；或直接用浏览器打开 `assets/example-architecture.html` 看锚点示例。

## 使用

### 基础用法

装完直接说人话：

- 「画一张电商系统的架构图」
- 「把这段时序画出来：用户 → 网关 → 订单服务 → 库存」
- 「把这个 Mermaid 文件重画成设计稿」——Mermaid / draw.io 文件导入后按设计系统**重绘**（不是渲染），附保真台账
- 「出一张公众号封面尺寸的飞轮图」——平台预设：公众号封面 900×380（@2 出 1800×760）、小红书 3:4 1080×1440，按尺寸重画不是缩放

### 效果预览

35 个中文锚点示例在 `assets/`，浏览器打开即看。产出是零依赖单文件 HTML——直接发人、贴文档、断网打开像素一致。

## 核心能力

- **28 种图表类型**：架构 / 流程 / 数据流 / 时序 / 状态机 / ER / 泳道 / 甘特 / 柱状 / 折线 / 散点 / 雷达 / 树 / 组织图 / 嵌套 / 分层 / 象限 / 飞轮 / 金字塔 / 矩形树图 / 韦恩 / 高层架构 / 徽章 / IT 现状 / 数据产品集成 / 安全矩阵 / 时间线 / 循环
- **中文排版内置**：思源三字体栈（宋体标题 / 黑体节点 / Sarasa 等宽标签）；成稿自动内嵌字体子集，零外链、断网可开；含汉字 ≥10px 硬线；中英混排空格与全角标点
- **换肤**：默认靛蓝 / 新中式（宣纸 · 玄墨 · 朱砂，钤印焦点 + 竖排题签）/ 中国红（政务）/ tonex 种子派生——`scripts/reskin.py` 一键换装
- **导入重绘**：Mermaid 源与 draw.io 文件 → 结构摘要 → 按设计系统重绘
- **语义模式 ×7 先行路由**：排队瓶颈 / 阶段框架 / 结构化产物 / 策略评估 / 安全铺路 / 治理清单 / 补偿分层
- **输出**：standalone HTML（默认）/ PNG @1/@2 / SVG / 透明底
- **质量门**：`scripts/self_check.py` 随包分发——单文件契约、无障碍、动效、中文排版、几何网格五层自检
- **可选增强层**（默认全不启用）：无障碍分步动效 · 103 枚单色图标（含国内品牌 16 枚）· 深色档 · 终端皮肤 · 编辑旁注 · 手绘滤镜

## 文件说明

- `SKILL.md` — 技能入口与调度
- `references/` — 全部规则文档（style-guide.md 是颜色唯一权威）
- `assets/` — 35 个中文锚点示例 + 3 个模板（深色 / 终端 / 动效）+ 图标页
- `scripts/` — self_check / embed_fonts / reskin 与导入提取器
- `fonts/` — 内嵌字体母本（思源 GB2312 子集，OFL）

## 贡献

欢迎 issue / PR。中文字体子集、CJK 排版边界、国内平台预设这类本土化问题优先。

## 许可

MIT（沿用原项目）。图标与字体的第三方许可汇总见 [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)。
