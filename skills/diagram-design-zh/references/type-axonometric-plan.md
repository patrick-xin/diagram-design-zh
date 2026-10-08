# 轴测平面图（Axonometric plan）

**最适合**：一层楼或一个场地从上往下斜着看、连同立在它上面的东西——办公室的房间与家具、校园的楼与路、仓库分区、门店布局。读者需要在一个视图里同时看房间/建筑的相互关系与使用方式时用。

**不用它**：抽象层（**层级堆叠**）；组件与连接（**架构图**——平面图没有箭头，位置关系即一切）；纯俯视 2D 户型（无高度信息时普通平面更省）。

## 投影

与爆炸轴测图同一个 `iso()` 函数（2:1 正二测、26.565° 地面轴、模型单位 4 的倍数落整像素、标签永不用矩阵保持水平）——见 [type-exploded.md](type-exploded.md) 投影节。

## 布局惯例

- **地板是一块板**：整层 footprint 的圆角棱柱（厚度约 6），一切房间与家具立在它上面。
- **房间 = data 上的分区，不是盒子**：房间靠墙段分隔，读者俯视穿透。**墙切到桌面高度（约 22）**：墙高于家具会把房间挡死，低于家具又丢失「这是墙」的读法——切墙不切家具，房间可读、家具有立体感。家具高 10–16。
- **房间数 4–7**；家具按房间配（工位岛、会议桌、储物柜），不摆满——标签要放得下。
- **画布 1000 宽**，viewBox 高随物体 + 底部说明行；窄屏容器横滚（svg `min-width` 900）。

## 标签

- 每房间一个白底标签盒，骑在房间重心上：房名（sans 600 12px）+ 一行技术副题（工位数、席数、用途；含汉字 10px 起，纯拉丁可 mono 9px）。盒白底细描边（`rule`），不遮家具主线。
- **焦点房间的标签描边与文字取 accent**，其余 ink/muted。不用编号、不用图例。

## 焦点房间

至多一间房地板染 accent 淡染（`accent@0.12`），其余房间保持地板色——空间图与图表一样一图一焦点。焦点是「正在讨论的那间」，不自动等于最大的。

## 面上色

同爆炸图的三面明暗：顶面基色、左面 `ink@0.07`、右面 `ink@0.15`；轮廓 ink 1.0–1.2、内棱 `ink@0.50` 0.6–0.8。面 = 不透明基 + ink 覆盖，禁半透明填充单独承担、禁阴影。

## 校园分期变体（campus）

多栋建筑 + 分期建设时：每栋是一个高体量棱柱（高 22–40），**期数写进标签副题**（一期/二期/三期），分期语义靠文字不靠颜色；焦点建筑用整栋体染色（爆炸图焦点件画法：顶/左/右三级 accent 淡染）——高体量棱柱盖住自己的 footprint，地板染色不可见。地面画路网与铺装（`ink@0.30` 淡染区）。

## 可选动效

平面图可从空白地基起、按期数依次升起建筑（reveal 模式，控制器逐字节锁，见 animation.md）；无 JS、reduced-motion、打印、导出都呈现全量建成帧。

## 诚实数据

房间分隔与相对位置、建筑期数取自真实对象；工位/席数/尺寸可示意，示意要直说（full 口径卡）。墙面高度是渲染惯例不编码数据。

## 反模式

- 手摆坐标或 transform 顶替几何。
- 满墙高度把房间挡死，或无高差的纯线框。
- 每间房一个颜色（彩虹分区）——焦点规矩同图表。
- 编号注记 + 底下钥匙；标签随面倾斜。
- 阴影、渐变、发光。
- 房间数超过 7 还不肯并「其他区」。

## 示例

- [`assets/example-axonometric-plan.html`](../assets/example-axonometric-plan.html) — 三层办公区：五房间 + 家具，会议室焦点
- [`assets/example-axonometric-plan-dark.html`](../assets/example-axonometric-plan-dark.html) — 深色档
- [`assets/example-axonometric-plan-full.html`](../assets/example-axonometric-plan-full.html) — full 页面级
- [`assets/example-axonometric-plan-campus.html`](../assets/example-axonometric-plan-campus.html) — 校园分期变体：六栋建筑三期建设，图书馆焦点
- [`assets/example-axonometric-plan-campus-dark.html`](../assets/example-axonometric-plan-campus-dark.html) — 变体深色档
- [`assets/example-axonometric-plan-campus-full.html`](../assets/example-axonometric-plan-campus-full.html) — 变体 full 页面级
- [`assets/example-axonometric-plan-campus-animated.html`](../assets/example-axonometric-plan-campus-animated.html) — 校园分期动效（reveal 3 步）：六栋建筑按三期建设依次进场，地面与道路常驻
