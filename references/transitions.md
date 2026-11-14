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

## FFmpeg 转场 · FFmpeg xfade presets

编号 11–68 使用 FFmpeg 内置转场。左右、上下和开合方向可单独指定。旧版 FFmpeg 的可用项目以本机 `--list-transitions` 为准，编号跨版本保持一致。

| 编号 | 中文名 | ID | 编号 | 中文名 | ID |
|---|---|---|---|---|---|
| 11 | 交叉淡化 | `fade` | 40 | 斜线左下 | `diagbl` |
| 12 | 向左擦除 | `wipeleft` | 41 | 斜线右下 | `diagbr` |
| 13 | 向右擦除 | `wiperight` | 42 | 横切片向左 | `hlslice` |
| 14 | 向上擦除 | `wipeup` | 43 | 横切片向右 | `hrslice` |
| 15 | 向下擦除 | `wipedown` | 44 | 纵切片向上 | `vuslice` |
| 16 | 左推画面 | `slideleft` | 45 | 纵切片向下 | `vdslice` |
| 17 | 右推画面 | `slideright` | 46 | 横向动感模糊 | `hblur` |
| 18 | 上推画面 | `slideup` | 47 | 灰阶显色 | `fadegrays` |
| 19 | 下推画面 | `slidedown` | 48 | 左上角擦除 | `wipetl` |
| 20 | 圆形裁切 | `circlecrop` | 49 | 右上角擦除 | `wipetr` |
| 21 | 矩形裁切 | `rectcrop` | 50 | 左下角擦除 | `wipebl` |
| 22 | 色距溶合 | `distance` | 51 | 右下角擦除 | `wipebr` |
| 23 | 淡经黑场 | `fadeblack` | 52 | 横向挤压 | `squeezeh` |
| 24 | 淡经白场 | `fadewhite` | 53 | 纵向挤压 | `squeezev` |
| 25 | 旋转扫盘 | `radial` | 54 | 推镜放大 | `zoomin` |
| 26 | 柔边左移 | `smoothleft` | 55 | 快速淡化 | `fadefast` |
| 27 | 柔边右移 | `smoothright` | 56 | 缓慢淡化 | `fadeslow` |
| 28 | 柔边上移 | `smoothup` | 57 | 左向风痕 | `hlwind` |
| 29 | 柔边下移 | `smoothdown` | 58 | 右向风痕 | `hrwind` |
| 30 | 圆窗张开 | `circleopen` | 59 | 上向风痕 | `vuwind` |
| 31 | 圆窗收拢 | `circleclose` | 60 | 下向风痕 | `vdwind` |
| 32 | 中线左右开门 | `vertopen` | 61 | 向左覆盖 | `coverleft` |
| 33 | 两侧左右合门 | `vertclose` | 62 | 向右覆盖 | `coverright` |
| 34 | 中线上下开帘 | `horzopen` | 63 | 向上覆盖 | `coverup` |
| 35 | 两侧上下合帘 | `horzclose` | 64 | 向下覆盖 | `coverdown` |
| 36 | 颗粒溶解 | `dissolve` | 65 | 向左揭幕 | `revealleft` |
| 37 | 像素聚焦 | `pixelize` | 66 | 向右揭幕 | `revealright` |
| 38 | 斜线左上 | `diagtl` | 67 | 向上揭幕 | `revealup` |
| 39 | 斜线右上 | `diagtr` | 68 | 向下揭幕 | `revealdown` |

Use `--transition NAME` to select the pair and `--transition-out NAME` to override the exit alone. If neither is specified, both share one random selection per video, independent of the drawing seed. Both renderers support `--list-transitions`. A typical 24-second movie uses 0.5 seconds for the entrance, 1.2 seconds for the finished art, and 0.6 seconds for the exit. Very short or low-frame-rate clips prioritize the clean preview. Use `--no-preview` to skip the entire sequence.
