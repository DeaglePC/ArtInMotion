# 绘画视频转场 · Painting transitions

从下表按中文名、英文 ID 或编号选。用户没有指定时，渲染器为每条视频随机选一种，成画进场与回到纸面共用该效果。要重现随机结果，可从日志的 `Transitions:` 读出两个 ID，下次显式传入。工具、音效和时间线都从转场结束后开始绘制。

| 编号 | 中文名 | ID | 画面变化 |
|---|---|---|---|
| 01 | 水墨晕染 | ink-bloom | 数处不规则的墨团洇开，汇成全画 |
| 02 | 干刷横扫 | dry-brush | 带细碎刷毛的边缘横扫纸面 |
| 03 | 纸角翻页 | page-curl | 卷边亮面和投影斜向掠过 |
| 04 | 镜头光圈 | iris | 六边形光圈从主体中央展开 |
| 05 | 马赛克显影 | mosaic | 方块错落出现并拼合 |
| 06 | 绸带交错 | ribbon | 相邻横带从左右两侧交错滑入 |
| 07 | 棱镜折光 | prism | 斜向光带边缘短暂分离色彩 |
| 08 | 柔焦显影 | focus | 从纸面淡入朦胧轮廓，再逐渐合焦 |
| 09 | 炭粉聚散 | charcoal | 细粒在纸面聚集，密度逐渐增加 |
| 10 | 折扇开合 | silk-fan | 扇骨从底边展开，依次露出画面 |

Use `--transition NAME` to select the pair and `--transition-out NAME` to override the exit alone. If neither is specified, both share one random selection per video, independent of the drawing seed. Both renderers support `--list-transitions`. A typical 24-second movie uses 0.5 seconds for the entrance, 1.2 seconds for the finished art, and 0.6 seconds for the exit. Very short or low-frame-rate clips prioritize the clean preview. Use `--no-preview` to skip the entire sequence.
