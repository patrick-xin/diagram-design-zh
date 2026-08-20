# 导出 PNG / SVG

把生成的图表 HTML 转成可携带的 `.svg` 和/或 `.png`，写在源文件旁边。**仅手动触发——绝不主动运行。**

## 触发

以下情况载入本文件：

- 用户用自然语言要求导出、保存、栅格化、转换、下载 `.svg` 或 `.png` 图表。典型说法：
  - "导出成 PNG"
  - "存一份 SVG"
  - "给我一张这图的 PNG"
  - "转成 png 和 svg"
  - "这张图我要发公众号，导出封面尺寸"
- 用户**只点名平台、没说导出**的说法同样命中（先按 output-spec.md 预设重画，再走本文件出图）：
  - "我需要一个公众号的"
  - "出一个小红书版本"
  - "做成微信封面那种"
  - 平台尺寸**不许心算**——查 output-spec.md 预设表（公众号封面 900×380、小红书 3:4 1080×1440）。

## 范围

两种格式都**只含图本身**——即 `<svg>` 节点。编辑包装（页眉、摘要卡、页脚）按设计丢弃：导出交付物就是图，进 Figma、幻灯、社交卡片或博客配图。

SVG 导出保留源里的 `<title>` 和 `<desc>`。它们带文件名 slug 前缀的 id 是多个导出 SVG 安全内联进同一页的前提——不会出现一张图解析到另一张图无障碍名称的事故。

用户明确要"整页截图包括卡片"是另一种请求——回退到普通的全页截图（用户的浏览器或系统工具）。

## SVG 导出程序

1. 读源 HTML 文件。
2. 抽取**第一个** `<svg ...>...</svg>` 块。用锚定 `<svg` 和 `</svg>` 的多行正则。生成的图通常只有一个 SVG；有多个时第一个是图。
3. 做成独立文件：
   - 开标签确保有 `xmlns="http://www.w3.org/2000/svg"`，缺了就补。
   - 确保有 `viewBox`。模板总会带；缺了就提醒用户，不要猜。
   - `role="img"`、`aria-labelledby`、首子 `<title>` / `<desc>` 原样保留。
   - **不注入任何远程字体 `@import`**——字体已自托管（SKILL.md §7.1），SVG 文本走三栈的系统兜底（宋体/苹方/雅黑）；要像素级一致导 PNG（HTML 内嵌字体随渲染生效）。
4. 头部加 `<?xml version="1.0" encoding="UTF-8"?>\n`，保证文件是良构 XML。
5. 写到源文件旁的 `<主名>.svg`（如 `example-architecture.html` → `example-architecture.svg`）。用户给了明确输出路径就照办。

### 需要向用户说明的注意事项

不联网拉字体的工具（离线 Illustrator、部分 Figma 导入路径、老式 SVG 查看器）会替换字体，且替换的是中文字体——观感差异比英文场景更明显。SVG 在任何现代机器上都靠系统 CJK 字体（宋体/苹方/雅黑）渲染，离线可读。要像素级一致，用 PNG 导出。

## PNG 导出程序

渲染**原始 HTML**（不是抽出来的 SVG），只截 `<svg>` 元素的包围盒。字体随源 HTML 走：内嵌子集（embed_fonts.py 过的文件断网也按思源渲染）或系统三栈，同时满足"只含图"的规则。PNG 背景**透明**（`omit_background=True`），可以放进任何底色的幻灯或文档而不带白边。

### 检测

跑任何东西之前，先验证 Playwright 已安装：

```
python3 -c "import playwright"
```

导入失败时，把下面这段指引原话给用户并停止：

> Playwright 未安装。要启用 PNG 导出，请运行：
> ```
> pip install playwright
> playwright install chromium
> ```
> 装好后再让我导出一次。

不要自动安装。用户要的是一个功能，不是一次系统变更。

### 栅格化

把下面的代码写进临时文件，用 `python3 <tmp.py> <src.html> <out.png>` 运行：

```python
from playwright.sync_api import sync_playwright
import sys, pathlib

src, out = sys.argv[1], sys.argv[2]
scale = int(sys.argv[3]) if len(sys.argv) > 3 else 2

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(device_scale_factor=scale)
    page.goto(f"file://{pathlib.Path(src).resolve()}")
    page.wait_for_load_state("networkidle")
    page.locator("svg").first.screenshot(path=out, omit_background=True)
    browser.close()
```

默认 `device_scale_factor=2`，输出清晰。紧凑素材用 `1`，打印 / 视网膜主图用 `3`，作为第三个 CLI 参数传入。

国内网络下 Google Fonts 可能拖慢 `networkidle`；等不到就改用 `page.wait_for_load_state("load")` 加 `page.wait_for_timeout(1500)`，让系统兜底字体先落地，再向用户说明本次导出用的是兜底字体。

### 输出命名

`example-architecture.html` → `example-architecture.png`，写在源文件旁。用户给了路径就照办。

## 导出尺寸

PNG 的像素尺寸 = SVG `viewBox` × `device_scale_factor`。尺寸决策在画图时就已经做完——预设见 [`output-spec.md` §2](output-spec.md)。导出只选倍率。

| 投放地 | 倍率 | 1280×720 `viewBox` 的结果 |
|---|---|---|
| 文档、README、wiki | 2 | 2560×1440 |
| 幻灯片（投屏） | 2 | 2560×1440 |
| 打印 / PDF 讲义 | 3 | 3840×2160 |
| 内联缩略图、邮件 | 1 | 1280×720 |

### 命中精确像素尺寸

用户要具体尺寸（公众号封面 900×380（`wechat-cover` 预设）、OG 卡 1200×630、幻灯图 1920×1080）时，计算缩放倍率而不是猜——Playwright 接受小数：

```
scale = 目标宽度 / viewBox 宽度
```

960 宽的 `viewBox` 打 1200px 目标就是 `scale=1.25`。两条规则：

- **永远不为命中小目标把倍率压到 1 以下**——那是给字号上柔焦。换小一号预设重画。
- **永远不超过 4**——再大是在放大一张为更小画布设计的布局；换 `slide-16x9` 或打印预设重画。

目标宽高比和 `viewBox` 宽高比不一致时，明说，并提议按匹配的预设重画。给成品图加垫边或裁切来凑画框不是导出操作——它破坏 40px 安全区。

## 边界情况

- **源是动效文件**（含 `data-motion-root`）：导出的是静态最终态。截图前给 URL 加 `?motion=static`，等 `document.fonts.ready` 并确认 `data-frame="static"`，再截；SVG 抽取直接取源里的 `<svg>` 块（语义标记本就完整）。用户点名要某一步时才用 `?motion=step&step=N`。详见 [`animation.md`](animation.md) 导出与验证。
- **找不到 `<svg>` 块**：源不是图表文件。告诉用户，什么都别写。
- **周边 HTML 对用户重要**：他们想要卡片 / 页眉进图。说明本技能只导出图，建议用浏览器全页截图（或单独打印 PDF）。
- **运行时字体缺失**：Playwright 会替换字体，截图会走样。检查源 HTML `<style>` 里有没有 `/*fonts:begin*/` 内嵌块（embed_fonts.py 产物）；没有就先跑内嵌，再导出——修源文件，而不是在导出端绕。

## 这个程序永远不做

- 修改源 HTML。
- 加导出按钮或新的 `<script>` 标签。脚本只可能来自源文件里的动效控制器，导出端一个字符都不加。
- 生成 HTML 时自动附带 `.svg` / `.png`。每次都要手动。
- 用 `foreignObject` 把 HTML 包装（卡片、页眉）嵌进 SVG。跨渲染器太脆。