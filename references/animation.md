# 可选动效

动效用来讲完一张已经完整的静态图，绝不补足缺失的含义。只在两种情况下加载本参考：用户明确要求动效，或动效确实能讲清顺序、累积、评估、包含或传播。否则一律用 `none` 模式交付静态 HTML。

## 模式

每张图选一种模式，标在根元素上：`data-motion-mode="none|reveal|step|loop"`。

| 模式 | 行为 | 控件 / 实现 | 用途 |
|---|---|---|---|
| `none` | 完整稳定的成品图 | 无 JavaScript | 默认；打印、截图、导出、减弱动效回退且无播放控件时 |
| `reveal` | 一次确定性自动播放，结束于完整画面 | ≤5s 用纯 CSS；更长用作用域控制器 | 短的有序讲解；绝不自动重播 |
| `step` | 可暂停的语义分步；**加载即完整成品图**（与无 JS 源一致），播放/重放才从头分步 | 最小内联 JS：播放 / 暂停 / 重放 / 上一步 / 下一步 | 教学、对比、策略追踪 |
| `loop` | 一个装饰令牌循环，不改变含义 | 默认纯 CSS | 安静的流动提示；周期 ≥3s |

只有 `loop` 允许重复。队列状态、打字、字段值、策略结果、包含关系、审计追加都用 `reveal` 或 `step`，且必须收在完整画面。

`reveal` 是唯一被认可的自动播放模式：仅在用户明确要求动效后可在初始加载时跑一次，然后停在完整画面。视口再次进入不重播，没有显式重放动作不重播。

## 静态优先增强契约

1. **源是完整的。** 每个语义节点、标签、连线、状态、结果在增强之前就已出现在 HTML/SVG 里。只有 `.motion-ready` 之下的选择器允许隐藏或变换它们。`step` 模式初始化也停在完整画面——加载第一眼就是成品图，空舞台只允许出现在播放过程中。
2. **稳定截取。** 初始 `data-frame="static"`、`?motion=static`、打印、无 JS、独立 SVG 导出都呈现完整画面并隐藏控件与装饰令牌。不要在任意延时后截取。
3. **CSS 负责呈现。** 出现与位移用 CSS transition/keyframes。最小内联 JavaScript 只允许：绑定显式控件、更新步/状态属性、调度确定性步进、更新专用播报区。禁止 fetch、注入标记、测量路径、改写语义标签或数值。
4. **一个时钟。** 用 `--motion-fast: 160ms`、`--motion-step: 480ms`、`--motion-hold: 720ms`、`--motion-total` ≤ `8000ms`；延迟从整数步推导。不用随机、弹簧或 transition 事件计时。
5. **显式顺序。** 条目标记 `data-motion-item data-step="N"`，N 为 1–8 的整数。DOM 顺序即叙事顺序。每步至多两个条目进场。
6. **稳定收尾。** 完成时全部条目可见并置 `data-frame="end"`。重放先回到第 0 步。暂停清除挂起的计时器，续播从同一步继续。
7. **作用域状态。** 控件只作用于最近的 `[data-motion-root]`；ID、计时器、播报区、步状态绝不跨图。
8. **失败即安全。** JavaScript 只在控件绑定且首帧渲染成功后才添加 `.motion-ready`。在那之前脚本报错，留下的是完整可见的源。

## 语义基元

每个基元除颜色外必须有文字、计数、符号、样式或轮廓之一。

