# 导出 PNG / SVG

用户要求图片/矢量文件，或明确点名平台图片时使用。先按 [output-spec.md](output-spec.md) 生成对应尺寸的 HTML，过质量门，再运行脚本。默认导图本身；用户明确要求页眉/卡片/整页时，PNG 用 `--page`。

```bash
python3 <技能目录>/scripts/export.py 图.html --format svg
python3 <技能目录>/scripts/export.py 图.html --format png --scale 2
```

默认输出在源旁，后缀改为 .svg/.png；明确路径用 `-o`。档案直读或临时指南用 `--style-guide <生效指南.md>` 传给质量门。源文件保持不变；目标不能覆盖源 HTML。

## SVG

脚本选择唯一的顶层可访问主图 SVG（保留嵌套图标、忽略装饰 SVG），补命名空间并检查良构 XML；title/desc、id、aria 引用与几何保留。SVG 字体使用字面栈，不带 HTML 内嵌块：目标机器缺自定义字体时会回退，观感可能改变。需要固定本次字体观感交 PNG。

PowerPoint 目标加 `--powerpoint`：仅导出副本的 fill/stroke rgba 转 hex + 独立 opacity，transparent 转 none，不改源码。

多张独立 SVG 的 HTML 用 `--svg-id <主图 id>` 按用户选择单独输出；未指定时明确报错。不能把第一个默认为用户想要的其他图。整页讲解包装需要 HTML 或 PNG，不用 foreignObject 塞进 SVG。

## PNG 与精确尺寸

PNG 需要 Playwright 和可用浏览器。优先使用已有环境；缺依赖时说明限制与安装到隔离环境的方法，不自动改变用户系统配置。可以用 `--browser-executable <已安装 Chrome 路径>`；未指定则用 Playwright 配置的 Chromium。

脚本渲染临时 HTML 副本，等待 `document.fonts.ready`；动效用 `?motion=static` 并确认静态帧。只导图时把 SVG CSS 宽高锁为 viewBox 宽高，并把截图起点对齐至 0，避免响应式宽度与小数位置影响文件尺寸。已有字体块随副本使用；缺内嵌时只在临时副本内嵌，失败会说明，不改用户源文件。

**图本身的像素尺寸 = 锁定的 viewBox 宽高 × scale**。支持小数倍率，例如 1000×360 的图用 `--scale 1.25` 产出 1250×450；交付前实际读取 PNG 宽高核对。整页 `--page` 的高度由页面决定，不套 SVG 尺寸公式。

| 目标 | 常用倍率 |
|---|---|
| 文档 / wiki / 幻灯 | 2 |
| 打印 | 3 |
| 小尺寸缩略 | 1；用户明确要求时可用更小倍率并检查可读性 |

精确目标宽度 / viewBox 宽度给 scale；宽高比必须相同。目标比例不一致时按匹配预设重排，不用裁切或拉伸改变图的含义。倍率须为有限正数，脚本上限 4；过大的目标改用合适画布重排。

默认保留原纸面。用户要求透明底时加 `--transparent`：清页面底，不删除节点底、遮罩和图内有语义的填充；透明交付同样检查目标背景下的可读性。

## 边界与验证

- 质量门错误先修源图；警告按实际内容判断，不能把导出成功当图表质量合格。
- 缺字体、缺依赖、缺完整 SVG、非法 viewBox/倍率，明确报错；不编造成功结果。
- 请求精确动效步骤时按 [animation.md](animation.md) 指定帧另行截图，默认脚本导静态最终态。
- PNG 验实际宽高、字体和内容；SVG 验 XML、命名/aria 与目标工具观感。
- 不添加导出按钮、远程字体或应用脚本，也不把用户已授权的 PNG 请求变成只交 HTML。

多主图页面每个顶层 SVG 有唯一 id；title/desc 使用 `<文件名>-<主图id>-title/desc`，aria 引用对应名称。单主图继续使用原文件名契约。
