# 皮肤表（reskin.py 的数据侧）

皮肤 = **语义槽位 → 色值** 的映射表。`scripts/reskin.py` 拿它对成品 HTML 做
值级替换：hex → 新 hex，
`rgba(基, α)` → 新基色 + 原 α 逐字保留。**α 档位是结构不是颜色**——换肤
永远不动透明度，15 档梯子、treemap 六档坡道、深色 0.72 契约换肤后原样成立。

## 槽位（与 style-guide / type-*.md 的角色名一致，换皮肤只换值不换名）

| 槽位 | 默认值 | 说明 |
|---|---|---|
| `paper` / `paper-2` | `#ffffff` / `#f3f2ff` | 纸面 / 容器底 |
| `ink` / `muted` / `soft` | `#29314f` / `#565e7e` / `#8f94ab` | 正文 / 二级 / 三级（含各自的 rgba 基） |
| `accent` | `#1a4dd9` | 焦点 ≤2 处；也是 link 色 |
| `paper-dark` | `#e0e4ff` | 深色档文字的纸色基（hex 与 rgba(224,228,255,α) 同源） |
| `dark-bg` / `muted-dark` / `soft-dark` / `accent-dark` | `#0a0d1b` / `#a2a9ce` / `#787fa2` / `#7d98ff` | 深色档其余四槽 |
| `series-1..5`（`-dark`） | 翠绿 / 暖橙 / 绛红 / 靛蓝 / 紫棠 | 图表系列色；不写就保持默认 |

**不在表里、也永远不许进表**：语义色族五色（浅深两档，sem-security `#b85450`/`#bf6561` /
sem-observability `#5a7d9a`/`#5e83a1` / sem-governance `#7a8c47` / sem-backup `#8c6d3f`/`#9b7946` /
sem-workspace `#c9a23a`）——换皮不换义，写了会被 gate 拒绝。

## 现有皮肤

| 名 | 来源 | 性质 |
|---|---|---|
| `default` | style-guide 现行值快照 | identity；配 `--dry-run` 当颜色出处普查器 |
| `xinzhongshi` | `references/skin-xinzhongshi.md` | 近似——钤印/题签/朱批/黛蓝 link 是生成时语义，值替换做不了 |
| `zhongguohong` | `references/skin-zhongguohong.md` | 忠实——节点语义沿用默认只换基色，link==accent 天然成立 |

皮肤文档（`references/skin-*.md`）是权威；本目录 JSON 只是
它们的机器可读转录，改值先改文档再同步这里。

## gate（定义在皮肤表层，不过门不让用）

- ink 对 paper WCAG 对比度 ≥ 4.5（硬门槛，< 7 给提示）
- 槽位互相撞值 = 错（焦点必须唯一）
- accent 与语义五色距离 < 40 → 警告（焦点色混进领域色）
- series 要覆盖就五色齐上，且两两色相差 ≥ 20°（防彩虹；现行默认系最窄对 22°，即阈值锚点）
- 深色槽位只覆盖一部分 → 警告（深色成品会得到半套皮肤）

## 用法

```
python3 scripts/reskin.py --list                              # 列皮肤 + 过 gate
python3 scripts/reskin.py --skin zhongguohong \
        assets/example-high-level.html \
        -o assets/example-high-level-zhongguohong.html        # 换肤出成品
python3 scripts/reskin.py --skin default --dry-run 文件.html   # 颜色出处普查
```

- 产物默认打 `reskin:<名>` 来源注释（`--no-tag` 关闭）——self_check 的
  颜色层靠它把这张皮肤表的值并进闭集，换肤产出照常过质量门。
- `-o` 换了文件名词干时，脚本自动同步 title/desc 的 slug id，保住
  `self_check.py` 的 `{stem}-title/-desc` 契约；产出直接跑 self_check 验证。
- 产出命名沿用现有惯例：`<原名>-<皮肤名>.html`。
- 未知颜色（不在任何槽位、不是语义五色、也不是终端灰阶）会以 `⚠ 未知`
  报告——这同时是值集闭集的脏值探测器；终端外壳灰阶七色原样保留、
  单列「终端」段（终端不吃皮肤，但只许出现在终端外壳文件里——
  self_check 在非终端文件里见到会红）。

## 边界（设计如此，不是 bug）

- reskin 只做值替换。皮肤的结构性语义（新中式钤印、题签、朱批、黛蓝 link）
  只能在生成时走皮肤文档，事后换肤只能逼近色板。
- 皮肤缺深色档（新中式 / 中国红）时深色值保持默认并告警，不产出半套猜测值。
- 纯色值改动不需要重跑 `embed_fonts.py`（那是文本变化才做的事）。
