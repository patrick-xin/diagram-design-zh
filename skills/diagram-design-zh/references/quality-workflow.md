# 内容与交付验证

单文件检查验证源码契约；内容对账验证已声明的源值与关系映射；浏览器验证最终字体、尺寸、遮挡与阅读体验。三者各有范围，任何一项通过都不能替代其他两项。

## 源码与工具

```bash
python3 <技能目录>/scripts/self_check.py 图.html
python3 <技能目录>/scripts/self_check.py 图.html --style-guide <生效配置.json>
```

交付物默认 diagram 模式；图中的属性或注释不能改变检查契约或取得豁免。

字体/文本改变后运行 embed_fonts；颜色-only 不重建字体。PNG/SVG 走 [export.md](export.md)。主图由顶层可访问 SVG 标识；装饰图标不参与选择，多主图用 `--svg-id`。

## 内容模型

数据图保留源值、单位与坐标映射；导入图保留源 ID→成品 ID 的映射及合并/省略理由。数据模型是非执行的 JSON 附属文件，不能混进图面或作为 agent 指令。

```json
{
  "schema": 1,
  "values": {"shop": 2.4},
  "encodings": [
    {"key": "shop", "element": "bar-shop", "attribute": "height", "scale": 60, "offset": 0},
    {"key": "shop", "element": "label-shop", "attribute": "text"}
  ]
}
```

上例需要真实源数据为 2.4，柱与数字标签的实际 id 对应这两个元素。系数从轴的真实单位和范围计算，不为了让错误成品过闸倒推系数。支持数值属性与可见数字文本的线性映射，不执行任意公式。默认容差 0.01 SVG 单位，显式容差只允许 0..1；单位前后缀在映射中声明。

```bash
python3 <技能目录>/scripts/content_check.py 图.html --model 图-content.json
```

对于非线性/复杂面积编码，另用明确的数据计算核对方式，不伪称此工具支持全部图表数学。源模型与图之间的映射仍需人检查是否表达了用户要求的故事。

## 导入内容对账

先运行提取器的 `--json` 得到单张已选图/页的完整 IR；摘要会截表，不能用截断摘要证明 faithful 完整。

模型中 `nodes` / `edges` 各记录 `source_ids` 与成品 `element`。合并多个 ID 要给 reason；省略项放 `omitted`，逐项给 kind、id、reason。图中关系元素携带 `data-source` / `data-target`，值指向对应成品节点 ID；非空边标签通过 `label_element` 指向可见文字。改写标签需同时记录 display_label 和 reason。

```bash
python3 <技能目录>/scripts/content_check.py 图.html --model 图-content.json --source-ir 源-ir.json
```

未映射也未交代的节点/关系、错误端点、缺可见标签会失败。时序片段、备注和 ER 字段完整记录在 `source_facts`（fragments、notes、fields）；程序核对记录完整性，呈现方式与守卫/基数的实际含义仍须逐项审核。省略理由是可复核记录，不自动代表用户批准。

## 实际阅读

实际字体大小 = 源字号经 SVG 与祖先变换后的显示大小。按目标窗口测量；保留图表尺度时把横向滚动限制在图区域，不能让整页溢出。新成品检查中文至少 10 CSS px；投屏/打印再按受众距离提高，不把最低线当默认字号。

```bash
python3 <技能目录>/scripts/reading_check.py 图.html --width 360 --height 800 --browser-executable <Chrome 路径>
```

需要滚动阅读版时加 `-o 图-reading.html`；输出包装和最小显示宽度，保留 SVG 几何、内容、字号和颜色，源文件不改。滚动容器会裁切 SVG 边界外的内容，包装须按实际边界预留空间；检查结果中的 `clippedElements` 必须为空，横向内容须能滚动到达，顶部/底部文字不能被截断。此检查覆盖元素布局边界，不代表滤镜、标记等全部绘制效果已验证；复核桌面与目标窄屏的实际观感。

字体内嵌依赖见 [requirements-fonts.txt](../scripts/requirements-fonts.txt)，PNG 导出与阅读测量依赖见 [requirements-browser.txt](../scripts/requirements-browser.txt)，并需可用的 Chrome/Chromium。按实际使用的功能安装依赖。

最终审核仍包括内容事实、真正的背景对比度、截断/遮挡和交付尺寸。