| 基元 | 机制 | 静态 / 减弱动效结果 | 限额 |
|---|---|---|---|
| **路径描绘** | 装饰性重复路径 `pathLength="1"` + 动画 dash offset | 带标签的基础连线保持可见 | ≤2 条；同时只激活 1 条 |
| **逐段揭示**（阶段揭示） | 幽灵预显：未揭示 = opacity .12 压暗预告 + translateY(8px)，transition 挂基态（显隐双向平滑） | 全部阶段可见 | ≤8 步、12 条目；**规则（2026-08-18 真机定案）：未揭示条目保持 .12 可见预告，不再完全隐藏**；静态/结束/减弱态全显 opacity 1 |
| **队列计数**（排队累积） | 稳定槽位；条目揭示 + 可见数字计数 | 最终队列与计数可见 | ≤5 项；不重排 |
| **打字 / 字段填充** | 完整可访问字符串；裁剪装饰层或逐行揭示 | 文字/字段一次性完整可见 | ≤32 个打字字符或 6 个字段 |
| **策略评估**（规则评估） | 有序规则行 + 文字状态 + 当前行轮廓 | 每个状态与结果可见 | 3–6 条规则；2 条追踪 |
| **流动令牌** | 固定路径上的 `aria-hidden` 令牌 | 令牌隐藏；连线仍在 | 一个令牌；loop ≥3s |
| **包含揭示** | 先揭示子项，再出现常驻带标签边界 | 子项与边界可见 | 一次边界过渡 |
| **审计追加** | 按时间顺序逐行揭示；稳定的时间戳/序号 | 完整有序日志可见 | ≤5 行追加 |

不动画布局坐标、连线走向、`viewBox`、节点尺寸、语义文字。避免缩放、视差、弹跳、抖动、发光、粒子与无限闪烁。

```css
:root {
  --motion-fast: 160ms;
  --motion-step: 480ms;
  --motion-hold: 720ms;
  --motion-total: 3600ms; /* 五步 × hold；按图设定 */
  --motion-ease: cubic-bezier(.2,.8,.2,1);
}
.motion-ready [data-motion-item] {
  opacity: 0;
  transform: translateY(8px);
}
.motion-ready [data-motion-item].is-visible {
  opacity: 1;
  transform: none;
  transition: opacity var(--motion-step) var(--motion-ease),
              transform var(--motion-step) var(--motion-ease);
}
.motion-ready[data-frame="end"] [data-motion-item] {
  opacity: 1;
  transform: none;
}
[data-motion-controls][hidden] { display: none !important; }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
  }
  [data-motion-item] { opacity: 1 !important; transform: none !important; }
  [data-motion-decorative] { display: none !important; }
  [data-motion-controls] { display: none !important; }
}
@media print {
  [data-motion-controls], [data-motion-decorative] { display: none !important; }
  [data-motion-item] { opacity: 1 !important; transform: none !important; }
}
```

## 播放控件与键盘

每个交互式 `step` 图在 SVG 之外提供原生按钮：**播放、暂停、重放、上一步、下一步**。用 `data-motion-action="play|pause|replay|prev|next"`，目标 ≥44×44px，焦点可见，不可用时禁用，播放/暂停用 `aria-pressed` 表达状态。

焦点在动效根内时：`→` 前进、`←` 后退、`Home` 复位、`End` 完成、焦点不在原生控件上时 `空格` 切换播放/暂停、无修饰键的 `R` 重放。按住 Control/Command/Alt 时绝不拦截 `R`。不从输入框、链接或无关区域抢键。画面切换绝不移动焦点。

提供可见的操作说明和作用域内的 `role="status" aria-live="polite" aria-atomic="true"` 播报区。播报区放在动效根之内、`[data-motion-controls]` 之外——这样减弱动效/静态状态隐藏控件时不会连带隐藏播报。播报用户动作（如「第 3 步 / 共 5 步：首个分歧点」）；不逐帧播报自动播放。控件只作用于最近的 `[data-motion-root]`。

**用 [`assets/template-motion.html`](../assets/template-motion.html)，不要另造控制器。**它的内联控制器就是可执行的实现契约：把 `<script data-diagram-controls>` 的脚本体逐字节原样复制，只替换图表内容与 slug 前缀的 ID。自检器会拒绝被修改或新增的控制器。控制按钮、播报文案、`<noscript>` 说明照抄模板的中文文案，不自行改写。

## 减弱动效、颜色与无障碍

