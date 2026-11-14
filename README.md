# 逐笔绘画工作室

[English](README.en.md) · [给 AI 助手的执行说明](SKILL.md)

把一张照片从空白纸面逐步画出来。可以交付一段 **MP4 绘画过程**、一张 **PNG / JPEG / WebP 成画**，也可以一次导出两者。笔触来自原图的颜色、边缘和局部走向。整个绘制过程在本机运行，无需 AI 生图、模型下载或 API Key。

![20 种画法对同一参考图的实际渲染](demo/styles.jpg)

图例采用仓库自带的黄仁勋底稿，编号与下面的画风表一致。上传自己的摄影原片即可直接绘制，支持单人、合照、风景、静物及横竖画幅。

## 让另一个 AI 直接使用

把下面这段话和照片一起交给能执行本地命令的助手：

> 从 https://github.com/DeaglePC/oil-painting-video 安装这个技能，读取仓库根目录的 SKILL.md，配置依赖。直接用我附的原照画彩色铅笔，保留构图，导出 24 秒 MP4 和一张 PNG。开头慢画，全程能看到笔尖。实际执行并把两个文件给我。

已安装的助手可以直接说「用 $oil-painting-video 把这张照片画成水彩，只给我成画」。其他代理可以把仓库放在任意位置，按 SKILL.md 调用相同的命令行。技能调用名沿用 `oil-painting-video`。

## 安装与首跑

在 Codex 的技能目录安装时运行下面两行。其他助手也可以克隆到自己的工作区。

```sh
git clone https://github.com/DeaglePC/oil-painting-video.git ~/.codex/skills/oil-painting-video
cd ~/.codex/skills/oil-painting-video
```

建议 Python 3.11 或 3.12。视频另需 PATH 中可用的 FFmpeg（带 libx264）。仅渲染静态图时只需 Python 依赖。在仓库根目录执行：

```sh
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell 使用 .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/render_art.py --list-styles
python scripts/render_art.py --input demo/jensen-huang.png --style watercolor --size 480 --fps 12 --seconds 3 --image renders/test.png --video renders/test.mp4
```

## 日常使用

```sh
# 同一批笔触同时生成视频和干净的成画
python scripts/render_art.py --input photo.jpg --style colored-pencil --video renders/pencil.mp4 --image renders/pencil.png

# 只出图片，无需启动浏览器或视频编码器
python scripts/render_art.py --input photo.jpg --style 02 --image renders/hatching.webp

# 用本地音频配乐，按指定时长裁切或循环
python scripts/render_art.py --input photo.jpg --style block-print --seconds 10 --music music.wav --video renders/print.mp4
```

默认 24 秒、30 fps、长边 960 像素。自动校正 EXIF 方向，保持构图并将边长取偶数。用 `--size 1920` 提高长边分辨率，`--seed` 固定笔触变化。默认开头慢画，中段加速，结尾停留。用 `--opening-seconds 6` 给开头几笔留出六秒，用 `--pigment 1.25` 加浓原照绘制时的笔触。绘画工具全程可见，拼贴、像素与沙画使用放置光标。`--no-tool` 输出纯画面。默认视频静音。输出文件必须使用新名字，可用 `--help` 查看完整选项。

## 画风

| 编号 | 画法 | 命令中的名称 | 编号 | 画法 | 命令中的名称 |
|---|---|---|---|---|---|
|01|轮廓线描|contour|11|蜡笔与油画棒|crayon|
|02|密线排绘|hatching|12|平涂插画与漫画|flat|
|03|黑白明暗素描|charcoal|13|黑白刻印与剪影|woodcut|
|04|彩铅细绘|colored-pencil|14|套色版画|block-print|
|05|黑白水墨|ink-wash|15|点描与网点|stipple|
|06|透明水彩与彩墨|watercolor|16|拼贴与镶嵌|collage|
|07|工笔设色与重彩|gongbi|17|沙画与颗粒画|sand|
|08|细腻写实绘画|realist|18|流体与拓纹|marbling|
|09|可见笔触与厚涂|impasto|19|几何切面|facets|
|10|干粉柔绘|pastel|20|像素与字符（像素示例）|pixel|

画风可用英文 ID、表中两位编号或 `--list-styles` 列出的中文全名。每组提供一种程序化演绎，例如 16 用纸片效果、20 用像素格。自定义画法或从文字构图时，可由助手编写 [笔触计划](references/marks.md)，用 `--plan` 直接输出图片或视频；也可按该文档加入新的取色和运笔算法。 更多材料和画法（含书法、喷绘、壁画、彩窗与字符画）的映射与扩展思路见[画法选择表](references/media.md)。

## 经典油画模式

原有的竖屏油画、镜头推拉、笔数计数、配乐与刷笔声仍有独立入口。需要 Playwright Chromium 和支持 WebGL 2 的环境。执行 `python -m playwright install chromium` 后按[经典油画说明](references/classic-oil.md)运行。

[![经典黄仁勋油画预览](demo/preview.gif)](demo/jensen-huang.mp4)
