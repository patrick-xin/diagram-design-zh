# diagram-design-zh

[![License: MIT](https://img.shields.io/badge/License-MIT-1a4dd9.svg)](LICENSE)
[![Format: Agent Skills](https://img.shields.io/badge/Format-Agent_Skills-565e7e.svg)](https://agentskills.io/specification)
[![types](https://img.shields.io/badge/types-45-217e7b.svg)](#图表类型)
[![output: single-file HTML](https://img.shields.io/badge/output-single--file_HTML_·_offline-29314f.svg)](#导入与导出)
[![GitHub stars](https://img.shields.io/github/stars/patrick-xin/diagram-design-zh.svg)](https://github.com/patrick-xin/diagram-design-zh/stargazers)

> 本项目是从 [diagram-design](https://github.com/cathrynlavery/diagram-design) fork 来的（感谢原作者 Cathryn Lavery ），按中文排版重做了整套规则。想画英文图表，直接用原项目就行。

**为 coding agent 提供一套生成中文图表的规则与资源。你描述图表要表达的内容，技能会选择合适的类型，按中文排版规范生成可直接使用的成品。**

默认使用白底和通用样式，输出独立 HTML；需要时也可导出 SVG 或 PNG。图表不依赖远程字体，适合保存、转发和离线打开。

## 能做什么

- **45 种图表类型**：覆盖系统结构、流程、计划、数据比较和数据平台等任务。
- **中文排版**：内置中文字体栈、字号下限、中英混排和标点规则；生成时会把实际用到的字体子集内嵌进文件。
- **统一样式**：按共享的颜色、几何、图例和可访问性规范生成图表；支持可选皮肤和品牌档案。
- **从已有图重绘**：读取 Mermaid 或 draw.io 的结构，再按本项目规则重排；不会把源图直接换皮当作成品。
- **按需增强**：可选图标、深色样式、终端外壳、分步动效、旁注和手绘效果，默认不启用。

## 画廊

45 种类型各一张成品示例，点图进入[在线画廊](https://patrick-xin.github.io/diagram-design-zh/)的对应位置——那里可以切换浅色 / 深色 / 讲解三档、按名称搜索，另有变体与动效示例。此处为浅色标准档静态导出。

<table>
  <tr>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#architecture"><img src="screenshots/architecture.png" alt="AI 客服平台 · 生产架构" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#data-flow"><img src="screenshots/data-flow.png" alt="数据平台 · 谁在哪个阶段碰数据" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#db-schema"><img src="screenshots/db-schema.png" alt="电商数据库 · 订单子系统" width="420"></a></td>
  </tr>
  <tr>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#dependency"><img src="screenshots/dependency.png" alt="TypeScript 单仓 · 依赖结构" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#deployment"><img src="screenshots/deployment.png" alt="结算服务 · 生产部署" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#er"><img src="screenshots/er.png" alt="内容平台 · 数据模型" width="420"></a></td>
  </tr>
  <tr>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#fishbone"><img src="screenshots/fishbone.png" alt="查询 p99 延迟事故 · 根因分析" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#flowchart"><img src="screenshots/flowchart.png" alt="线上告警怎么处置？" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#kanban"><img src="screenshots/kanban.png" alt="数据平台迭代看板 · 2026 W36" width="420"></a></td>
  </tr>
  <tr>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#layers"><img src="screenshots/layers.png" alt="AI 应用技术栈 · 差异化到底发生在哪一层" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#mindmap"><img src="screenshots/mindmap.png" alt="短视频账号运营" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#nested"><img src="screenshots/nested.png" alt="数据访问边界" width="420"></a></td>
  </tr>
  <tr>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#org-chart"><img src="screenshots/org-chart.png" alt="研发部责任图 · 谁拥有什么" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#process"><img src="screenshots/process.png" alt="季度入户调查 · 从问卷设计到公开发布" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#sequence"><img src="screenshots/sequence.png" alt="扫码点单链路 · 从提单到取餐码" width="420"></a></td>
  </tr>
  <tr>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#state"><img src="screenshots/state.png" alt="文章生命周期 · 从草稿到归档" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#swimlane"><img src="screenshots/swimlane.png" alt="采购审批流 · 谁在什么时候接手" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#tree"><img src="screenshots/tree.png" alt="订单系统模块分解" width="420"></a></td>
  </tr>
  <tr>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#uml-class"><img src="screenshots/uml-class.png" alt="支付域 · 类图" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#wardley"><img src="screenshots/wardley.png" alt="AI 助手产品 · Wardley 地图" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#gantt"><img src="screenshots/gantt.png" alt="App 2.0 重构 · 十二周排期" width="420"></a></td>
  </tr>
  <tr>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#journey"><img src="screenshots/journey.png" alt="协作工具试用转付费 · 第一周" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#loop"><img src="screenshots/loop.png" alt="开发者工具的增长飞轮" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#pyramid"><img src="screenshots/pyramid.png" alt="用户参与金字塔 · 少数人创造多数价值" width="420"></a></td>
  </tr>
  <tr>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#quadrant"><img src="screenshots/quadrant.png" alt="团队 AI 自动化机会 · 2026 H2" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#story-map"><img src="screenshots/story-map.png" alt="报表工具 · 首个发布" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#timeline"><img src="screenshots/timeline.png" alt="App 2.0 · 2025–2026 五个关键节点" width="420"></a></td>
  </tr>
  <tr>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#venn"><img src="screenshots/venn.png" alt="数据团队成员画像" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#axonometric-plan"><img src="screenshots/axonometric-plan.png" alt="三层办公区：团队真正落座的地方" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#bar"><img src="screenshots/bar.png" alt="2026 H1 各渠道新增用户" width="420"></a></td>
  </tr>
  <tr>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#dumbbell"><img src="screenshots/dumbbell.png" alt="改版后，哪些自助流程更容易一次完成？" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#exploded"><img src="screenshots/exploded.png" alt="应用三层结构：一个产品的拆解" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#heatmap"><img src="screenshots/heatmap.png" alt="支付在迭代 4 出的事故" width="420"></a></td>
  </tr>
  <tr>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#line"><img src="screenshots/line.png" alt="近 12 周活跃用户趋势" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#polar"><img src="screenshots/polar.png" alt="在线课堂并发负载 · 分时段" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#radar"><img src="screenshots/radar.png" alt="存储方案选型评估" width="420"></a></td>
  </tr>
  <tr>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#sankey"><img src="screenshots/sankey.png" alt="流水线算力 · 一个月的构建分钟" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#scatter"><img src="screenshots/scatter.png" alt="广告计划：展示量 × 转化率" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#treemap"><img src="screenshots/treemap.png" alt="对象存储占用分布" width="420"></a></td>
  </tr>
  <tr>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#waterfall"><img src="screenshots/waterfall.png" alt="云成本预算桥 · 2025 → 2026" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#dp-integration"><img src="screenshots/dp-integration.png" alt="数据平台集成拓扑" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#dp-security-matrix"><img src="screenshots/dp-security-matrix.png" alt="平台访问矩阵" width="420"></a></td>
  </tr>
  <tr>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#high-level"><img src="screenshots/high-level.png" alt="K8s 数据栈全景" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#it-state"><img src="screenshots/it-state.png" alt="现行 IT 版图 · 数据平台建成之前" width="420"></a></td>
    <td><a href="https://patrick-xin.github.io/diagram-design-zh/#medallion"><img src="screenshots/medallion.png" alt="五层奖章架构 · 季度调研数据" width="420"></a></td>
  </tr>
</table>

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

## 仓库结构

- [`skills/diagram-design-zh/SKILL.md`](skills/diagram-design-zh/SKILL.md)：入口、选型路由和通用工作规则。
- [`skills/diagram-design-zh/references/`](skills/diagram-design-zh/references/)：图表类型、排版、样式、导入和输出规则。
- [`skills/diagram-design-zh/assets/`](skills/diagram-design-zh/assets/)：各类型的 HTML 示例、模板和图标资源；示例可直接用浏览器打开。
- [`skills/diagram-design-zh/scripts/`](skills/diagram-design-zh/scripts/)：自检（`self_check.py` 检查单个 HTML 成品的文件、无障碍、颜色、中文排版、几何与动效六层）、字体子集内嵌与换肤脚本。
- [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md)：字体、图标和商标相关说明。

## 贡献

欢迎通过 issue 或 pull request 报告问题、提出改进。新增或修改示例时，请同步更新对应的类型规则，并运行质量门确认通过：

```bash
python3 skills/diagram-design-zh/scripts/self_check.py skills/diagram-design-zh/assets/example-你的类型.html
```

## 许可

本项目采用 MIT 许可，详见 [`LICENSE`](LICENSE)。字体、图标等第三方内容遵循各自许可，具体说明见 [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md)。

## 友情链接

[LINUX DO](https://linux.do/) — 新的理想型社区 / A new ideal community
