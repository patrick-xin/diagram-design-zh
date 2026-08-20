# 甘特图（Gantt）

**最适合**：项目计划与路线图——有明确起止日期的任务、按阶段分组。读者需要一眼看出时间重叠、并行轨道和里程碑次序时用。

## 布局

- **左侧标签列**：x=20–200（180px）。任务名 sans 14px · 600。阶段标签 = 每组上方的 eyebrow：中文 sans 12px · 0.3em（**汉字禁止 <10px**），纯拉丁可用 mono。
- **时间轴区**：x=200–960。时间自左向右。
- **行高**：每任务 40px。条形 h=24 居中在行内（顶部 8px padding）。
- **时间轴**：周/月标签在 y=56，x = 200 + i × pitch；y=64 一条发丝分隔线。轴标签纯拉丁（`W01`、`2026-10`）用 mono 8px，含汉字（`10 月`）用 sans 12px。
- **阶段分组**：每组行后面垫淡色分区 rect（同架构图分区）：`ink@0.02` 填充、`ink@0.10` 描边，阶段 eyebrow 放分区左上。
- **焦点任务条**：恰好 1 条 accent 填充/描边（关键交付或关键路径任务）。其余：muted @ 0.15 填充 + muted 描边。
- **今日 / 里程碑标记**（可选）：当前周 x 位置的 muted 竖虚线。

### 任务条模式

```svg
<!-- 常规任务 -->
<rect x="X_start" y="ROW_Y+8" width="DURATION_PX" height="24" rx="4"
      fill="rgba(86,94,126,0.15)" stroke="rgba(86,94,126,0.60)" stroke-width="1"/>
<text x="X_start+8" y="ROW_Y+25" fill="#29314f" font-size="10" font-weight="600"
      font-family="'MiSans', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif">任务名</text>

<!-- 焦点任务 -->
<rect x="X_start" y="ROW_Y+8" width="DURATION_PX" height="24" rx="4"
      fill="rgba(26,77,217,0.12)" stroke="#1a4dd9" stroke-width="1"/>
<text x="X_start+8" y="ROW_Y+25" fill="#1a4dd9" font-size="10" font-weight="600"
      font-family="'MiSans', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif">关键任务</text>
```

像素时长：`(结束周 − 起始周) × pitch`，pitch = 时间轴宽度 ÷ 总周数。**如实换算**——条形长度就是时长，不许为好看拉伸。

条内文字放不下（窄条）时，省略条内文字、只靠左列任务名。

## 反模式

- 超过 12 个任务（拆子计划或折叠成阶段级视图）
- 每阶段超过 5 条并行轨道（重叠不可读）
- 任务间画依赖箭头（v1 不做；确有必要时用旁注标注）
- 条形标签里写起止日期（日期归 x 轴或注释）
- 所有条等视觉权重（焦点任务必须跳出来）
- 汉字轴标签 / 阶段标签 <10px

## 示例

- [`assets/example-gantt.html`](../assets/example-gantt.html) — 十周排期：三阶段分区 + 焦点条 + 今日线