- `prefers-reduced-motion: reduce` 初始化为完整静态画面，禁用并隐藏全部播放控件，隐藏装饰运动，置 `data-motion-state="reduced"`，播报文案说明播放不可用。绝不在完整画面旁边播报中间步。
- SVG 的 `<title>` 与 `<desc>` 描述完整含义，不描述动画。操作说明保持为可见的 HTML 文字。
- 装饰层带 `aria-hidden="true" focusable="false"`。语义文字在可访问树里只出现一次。
- 状态绝不只靠颜色：策略用符号 + 文字（如 ✓ 通过 / ✗ 失败 / ⊘ 跳过 / ○ 未到达）；队列给计数；活动阶段给编号/标签/轮廓。
- 无闪烁，亮度变化不超过每秒三次。

## 复杂度与确定性时序

动效不放宽静态预算：≤8 个语义步（目标 3–6）、≤12 个标记条目、≤2 个同时揭示、≤2 条描绘路径、一个流动令牌循环、160–600ms 过渡、400–1200ms 停顿、≤24px 位移、总自动播放 3–8s。

声明 `data-step-count`；不从 transition 事件推断步数。`--motion-total` = 步数 × `--motion-hold`，且不超过 8 秒预算。每个根一条 `setTimeout` 链，间隔取自 `--motion-hold`；暂停/重放/页面隐藏时清除，渲染完最后一步后立即清除；语义播放绝不用 `setInterval`。`document.visibilityState` 变 hidden 时暂停，之后不追赶。`?motion=step&step=N` 仅当 N 是 0..`data-step-count` 的非负十进制整数时暴露一个零时长精确帧，供视觉回归；缺失、小数、负数、超预算值一律走正常播放。

最终态截取契约是同步的：`?motion=static`、`<html data-motion="static">` 或 `none` 模式呈现全部语义条目、隐藏控件与装饰层、置 `data-frame="static"`。截取前等待 `document.fonts.ready`。同一 URL、视口、字体、设备像素比下的两次截取必须逐像素一致；随机延时、生成 ID、时钟、运行时路径测量都被禁止。

## 导出与验证

PNG 与 SVG 导出默认是静态最终态，除非用户点名要某一步。截取前打开 `?motion=static`，等 `document.fonts.ready`，确认 `data-frame="static"`。SVG 抽取省略 HTML 控件与脚本；源可见的语义标记保证结果完整。

跑技能自带的客观门：

```bash
python3 <技能目录>/scripts/self_check.py path/to/animated-diagram.html
```

它检查：脚本唯一且与模板逐字节一致、模式/步数声明、步号连续、动效预算、无 JS 源可见性、装饰可访问性、全套控件、播报区、减弱动效/打印 CSS。然后在浏览器里人工核验：

1. 关闭 JavaScript：完整图表仍然可见且可读。
2. 模拟 `prefers-reduced-motion: reduce`：最终态完整，播放控件隐藏且禁用，DOM 播报说明播放不可用。
3. 只用键盘：Tab 能到每个原生控件；Enter/空格 可操作；←/→/Home/End 换步且不移动焦点。
4. 暂停、续播、重放两次：顺序与最终态完全一致。
5. `?motion=static` 等 `document.fonts.ready` 后截取两次：像素稳定。
6. 打印预览 + PNG/SVG 导出：控件与装饰令牌消失，语义标签与关系全部保留。

## 反模式

- **未揭示条目完全隐藏（opacity 0）**：未揭示 = opacity .12 幽灵预显（2026-08-18 真机定案）——首屏要能预告哪些元素即将动画；完全隐藏是已废止的旧案。已揭示/静态/结束态文字保持 opacity 1（.12 仅是待揭示预告态，不承担正读）。
- **把 transition 只挂在 `.is-visible` 上（回退瞬间消失）**：transition 挂基态，显现与回退双向都走 `--motion-step` 平滑过渡。
- 未经要求的自动播放、超出唯一认可 `reveal` 的自动播放、视口再进入重播、无休止的语义循环。
- 无 JS 或减弱动效时出现空白/半成品画面。
- 用动效抢救一张过密或没标签的静态图。
- 通过/失败、队列满载、结果只用色相表达。
- 远程脚本、通用应用逻辑、运行时几何、语义文字出现两份。
- 按墙上时钟延时截取，而不是用显式静态覆盖。
