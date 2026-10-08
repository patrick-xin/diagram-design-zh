# diagram-design-zh

为 coding agent 提供一套生成中文图表的规则与资源。你描述图表要表达的内容，技能会选择合适的类型，按中文排版规范生成可直接使用的成品。

默认使用白底和通用样式，输出独立 HTML；需要时也可导出 SVG 或 PNG。图表不依赖远程字体，适合保存、转发和离线打开。

## 能做什么

- **45 种图表类型**：覆盖系统结构、流程、计划、数据比较和数据平台等任务。
- **中文排版**：内置中文字体栈、字号下限、中英混排和标点规则；交付前将实际用到的字体子集内嵌到文件中。
- **统一样式**：按共享的颜色、几何、图例和可访问性规范生成图表；支持可选皮肤和品牌档案。
- **从已有图重绘**：读取 Mermaid 或 draw.io 的结构，再按本项目规则重排；不会把源图直接换皮当作成品。
- **按需增强**：可选图标、深色样式、终端外壳、分步动效、旁注和手绘效果，默认不启用。

## 图表类型

每种类型都有对应的规则文档和中文示例。

| 分组       | 类型                                                                                                                                                                                     |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 系统与流程 | 架构图、部署图、流程图、时序图、状态机、ER / 数据模型、数据库 schema、UML 类图、数据流、流程、泳道图、组织架构图、树形图、思维导图、依赖图、Wardley 地图、嵌套图、分层堆叠、鱼骨图、看板 |
| 计划与叙事 | 时间线、用户旅程、用户故事地图、甘特图、象限图、飞轮、金字塔 / 漏斗、维恩图                                                                                                              |
| 数据图表   | 柱状图、瀑布图、折线图、散点图、哑铃图、雷达图、极坐标图、桑基图、矩形树图、热力图、轴测平面图、爆炸轴测图                                                                               |
| 数据平台   | 数据栈全景图、奖章架构、IT 现状图、数据平台集成图、安全矩阵                                                                                                                              |

按任务需要，技能还会先选择语义模式，再确定图表类型；例如瓶颈分析、阶段框架、策略评估和治理清单。

## 安装

```bash
npx skills add https://github.com/patrick-xin/diagram-design-zh --skill diagram-design-zh
```

本仓采用 [Agent Skills 格式](https://agentskills.io/specification)。自动安装和自动发现取决于 agent 是否支持该格式；[`skills` 安装器](https://github.com/vercel-labs/skills#supported-agents)也只面向其支持的 agent。使用其他 agent 时，可按该产品支持的方式提供技能目录及其引用文件。

## 使用

安装后，用自然语言说明内容、受众和用途即可，例如：

- 「画一张电商系统的架构图，给不熟悉技术的管理者看。」
- 「比较这五条产品线今年和去年的收入变化。」
- 「把这段 Mermaid 时序图重绘成中文图表。」
- 「把这张架构图改成公众号封面尺寸。」

如果图表类型不明确，说明想表达什么、希望读者看出什么，agent 会给出合适的选项及读法差异。

### 导入与导出

Mermaid 和 draw.io 文件会先提取节点、关系、分组等结构，再依照本项目的规则重绘。每次导入都会说明合并、折叠或省略的内容，便于核对信息是否保留。

默认输出独立 HTML。需要图片或矢量文件时，可请求 PNG 或 SVG；导出流程和尺寸预设见 [`skills/diagram-design-zh/references/export.md`](skills/diagram-design-zh/references/export.md) 与 [`skills/diagram-design-zh/references/output-spec.md`](skills/diagram-design-zh/references/output-spec.md)。

### 皮肤与品牌

可使用内置皮肤，也可按项目配置品牌样式。皮肤适用于单张成品；品牌档案适用于一个项目中的后续图表。命令与配置流程见 [`skills/diagram-design-zh/references/onboarding.md`](skills/diagram-design-zh/references/onboarding.md) 和 [`skills/diagram-design-zh/references/profiles.md`](skills/diagram-design-zh/references/profiles.md)。

## 规则与示例

- [`skills/diagram-design-zh/SKILL.md`](skills/diagram-design-zh/SKILL.md)：入口、选型路由和通用工作规则。
- [`skills/diagram-design-zh/references/`](skills/diagram-design-zh/references/)：图表类型、排版、样式、导入和输出规则。
- [`skills/diagram-design-zh/assets/`](skills/diagram-design-zh/assets/)：各类型的 HTML 示例、模板和图标资源；示例可直接用浏览器打开。
- [`skills/diagram-design-zh/scripts/self_check.py`](skills/diagram-design-zh/scripts/self_check.py)：检查单个 HTML 成品是否符合文件、无障碍、颜色、中文排版、几何和动效规则。
- [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md)：字体、图标和商标相关说明。

提交或更新示例前，运行：

```bash
python3 skills/diagram-design-zh/scripts/self_check.py skills/diagram-design-zh/assets/example-你的类型.html
```

## 贡献

欢迎通过 issue 或 pull request 报告问题、提出改进。新增或修改示例时，请同时更新对应的类型规则，并先通过质量检查。

## 致谢

感谢 Cathryn Lavery 创建并以 MIT 许可发布 [`diagram-design`](https://github.com/cathrynlavery/diagram-design)。本项目沿用了其类型组织、布局与几何计算、按需载入等基础工作，并围绕中文排版、字体支持和质量检查进行了扩展。

## 许可

本项目采用 MIT 许可，详见 [`LICENSE`](LICENSE)。字体、图标等第三方内容遵循各自许可，具体说明见 [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md)。

## 友情链接

[LINUX DO](https://linux.do/) — 新的理想型社区 / A new ideal community
