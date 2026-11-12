# 逐笔油画视频 · Oil Painting Video

把一张肖像从空白画布开始，一笔一笔画成油画。开头可以看清笔尖怎样拖出一笔颜色，随后画笔加速，用越来越细的笔触画出五官。镜头最后从眼部拉回，展示整幅画。

这是一个 Codex 技能，也可以直接用 Python 在本地运行。已有底稿时，渲染过程无需模型 API 或密钥。

## 黄仁勋 Demo

[![黄仁勋逐笔油画：从熟褐色画布到完成的肖像，点击打开完整视频](demo/preview.gif)](demo/jensen-huang.mp4)

上图是 4 倍速无声预览。这支成片以 AI 生成的黄仁勋油画肖像为底稿，程序实际绘制了 **150,053 笔**。原速版长 **32.5 秒**，1080 × 1920，30 fps，带钢琴配乐与刷笔声。

[下载原速有声 MP4（43.5 MB）](https://github.com/DeaglePC/oil-painting-video/raw/refs/heads/main/demo/jensen-huang.mp4) · [查看底稿 PNG](demo/jensen-huang.png)

## 安装

以下命令适用于 Windows PowerShell。需要 Git、Python 和 FFmpeg。请先确认 `ffmpeg -version` 可以运行，所用 FFmpeg 包含 libx264 和 AAC 编码器。

```powershell
$skillsRoot = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $HOME '.codex/skills' }
git clone https://github.com/DeaglePC/oil-painting-video.git (Join-Path $skillsRoot 'oil-painting-video')
Set-Location (Join-Path $skillsRoot 'oil-painting-video')
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
```

渲染需要支持 WebGL 2 的 Chromium 内核浏览器。Windows 下已有 Chrome 或 Edge 时，也可跳过最后一行，让脚本查找系统浏览器。只想使用命令行时，可以把仓库克隆到任意目录。

## 在 Codex 中使用

新开一个对话，附上照片或油画底稿，输入：

> 用 $oil-painting-video 把这张照片做成逐笔油画视频。开头慢慢落笔，中段推近眼睛，最后拉回全景。用技能目录里的 .venv 运行。

## 用命令行画一遍黄仁勋

在仓库根目录运行以下命令。脚本自动创建 `renders` 目录，输出文件名需尚未被使用。

```powershell
.\.venv\Scripts\python.exe scripts/paint_video.py demo/jensen-huang.png renders/jensen-huang.mp4 --title "黄仁勋  /  油画" --focus .55 .31 --radius .284 .211 --detail .60 .294
```

这组参数适合随仓库提供的底稿。片中计数来自当前底稿和细画区域的实际运算结果。仓库附带的 MP4 是流程整理成技能前的原始成片，使用上述命令重画时，笔数和局部笔迹会略有差异。

## 换一张图时怎么调

脚本先把图片等比居中裁成 9:16。下列坐标都以**裁切后的画面**为准，左上角为 `0 0`，右下角为 `1 1`。如果横图里的人脸偏向一侧，先裁出合适的竖版构图。

| 参数 | 作用 |
| --- | --- |
| `--focus X Y` | 把细笔集中在主体中心。画肖像时可取两眼与嘴之间的位置。 |
| `--radius RX RY` | 设置细画区域的椭圆半径，分别占画幅宽、高的比例；脸占画面越大，半径相应调大。 |
| `--detail X Y` | 设置镜头推近的目标，如双眼中点。省略时沿用 `--focus`。 |
| `--title "题签"` / `--no-overlay` | 指定计数上方的题签，或同时隐藏题签和笔数。 |
| `--seconds 20` | 在指定时长内完成全部笔触。默认 32.5 秒。 |
| `--music "配乐.wav"` / `--silent` | 替换内置配乐，或导出无音轨的 MP4。 |
| `--browser "浏览器路径"` | 手动指定 Chrome 或 Chromium 可执行文件。 |

## 笔触怎么生成

[笔触生成器](scripts/strokes.py) 依笔宽分六层比较画布和底稿，在颜色差异大的位置取色，沿明暗等高线延伸笔迹。大笔先建立轮廓，最后两层把细笔集中在主体附近。

[画布渲染器](assets/oil.js) 将每一笔拆成多束笔毛，同时累积颜色和颜料厚度，用侧光表现笔脊。前 14 笔放慢，之后按层加速。最后由 [视频导出脚本](scripts/paint_video.py) 将逐帧画面和音轨合成为 H.264 MP4。Codex 的完整操作说明见 [SKILL.md](SKILL.md)。
