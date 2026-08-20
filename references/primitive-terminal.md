# 终端窗口（CLI 外壳变体）

可选的全页皮肤，把任何图表包进一个仿真终端窗口——三个圆点的标题栏、`$` 提示行、通篇等宽字体。用于开发工具发布、CLI 产品贴、技术社交卡——截图要读出"终端"而不是"编辑文档"的场合。

这是**第二套固定皮肤**——九个 token 的表见 [style-guide.md § 终端皮肤](style-guide.md)。它不继承 `onboarding.md` 的品牌 token，也不参与浅/深反转规则；任何终端图都用同样的九个 token，与宿主网站的品牌无关。

## 语法

以 [`assets/template-terminal.html`](../assets/template-terminal.html) 为模板（中文版，mono 栈）。结构：

```html
<div class="terminal">
  <div class="titlebar">
    <div class="dot accent"></div>
    <div class="dot"></div>
    <div class="dot"></div>
    <div class="titlebar-name">deploy.sh — ai-support-architecture</div>
  </div>
  <main class="frame">
    <p class="prompt">
      <span class="sign">$</span> diagram-design render --type architecture
    </p>
    <h1># 自改进循环</h1>
    <svg>...</svg>
  </main>
</div>
```

SVG 内部把默认浅/深 token 1:1 换成 terminal 等价物：`paper` → `terminal-paper`，`ink` → `terminal-ink`，`muted`/`soft` → `terminal-muted`/`terminal-soft`，`accent`/`accent-tint` → `terminal-accent`/`terminal-accent-tint`。hub / 焦点节点的反色填充模式照常适用。

## 中文化的关键差异

- **等宽 = mono 栈**（Sarasa Mono SC 首选）。Sarasa 中英 2:1 等宽，中文在终端语域里第一次有了"真等宽"。系统没装 Sarasa 时退 Noto Sans SC——可读性优先，不追伪等宽。
- **通篇等宽是唯一例外**，不违反"mono 只放技术内容"的三栈纪律——终端皮肤是语域声明，整页都是"终端里的技术内容"。但 `:root` 仍需三栈齐全（self_check 硬校验），只是 sans / serif 不出场。
- 页面标题用 mono 加粗 + `# ` 前缀（读作注释行）。eyebrow 变 shell 提示：`$ ` 用 `terminal-accent`，命令用 `terminal-muted`。标题栏名与提示行可含中文。

## 字号

文字角色与默认坡道对齐（SKILL §7.3）：节点名 14px，中文子标签 / 箭头标签 12px，拉丁技术串 9px；hub 标签抬到 18px。**中文 ≥10px 下限不放宽**（SKILL §7.2）。等宽字在同字号下视觉更小，且终端卡常在社交信息流里缩放观看，不在全幅。

## 标题栏圆点

三个 10px 圆点，macOS 风格。**1-accent 规则在此同样生效**：一个点用 `terminal-accent`，其余两个用 `terminal-soft`。不用红黄绿交通灯三连——那是第二、第三色相，色板禁止。

## 关键规则

- 灰阶九 token 是本皮肤**自有闭集**，不按默认皮肤的值集判脏；强调色用 accent-dark。墨色 `#f5f5f5` 是深底文字角色而非纸面背景，不在默认皮肤禁值令的适用范围。
- 无纯黑——页面用 `terminal-page`、窗体用 `terminal-paper`。与默认皮肤同理：OLED 与印刷上纯黑都会裁切。
- 只有一个 accent。需要第二焦点时用 `terminal-ink`（白）以字重 / 字号强调，不加第二种颜色。
- 背景点阵（若启用）保持 `rgba(255,255,255,0.06–0.08)`——若隐若现的纹理，不做标题栏之外的第二个视觉焦点。

## 何时用

- 开发工具 / CLI 产品发布贴（npm 包、CLI 参数、终端工作流）。
- "这是给工程师的工具"本身是信息的一部分的技术社交卡。
- 要在深色信息流（X、Discord、开发者博客）里跳出来的截图。

## 何时不用的场合

- 编辑性 / 长文——配默认浅色或深色变体。
- `onboarding.md` 品牌匹配产出——终端是固定皮肤，不做品牌化，两者不调和。
- 读者不把 `$` / `#` / 圆点读作外壳而非内容的场合。
