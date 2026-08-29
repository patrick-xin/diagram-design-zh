# 实体关系 / 数据模型（ER）

**最适合**：数据库 schema、API 资源关系、领域模型。

**分工判据**：ER 是**概念层**——实体盒 + 基数 + 平铺字段，谈「实体是什么」。物理层（真实表、SQL 类型、列到列外键、ON DELETE 行为）用[数据库 schema](type-db-schema.md)：谈「删一行会发生什么」用它，谈「订单到底是什么」留在这。

## 布局

- 实体 = 两段式盒子：
  - **头部**：类型角标 + 实体名。角标按语言选行——`ENTITY`、`JOIN` 纯拉丁走 eyebrow-tech（mono 7–8px）；**混合角标**（如 `ENTITY · 聚合根`）拆两段同基线拼行：拉丁段跟 eyebrow-tech 原规格，中文段 mono 10px · 500 · 0.18em（混合角标专用档；汉字 ≥10px 硬规则）。实体名走 `node-name`。
  - **字段区**：一行一字段，mono 9px（sublabel-tech）。PK 前缀 `#`，FK 前缀 `→`；右端对齐字段类型（`uuid`、`text`）。字段名与类型是纯拉丁技术串，保持 9px 合法。
- 关系 = 实体间直线，两端标基数：`1`、`N`、`0..1`、`1..*`（mono，落在实体边外 10–12px，配 paper 不透明遮罩）。
- 关系动词（撰写、属于、打标）居中于线上：中文走 sans 12px · 0.1em，配不透明 paper 遮罩与线 6px 净空。
- 相关实体靠近排布；让大多数关系是直线而不是乱麻。
- 焦点色落在聚合根或模型的中心实体上。
- 联表 / 纯关联实体用降一级处理：浅填充 + `muted` 描边 + 虚线，不与一等实体争夺注意力。
- 背景默认无纹理，不铺背景点阵。
- 图例条按 style-guide「图例条（底部横条）」节执行；符号样本（`#` 主键、`→` 外键、`1 / N` 基数）符号即样本、后跟中文标签。
- 标题对齐：跟 style-guide「容器对齐与画布基线」container 四件套（内容 x=0 起排，eyebrow / h1 不写 margin-left）。

## 反模式

- 几十个 FK 就画几十条线——按聚类布局替代逐条连线。
- 同一条关系两端的基数记法不一致。
- 字段区强行拉齐等高——按内容自然高度即可。

## 示例

- [`assets/example-er.html`](../assets/example-er.html) — 内容平台数据模型（浅色基准）：作者 — 文章（聚合根，焦点）— 标签 / 文章标签联表
- [`assets/example-er-dark.html`](../assets/example-er-dark.html) — 深色档（对称换基、α 不动）
- [`assets/example-er-full.html`](../assets/example-er-full.html) — full 页面级（subtitle / 三卡 / footer / 九 token）
