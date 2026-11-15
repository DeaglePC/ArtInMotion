/* ==========================================================================
   ArtInMotion · Interactive Atelier & Screening Room Controller
   ========================================================================== */

const PRESETS = [
  { no: "01", id: "contour", zh: "轮廓线描", en: "Contour Line", toolZh: "钢笔长线", toolEn: "Fine Pen", ground: "#FBF8EE", family: "line", hasFilm: false, noteZh: "从照片边缘提取显著长轮廓线，慢笔起稿清晰利落。", noteEn: "Extracts dominant Canny edge paths for crisp, legible opening linework." },
  { no: "02", id: "hatching", zh: "密线排绘", en: "Cross Hatching", toolZh: "针管排线", toolEn: "Technical Pen", ground: "#FBF8EE", family: "line", hasFilm: false, noteZh: "平行细线铺底，暗部自动加密交叉排线表现体积。", noteEn: "Builds tonal depth through directional parallel and cross-hatched meshes." },
  { no: "03", id: "charcoal", zh: "黑白明暗素描", en: "Charcoal Tonal", toolZh: "炭条纸纹", toolEn: "Charcoal Stick", ground: "#FBF8EE", family: "line", hasFilm: true, noteZh: "炭粉层叠压暗并保留粗颗粒纸纹，光影过渡克制厚重。", noteEn: "Layers dry charcoal grain over toothy paper for sculptural chiaroscuro." },
  { no: "04", id: "colored-pencil", zh: "彩铅细绘", en: "Colored Pencil", toolZh: "彩铅落纸", toolEn: "Colored Pencil", ground: "#FBF8EE", family: "paint", hasFilm: false, noteZh: "细密色线顺着面部结构交叠，配真实铅笔划纸原声。", noteEn: "Directional fiber strokes follow surface contours with real pencil foley." },
  { no: "05", id: "ink-wash", zh: "黑白水墨", en: "Monochrome Ink Wash", toolZh: "水墨毛笔", toolEn: "Sumi Brush", ground: "#FBF8EE", family: "ink", hasFilm: true, noteZh: "先淡墨晕染大势，再浓墨提神，高光处自然留白。", noteEn: "Pale-to-deep sumi washes with deliberate paper highlights left untouched." },
  { no: "06", id: "watercolor", zh: "透明水彩与彩墨", en: "Watercolor", toolZh: "水彩圆笔", toolEn: "Wash Brush", ground: "#FBF8EE", family: "ink", hasFilm: false, noteZh: "半透明色层湿叠洇合，可通过 --pigment 加浓色泽。", noteEn: "Translucent wet-on-dry color glazes; deepen saturation with --pigment." },
  { no: "07", id: "gongbi", zh: "工笔设色与重彩", en: "Gongbi Rich Color", toolZh: "设色勾线", toolEn: "Gongbi Brush", ground: "#FBF8EE", family: "ink", hasFilm: true, noteZh: "分区多层罩染设色后再以细墨线严谨勾勒神态。", noteEn: "Structured mineral-style color washes anchored by fine contour ink lines." },
  { no: "08", id: "realist", zh: "细腻写实绘画", en: "Realist Painting", toolZh: "写实画笔", toolEn: "Round Brush", ground: "#FBF8EE", family: "paint", hasFilm: true, noteZh: "由大色块渐进收细笔触，细腻还原肤色冷暖与五官细节。", noteEn: "Progressively refines brush scale from broad underpainting to fine likeness." },
  { no: "09", id: "impasto", zh: "厚涂油画", en: "Impasto Oil Painting", toolZh: "猪鬃油画笔", toolEn: "Bristle Oil Brush", ground: "#8B705B", family: "paint", hasFilm: true, noteZh: "亚麻熟褐底布上堆叠立体猪鬃油彩笔触，实时解算颜料脊线高光。", noteEn: "3D multi-bristle oil ridges with raking specular highlights over woven raw-umber linen." },
  { no: "10", id: "pastel", zh: "干粉柔绘", en: "Soft Pastel", toolZh: "色粉柔擦", toolEn: "Pastel Chalk", ground: "#DDD3C3", family: "paint", hasFilm: true, noteZh: "暖灰有色粉纸打底，粉质笔触柔和朦胧、温润透气。", noteEn: "Velvety chalk marks blended softly across warm tinted pastel paper." },
  { no: "11", id: "crayon", zh: "蜡笔与油画棒", en: "Crayon & Oil Pastel", toolZh: "油画棒", toolEn: "Oil Pastel", ground: "#FBF8EE", family: "paint", hasFilm: true, noteZh: "饱满蜡质粗笔保留纸面飞白孔隙，色彩浓郁灵动。", noteEn: "Rich waxy strokes that skip across paper tooth with vibrant energy." },
  { no: "12", id: "flat", zh: "平涂插画与漫画", en: "Flat Illustration", toolZh: "平涂墨线", toolEn: "Cel Brush", ground: "#FBF8EE", family: "paint", hasFilm: true, noteZh: "概括利落的色块分区铺设，最后压上清晰结构墨线。", noteEn: "Clean graphic color regions finished with crisp comic ink contours." },
  { no: "13", id: "woodcut", zh: "黑白刻印与剪影", en: "Woodcut Relief", toolZh: "木刻圆刀", toolEn: "Carving Gouge", ground: "#2B2725", family: "line", hasFilm: true, noteZh: "在深褐木版上以减色顺序一刀刀刻出受光亮面。", noteEn: "Subtractive gouge cuts carve bright highlights out of a dark timber block." },
  { no: "14", id: "block-print", zh: "套色版画", en: "Block Print", toolZh: "油墨滚筒", toolEn: "Ink Roller", ground: "#FBF8EE", family: "construct", hasFilm: false, noteZh: "按明暗色版分版依次叠印，带有质朴版画套色肌理。", noteEn: "Sequential multi-plate color registration with bold printmaking contrast." },
  { no: "15", id: "stipple", zh: "点描与网点", en: "Stipple & Halftone", toolZh: "点彩细笔", toolEn: "Stipple Pen", ground: "#FBF8EE", family: "line", hasFilm: true, noteZh: "不画一根线条，完全依靠墨点疏密聚散凝结出光影。", noteEn: "Forms continuous tone purely through calibrated stipple dot density." },
  { no: "16", id: "collage", zh: "拼贴与镶嵌", en: "Collage & Mosaic", toolZh: "剪纸色片", toolEn: "Cut Paper", ground: "#FBF8EE", family: "construct", hasFilm: true, noteZh: "将照片解构为一片片不规则彩纸，逐片落位拼合成像。", noteEn: "Places polygonal torn-paper color fragments one piece at a time." },
  { no: "17", id: "sand", zh: "沙画与颗粒画", en: "Backlit Sand Art", toolZh: "背光手影", toolEn: "Sand & Hand", ground: "#FFDA91", family: "construct", hasFilm: false, noteZh: "俯视暖光灯箱，背光手影撒沙铺暗、指腹推薄透出底光。", noteEn: "Overhead warm lightbox performance: pour sand, sweep highlights, carve lines." },
  { no: "18", id: "marbling", zh: "流体与拓纹", en: "Fluid Marbling", toolZh: "水拓画针", toolEn: "Marbling Stylus", ground: "#FBF8EE", family: "construct", hasFilm: true, noteZh: "沿等高流场排布回旋色带，呈现水拓画般的丝滑波纹。", noteEn: "Combed ribbon veins flow along tonal contours like suminagashi marbling." },
  { no: "19", id: "facets", zh: "几何切面", en: "Geometric Facets", toolZh: "切面色块", toolEn: "Planar Facet", ground: "#FBF8EE", family: "construct", hasFilm: true, noteZh: "以自适应三角剖分构筑立体切面，边缘硬朗现代。", noteEn: "Delaunay planar shards cluster densely around facial features." },
  { no: "20", id: "pixel", zh: "像素与字符", en: "Pixel & Tile Art", toolZh: "方格色砖", toolEn: "Mosaic Tile", ground: "#FBF8EE", family: "construct", hasFilm: true, noteZh: "将连续光影化为秩序井然的马赛克方格逐粒镶嵌。", noteEn: "Discrete chromatic tiles assemble into a crisp retro-modern mosaic." }
];

const HERO_REELS = [
  {
    key: "legendsDuo",
    zhTab: "01 · 梅罗双骄油画 (24s)",
    enTab: "01 · Messi × CR7 Oil (24s)",
    src: "./demo/legends/01-duo-messi-ronaldo.mp4?v=1",
    portrait: false,
    zhCaption: "胡桃木画架装裱 · 09 号立体厚涂油画引擎逐笔塑造 C 罗与梅西同框瞬间，配前三笔刷涂原声与即兴钢琴",
    enCaption: "Walnut studio easel · 3D impasto oil bristle relief of Cristiano Ronaldo & Lionel Messi with brush foley & solo piano"
  },
  {
    key: "ribbon",
    zhTab: "02 · 画板彩铅 (24s)",
    enTab: "02 · Board Pencil (24s)",
    src: "./demo/ribbon-portrait.mp4?v=4",
    portrait: false,
    zhCaption: "木纹画板美纹纸装裱 · 06 号绸带进退场 · 前三笔配轻柔铅笔原声，随后切入随机即兴合成钢琴",
    enCaption: "Mounted on studio wood board with masking tape · Gentle foley on first 3 strokes + random improvised piano"
  },
  {
    key: "atlas20",
    zhTab: "03 · 20 画风对照 (30s)",
    enTab: "03 · 20 Styles (30s)",
    src: "./demo/musk-style-atlas.mp4",
    portrait: true,
    zhCaption: "同一张肖像裁切，每屏 4 种画风同步落笔，30 秒纵览 01–20 全部媒材",
    enCaption: "One reference crop rendered side by side across all 20 media presets (01–20)"
  },
  {
    key: "paintTrans",
    zhTab: "04 · 绘画转场 (31s)",
    enTab: "04 · Art Transitions (31s)",
    src: "./demo/painting-transitions.mp4?v=2",
    portrait: false,
    zhCaption: "全画幅展示水墨晕染、干刷横扫、纸角翻页、折扇开合等 10 种绘画专属进退场",
    enCaption: "Full-frame showcase of ink bloom, dry brush, page curl, silk fan, and 6 more painting transitions"
  },
  {
    key: "classicOil",
    zhTab: "05 · 3D 特写运镜 (32s)",
    enTab: "05 · 3D Oil Zoom (32s)",
    src: "./demo/jensen-huang.mp4",
    portrait: true,
    zhCaption: "WebGL 立体油彩笔触 · 电影级特写推镜刻画双眸，落笔计数结束后拉回完整肖像",
    enCaption: "WebGL 3D bristle relief · Camera pushes in on the eyes with live stroke counter before pulling back"
  }
];

const LEGEND_FILMS = [
  {
    no: "01",
    slug: "01-duo-messi-ronaldo",
    player: "duo",
    playerBadgeZh: "CR7 × MESSI",
    playerBadgeEn: "CR7 × MESSI",
    styleId: "impasto",
    boardCli: "easel",
    transIn: "silk-fan",
    aspect: "landscape",
    zh: "绝代双骄同框 · 2011 日内瓦国家队对决",
    en: "Rivals Side by Side · Portugal vs Argentina (2011)",
    subZh: "胡桃木画架 · 09 厚涂油画 · 10 折扇开合转场",
    subEn: "Walnut Easel · 09 Impasto Oil · 10 Silk Fan Reveal",
    storyZh: "2011 年 2 月 9 日葡萄牙对阵阿根廷，身披五盾 7 号红衫的 C 罗与蓝白 10 号的梅西并肩同框。由纯 Python 3D 猪鬃厚涂油画引擎在熟褐亚麻画布上逐层堆叠立体脊线高光，装裱于深色胡桃木画架。",
    storyEn: "Geneva, 9 Feb 2011: Cristiano Ronaldo in Portugal #7 crimson beside Lionel Messi in Argentina #10 sky-blue stripes. Rendered stroke-by-stroke with 3D multi-bristle impasto oil relief on a dark walnut studio easel.",
    credit: "Photo: Fanny Schertzer · CC BY 3.0"
  },
  {
    no: "02",
    slug: "02-messi-worldcup-star",
    player: "messi",
    playerBadgeZh: "MESSI #10",
    playerBadgeEn: "MESSI #10",
    styleId: "colored-pencil",
    boardCli: "tape",
    transIn: "ribbon",
    aspect: "portrait",
    zh: "梅西 · 三星蓝白与世界冠军金章",
    en: "Messi · Three-Star World Champion #10",
    subZh: "美纹纸木画板 · 04 彩铅细绘",
    subEn: "Masking-Taped Board · 04 Colored Pencil",
    credit: "Photo: Bryan Berlin · CC BY-SA 4.0"
  },
  {
    no: "03",
    slug: "03-ronaldo-captain-gaze",
    player: "ronaldo",
    playerBadgeZh: "RONALDO #7",
    playerBadgeEn: "RONALDO #7",
    styleId: "realist",
    boardCli: "easel",
    transIn: "iris",
    aspect: "portrait",
    zh: "C罗 · 五盾军团7号队长凝视",
    en: "Ronaldo · Portugal #7 Captain's Gaze",
    subZh: "胡桃木画架 · 08 细腻写实绘画",
    subEn: "Walnut Easel · 08 Realist Painting",
    credit: "Photo: Bryan Berlin · CC BY-SA 4.0"
  },
  {
    no: "04",
    slug: "04-messi-sky-celebration",
    player: "messi",
    playerBadgeZh: "MESSI #10",
    playerBadgeEn: "MESSI #10",
    styleId: "watercolor",
    boardCli: "tape",
    transIn: "ink-bloom",
    aspect: "portrait",
    zh: "梅西 · 双手指天经典庆祝",
    en: "Messi · Iconic Skyward Celebration",
    subZh: "美纹纸木画板 · 06 透明水彩与彩墨",
    subEn: "Masking-Taped Board · 06 Watercolor Wash",
    credit: "Photo: Bryan Berlin · CC BY-SA 4.0"
  },
  {
    no: "05",
    slug: "05-ronaldo-siuuu-leap",
    player: "ronaldo",
    playerBadgeZh: "RONALDO #7",
    playerBadgeEn: "RONALDO #7",
    styleId: "ink-wash",
    boardCli: "clip",
    transIn: "ink-bloom",
    aspect: "portrait",
    zh: "C罗 · 腾空跃起「SIUUU!」庆祝",
    en: "Ronaldo · Mid-Air 'SIUUU!' Celebration",
    subZh: "金属夹写生板 · 05 黑白水墨",
    subEn: "Brass Clip Board · 05 Sumi Ink Wash",
    credit: "Photo: YantsImages · CC BY-SA 4.0"
  },
  {
    no: "06",
    slug: "06-messi-barca-2005",
    player: "messi",
    playerBadgeZh: "MESSI · BARÇA",
    playerBadgeEn: "MESSI · BARÇA",
    styleId: "crayon",
    boardCli: "tape",
    transIn: "dry-brush",
    aspect: "portrait",
    zh: "梅西 · 2005 巴萨红蓝长发少年",
    en: "Messi · Young Barça Blaugrana (2005)",
    subZh: "美纹纸木画板 · 11 蜡笔与油画棒",
    subEn: "Masking-Taped Board · 11 Oil Pastel",
    credit: "Photo: Josep Tomàs · CC BY-SA 4.0"
  },
  {
    no: "07",
    slug: "07-ronaldo-ballon-dor",
    player: "ronaldo",
    playerBadgeZh: "RONALDO · CR7",
    playerBadgeEn: "RONALDO · CR7",
    styleId: "sand",
    boardCli: "auto",
    transIn: "focus",
    aspect: "portrait",
    zh: "C罗 · 伯纳乌高举金球奖",
    en: "Ronaldo · Bernabéu Golden Ballon d'Or",
    subZh: "暖光背光沙画台 · 17 灯箱沙画",
    subEn: "Warm Backlit Lightbox · 17 Sand Art",
    credit: "Photo: Anish Morarji · CC BY 2.0"
  },
  {
    no: "08",
    slug: "08-messi-wcfinal-strike",
    player: "messi",
    playerBadgeZh: "MESSI #10",
    playerBadgeEn: "MESSI #10",
    styleId: "flat",
    boardCli: "clip",
    transIn: "prism",
    aspect: "portrait",
    zh: "梅西 · 世界杯决赛左脚劲射",
    en: "Messi · World Cup Final Left-Foot Strike",
    subZh: "金属夹写生板 · 12 平涂插画与漫画",
    subEn: "Brass Clip Board · 12 Graphic Illustration",
    credit: "Photo: Agência Brasil · CC BY 3.0 br"
  },
  {
    no: "09",
    slug: "09-ronaldo-euro-leap",
    player: "ronaldo",
    playerBadgeZh: "RONALDO #7",
    playerBadgeEn: "RONALDO #7",
    styleId: "hatching",
    boardCli: "easel",
    transIn: "page-curl",
    aspect: "portrait",
    zh: "C罗 · 2016 欧洲杯逆天滞空头槌",
    en: "Ronaldo · Euro 2016 Gravity-Defying Leap",
    subZh: "胡桃木画架 · 02 钢笔密线排绘",
    subEn: "Walnut Easel · 02 Cross Hatching",
    credit: "Photo: Chensiyuan · CC BY-SA 4.0"
  },
  {
    no: "10",
    slug: "10-messi-ucl-dribble",
    player: "messi",
    playerBadgeZh: "MESSI #10",
    playerBadgeEn: "MESSI #10",
    styleId: "block-print",
    boardCli: "clean",
    transIn: "mosaic",
    aspect: "portrait",
    zh: "梅西 · 2015 欧冠决赛单骑突破",
    en: "Messi · 2015 UCL Final Solo Dribble",
    subZh: "极简原木画板 · 14 套色版画",
    subEn: "Clean Oak Board · 14 Multi-Plate Block Print",
    credit: "Photo: Biser Todorov · CC BY 3.0"
  },
  {
    no: "11",
    slug: "11-ronaldo-manutd-7",
    player: "ronaldo",
    playerBadgeZh: "RONALDO #7",
    playerBadgeEn: "RONALDO #7",
    styleId: "gongbi",
    boardCli: "tape",
    transIn: "silk-fan",
    aspect: "portrait",
    zh: "C罗 · 重返梦剧场曼联红衣7号",
    en: "Ronaldo · Old Trafford Man United #7",
    subZh: "美纹纸木画板 · 07 工笔设色与重彩",
    subEn: "Masking-Taped Board · 07 Gongbi Rich Color",
    credit: "Photo: Ardfern · CC BY-SA 4.0"
  },
  {
    no: "12",
    slug: "12-messi-miami-pink",
    player: "messi",
    playerBadgeZh: "MESSI #10",
    playerBadgeEn: "MESSI #10",
    styleId: "pastel",
    boardCli: "tape",
    transIn: "silk-fan",
    aspect: "portrait",
    zh: "梅西 · 迈阿密国际粉衣10号队长",
    en: "Messi · Inter Miami #10 Pink Kit",
    subZh: "美纹纸木画板 · 10 干粉柔绘",
    subEn: "Masking-Taped Board · 10 Soft Pastel",
    credit: "Photo: Hayden Schiff · CC BY 4.0"
  },
  {
    no: "13",
    slug: "13-ronaldo-worldcup-roar",
    player: "ronaldo",
    playerBadgeZh: "RONALDO #7",
    playerBadgeEn: "RONALDO #7",
    styleId: "charcoal",
    boardCli: "clip",
    transIn: "charcoal",
    aspect: "portrait",
    zh: "C罗 · 2022 世界杯握拳怒吼",
    en: "Ronaldo · World Cup 2022 Fist-Pump Roar",
    subZh: "金属夹写生板 · 03 黑白明暗素描",
    subEn: "Brass Clip Board · 03 Charcoal Chiaroscuro",
    credit: "Photo: Hossein Zohrevand · CC BY 4.0"
  }
];

const BESPOKE_TRANSITIONS = [
  { no: "01", id: "ink-bloom", zh: "水墨晕染", en: "Ink Bloom", descZh: "数处不规则墨团自然洇开汇成全画", descEn: "Organic ink blots spread and merge across paper" },
  { no: "02", id: "dry-brush", zh: "干刷横扫", en: "Dry Brush", descZh: "带细碎飞白刷毛的边缘横掠纸面", descEn: "Feathered dry-bristle edge sweeps the frame" },
  { no: "03", id: "page-curl", zh: "纸角翻页", en: "Page Curl", descZh: "卷边高光与立体投影斜向翻过画页", descEn: "Angled curling sheet with soft cast shadow" },
  { no: "04", id: "iris", zh: "镜头光圈", en: "Iris Aperture", descZh: "六边形机械光圈自人物主体中央展开", descEn: "Hexagonal aperture opens from subject center" },
  { no: "05", id: "mosaic", zh: "马赛克显影", en: "Mosaic", descZh: "错落色块依次浮现拼合为清晰成画", descEn: "Staggered color tiles assemble into the piece" },
  { no: "06", id: "ribbon", zh: "绸带交错", en: "Ribbon", descZh: "相邻横带从左右两侧交错滑入合拢", descEn: "Interleaved horizontal bands slide from left & right" },
  { no: "07", id: "prism", zh: "棱镜折光", en: "Prism", descZh: "斜向光带掠过并伴随微妙光谱色散", descEn: "Diagonal light band with subtle chromatic split" },
  { no: "08", id: "focus", zh: "柔焦显影", en: "Soft Focus", descZh: "从纸面淡入朦胧色影再缓缓合焦清晰", descEn: "Hazy paper silhouette pulls smoothly into focus" },
  { no: "09", id: "charcoal", zh: "炭粉聚散", en: "Charcoal Dust", descZh: "细微颗粒在纸面聚拢直至显出全貌", descEn: "Fine charcoal grains coalesce onto paper" },
  { no: "10", id: "silk-fan", zh: "折扇开合", en: "Silk Fan", descZh: "扇骨自底边旋开依次露出画作", descEn: "Radial fan ribs unfold gracefully from base" }
];

const FFMPEG_TRANSITIONS = [
  ["11", "交叉淡化", "fade"], ["12", "向左擦除", "wipeleft"], ["13", "向右擦除", "wiperight"], ["14", "向上擦除", "wipeup"],
  ["15", "向下擦除", "wipedown"], ["16", "左推画面", "slideleft"], ["17", "右推画面", "slideright"], ["18", "上推画面", "slideup"],
  ["19", "下推画面", "slidedown"], ["20", "圆形裁切", "circlecrop"], ["21", "矩形裁切", "rectcrop"], ["22", "色距溶合", "distance"],
  ["23", "淡经黑场", "fadeblack"], ["24", "淡经白场", "fadewhite"], ["25", "旋转扫盘", "radial"], ["26", "柔边左移", "smoothleft"],
  ["27", "柔边右移", "smoothright"], ["28", "柔边上移", "smoothup"], ["29", "柔边下移", "smoothdown"], ["30", "圆窗张开", "circleopen"],
  ["31", "圆窗收拢", "circleclose"], ["32", "中线左右开门", "vertopen"], ["33", "两侧左右合门", "vertclose"], ["34", "中线上下开帘", "horzopen"],
  ["35", "两侧上下合帘", "horzclose"], ["36", "颗粒溶解", "dissolve"], ["37", "像素聚焦", "pixelize"], ["38", "斜线左上", "diagtl"],
  ["39", "斜线右上", "diagtr"], ["40", "斜线左下", "diagbl"], ["41", "斜线右下", "diagbr"], ["42", "横切片向左", "hlslice"],
  ["43", "横切片向右", "hrslice"], ["44", "纵切片向上", "vuslice"], ["45", "纵切片向下", "vdslice"], ["46", "横向动感模糊", "hblur"],
  ["47", "灰阶显色", "fadegrays"], ["48", "左上角擦除", "wipetl"], ["49", "右上角擦除", "wipetr"], ["50", "左下角擦除", "wipebl"],
  ["51", "右下角擦除", "wipebr"], ["52", "横向挤压", "squeezeh"], ["53", "纵向挤压", "squeezev"], ["54", "推镜放大", "zoomin"],
  ["55", "快速淡化", "fadefast"], ["56", "缓慢淡化", "fadeslow"], ["57", "左向风痕", "hlwind"], ["58", "右向风痕", "hrwind"],
  ["59", "上向风痕", "vuwind"], ["60", "下向风痕", "vdwind"], ["61", "向左覆盖", "coverleft"], ["62", "向右覆盖", "coverright"],
  ["63", "向上覆盖", "coverup"], ["64", "向下覆盖", "coverdown"], ["65", "向左揭幕", "revealleft"], ["66", "向右揭幕", "revealright"],
  ["67", "向上揭幕", "revealup"], ["68", "向下揭幕", "revealdown"]
];

const ANATOMY_SEGMENTS = [
  {
    time: "0.0s — 0.5s",
    zhTitle: "成画进场",
    enTitle: "Entrance Reveal",
    zhDetail: "从 10 种绘画专用效果与 58 种 FFmpeg 转场中择一（或随机抽取），将最终完成态画作优雅引入画面，无任何画具音效干扰。",
    enDetail: "Reveals the finished artwork cleanly using 1 of 10 bespoke painting effects or 58 FFmpeg presets—kept completely free of tool sounds."
  },
  {
    time: "0.5s — 1.7s",
    zhTitle: "成画定格 · 1.2s",
    enTitle: "Finished Hold · 1.2s",
    zhDetail: "在进入绘制过程前先静止展示 1.2 秒完整画作，让观众看清整体光影、媒材肌理与构图。",
    enDetail: "Holds the clean finished piece for 1.2 seconds so viewers absorb the likeness, palette, and medium before the first mark begins."
  },
  {
    time: "1.7s — 2.3s",
    zhTitle: "翻回空白底纸",
    enTitle: "Return to Ground",
    zhDetail: "通过同一转场（或通过 --transition-out 指定的独立退场效果）翻回暖白棉纸、熟褐画布、木版或暖光灯箱底材。",
    enDetail: "Transitions smoothly back to the actual drawing ground—warm rag paper, raw umber canvas, dark woodblock, or backlit sand glass."
  },
  {
    time: "2.3s — 24.0s",
    zhTitle: "前三笔原声慢画 → 钢琴独奏延时成画",
    enTitle: "3 Foley Marks → Solo Piano Time-Lapse",
    zhDetail: "前 3 笔以慢动作清晰呈现笔尖轨迹，精准对齐落纸与抬笔的真实录音；第 4 笔起收去画具声，由本机实时合成的轻柔钢琴伴随千百笔层叠直至完画定格。",
    enDetail: "Marks 1–3 draw slowly with contact-accurate foley that cuts on lift; from mark 4 onward, locally synthesized solo piano carries the accelerated build."
  }
];

const I18N = {
  zh: {
    brandSub: "逐笔绘画工作室",
    navFilms: "27 部放映厅",
    navTaxonomy: "20 种画法",
    navImpasto: "3D 厚涂",
    navTransitions: "68 种转场",
    navStudio: "提示词工坊",
    themePaper: "宣纸",
    themeDark: "暗房",
    eyebrow: "LOCAL ALGORITHMIC ATELIER · 纯本地逐笔渲染引擎",
    heroTitleHtml: "把一张照片，<br>画成一部 <em>24 秒</em>的有声短片。",
    heroLead: "观众先凝视成画，再随转场回到空白纸面，看第一笔落在哪里、色彩如何层层叠起。ArtInMotion 直接从原照计算轮廓、色相与笔触走向，无需生图大模型或 API Key，同步导出带配乐的 MP4 与干净成画。",
    ctaStudio: "定制专属提示词与命令",
    ctaFilms: "进入双馆有声放映室 (27 部)",
    m1Label: "手绘媒材预设",
    m2Label: "进退场转场效果",
    m3Label: "大模型与云端依赖",
    m4Label: "标准声画叙事成片",
    soundMuted: "点击开启原声 · 听落笔与钢琴",
    soundUnmuted: "原声播放中 · 落笔与钢琴",
    anatomyHeader: "一部 24 秒短片的声画时间轴（点击分段查看设计细节）",
    anatomyHint: "默认 30 FPS · 长边 960px（可调至 1920px）",
    sec2Index: "EXHIBITION I · DARK SCREENING ROOM",
    sec2Title: "二十七部有声完整版 · 双馆暗房放映厅",
    sec2Desc: "特设「绿茵双骄 · 梅西 × C罗传奇画廊」与「单像 14 种媒材对照」两大展厅。点击任意画作即可播放 24 秒落笔与钢琴原声成片，或一键将同款画风与木纹画板送入工坊。",
    wingLegendsTitle: "绿茵双骄特展 · 梅西 × C罗",
    wingLegendsCount: "13 部有声成片",
    wingLegendsSub: "1 幅双骄同框厚涂镇馆作 + 梅西 6 大瞬间 + C罗 6 大瞬间，横跨 13 种手绘媒材与木画板",
    wingMuskTitle: "单像媒材对照 · 同一肖像 14 种画法",
    wingMuskCount: "14 部有声成片",
    wingMuskSub: "同一张肖像在 14 种底纸、颜料与画具上的纯粹质感对照实验",
    legFilterAll: "全部典藏 (13)",
    legFilterDuo: "双骄同框 (1)",
    legFilterMessi: "梅西 · Messi (6)",
    legFilterRonaldo: "C罗 · Ronaldo (6)",
    featuredKicker: "CENTERPIECE · 绿茵双骄镇馆之作",
    filterAll: "全部展品 (14)",
    filterLine: "素描与刀刻 (3)",
    filterInk: "水墨与丹青 (2)",
    filterPaint: "油彩与粉蜡 (5)",
    filterConstruct: "拼贴与构成 (4)",
    playFilmBtn: "▶ 播放有声成片",
    useStyleBtn: "选用此画风",
    creditLegendsHtml: "「绿茵双骄特展」13 部影片改编自 Wikimedia Commons 自由版权摄影（摄影师：Fanny Schertzer、Bryan Berlin、YantsImages、Josep Tomàs、Anish Morarji、Agência Brasil、Chensiyuan、Biser Todorov、Ardfern、Hayden Schiff、Hossein Zohrevand），衍生画作依 <a href='https://creativecommons.org/licenses/by-sa/4.0/' target='_blank' rel='noopener'>CC BY / CC BY-SA 4.0</a> 协议署名分享。",
    creditMuskHtml: "「单像媒材对照」14 部影片改编自 Duncan.Hull / The Royal Society 拍摄的 <a href='https://commons.wikimedia.org/wiki/File:Elon_Musk_Royal_Society.jpg' target='_blank' rel='noopener'>Elon Musk 肖像原照</a>，衍生作品依 <a href='https://creativecommons.org/licenses/by-sa/4.0/' target='_blank' rel='noopener'>CC BY-SA 4.0</a> 协议分享。",
    creditFilmsHtml: "衍生有声绘画短片均基于 Wikimedia Commons 开放授权摄影纯本地算法绘制，依 <a href='https://creativecommons.org/licenses/by-sa/4.0/' target='_blank' rel='noopener'>CC BY-SA 4.0</a> 协议分享。",
    sec3Index: "CATALOGUE II · COMPLETE 20-MEDIA TAXONOMY",
    sec3Title: "一图二十画 · 全媒材色卡与笔触图谱",
    sec3Desc: "左侧可按章节跳看 20 种画风四宫格同步落笔，下方完整收录 01–20 号预设的真实底纸色卡、画具与技法特征。点击任意色卡即可送入下方工坊。",
    atlasModeVideo: "四宫格动态对照 (30s)",
    atlasModeSheet: "20 格高清静态总览",
    chapterHeading: "点击时间轴直达对应四宫格画风组",
    chapterSub: "喜欢哪一幅的质感，直接记下编号（如 04 号彩铅、17 号灯箱沙画）即可在助手或命令行中使用。",
    ch1: "轮廓线描 · 密线排绘 · 黑白素描 · 彩铅细绘",
    ch2: "黑白水墨 · 透明水彩 · 工笔重彩 · 细腻写实",
    ch3: "厚涂油画 · 干粉柔绘 · 蜡笔油画棒 · 平涂插画",
    ch4: "木刻剪影 · 套色版画 · 点描网点 · 拼贴镶嵌",
    ch5: "灯箱沙画 · 流体拓纹 · 几何切面 · 像素字符",
    sec4Index: "SPECIAL FEATURE III · WEBGL 3D IMPASTO",
    sec4Title: "经典竖屏 3D 厚涂油画 · 光学放大镜检视",
    sec4Desc: "独立渲染引擎 paint_video.py 在熟褐色画布上逐层堆叠六层曲线笔触，实时计算油彩厚度高光与镜头推拉。",
    loupeHint: "移动鼠标（或手指滑动）透过 2.6× 放大镜检视立体油彩笔触肌理",
    impastoSubTitle: "从眼部特写到全景揭晓的电影运镜",
    impastoSpec1: "熟褐色画布打底，六层由宽到细的弯曲猪鬃画笔路径逐笔堆叠立体厚度。",
    impastoSpec2: "WebGL 2 着色器实时解算油彩边缘高光与凹槽阴影，静态 PNG 同样保留微距肌理。",
    impastoSpec3: "前 14 笔慢速落笔配刷涂声，镜头推近双眸刻画神采，附带实时笔数计数与收尾全景定格。",
    impastoTryBtn: "在工坊中载入「竖屏 3D 油画」提示词 →",
    sec5Index: "ATLAS IV · 68 ENTRANCE & EXIT TRANSITIONS",
    sec5Title: "六十八种进退场转场选片册",
    sec5Desc: "包含 10 种专为纸本与绘画设计的定制转场，以及 58 种跨版本编号一致的 FFmpeg 转场。点击任意转场即可设为工坊开场效果。",
    transVideo10: "10 种绘画专用转场单屏精看 (31s)",
    transVideo68: "68 种全量动态选片册 (60s)",
    ffmpegDrawerTitle: "FFmpeg 内置转场速查（编号 11–68 · 点击即选）",
    searchPlaceholder: "搜索编号、中文名或英文 ID（如 ink / 翻页 / 30）...",
    sec6Index: "ATELIER V · INTERACTIVE PROMPT & CLI STUDIO",
    sec6Title: "定制你的第一条画作短片",
    sec6Desc: "点选画风、开场转场与声音细节，右侧实时生成可直接发送给 AI 助手（Codex / Claude Code / Antigravity）的提示词与本地 Python 命令。",
    lblEngine: "渲染模式",
    engPortable: "通用 20 画风渲染器 (render_art.py)",
    engClassic: "竖屏 3D 厚涂油画电影 (paint_video.py)",
    lblStyle: "画风预设 (01–20)",
    lblTransIn: "进场转场 (--transition)",
    lblTransOut: "退场转场 (--transition-out)",
    optRandom: "随机挑选 (默认)",
    optSameIn: "与进场保持一致",
    lblBoard: "画板装裱 (--board)",
    brdAuto: "自动适配木纹画板 (默认)",
    brdTape: "美纹纸胶带木画板 (tape)",
    brdClip: "金属写生夹木画板 (clip)",
    brdEasel: "深色木质画架托槽 (easel)",
    brdClean: "极简无夹木画板 (clean)",
    brdNone: "无画板铺满全屏 (--no-board)",
    lblOrientation: "横竖屏画幅 (--orientation)",
    oriAuto: "跟随原图自然方向 (默认)",
    oriLandscape: "横屏 16:9 画板 (landscape)",
    oriPortrait: "竖屏 9:16 画板 (portrait)",
    oriSquare: "方屏 1:1 画板 (square)",
    lblAspect: "图片比例 (--aspect)",
    aspOrig: "保留原图完整比例 (默认)",
    lblDuration: "影片总时长",
    lblAudio: "声音与配乐方案",
    audDefault: "前三笔落纸原声 + 钢琴独奏 (推荐)",
    audFoleyOnly: "仅保留落笔声 (--no-music)",
    audSilent: "导出纯静音视频 (--silent)",
    lblExtras: "画面细节微调",
    extSlowOpen: "6 秒慢画开场",
    extRichPigment: "加浓颜料 (1.25×)",
    extHD: "高清 1920px",
    extHideTool: "隐藏笔尖工具",
    extNoPreview: "跳过成画预览直接起笔",
    outPromptLabel: "AI 助手提示词 · 附照片直接发送",
    outCliLabel: "本地 Python CLI 命令 · 可精确复现",
    copyBtn: "复制",
    copiedToast: "已复制到剪贴板",
    styleLoadedToast: "已载入画风至下方提示词工坊：",
    transLoadedToast: "已设定进场转场：",
    lbPrev: "← 上一部",
    lbNext: "下一部 →",
    lbUseStyle: "用此画风生成提示词",
    lbClose: "关闭 Esc",
    footerCopy: "ArtInMotion · 纯本地逐笔绘画与有声短片工作室。零大模型、零 API Key。"
  },
  en: {
    brandSub: "Stroke-by-Stroke Studio",
    navFilms: "27 Sound Films",
    navTaxonomy: "20 Media",
    navImpasto: "3D Impasto",
    navTransitions: "68 Transitions",
    navStudio: "Prompt Studio",
    themePaper: "Paper",
    themeDark: "Dark",
    eyebrow: "LOCAL ALGORITHMIC ATELIER · ZERO MODELS · ZERO API KEYS",
    heroTitleHtml: "Turn a photograph into<br>a <em>24-second</em> drawing film.",
    heroLead: "Open on the finished artwork, transition back to blank paper, and watch the first stroke build into layered color. ArtInMotion computes contours, palette, and brushwork locally—exporting both a scored MP4 and a clean still.",
    ctaStudio: "Open Prompt & CLI Studio",
    ctaFilms: "Enter Screening Room (27 Films)",
    m1Label: "Tactile Drawing Media",
    m2Label: "Entrance & Exit Effects",
    m3Label: "Cloud Models or Keys",
    m4Label: "Scored Cinema Arc",
    soundMuted: "Click for Sound · Foley & Piano",
    soundUnmuted: "Sound On · Foley & Solo Piano",
    anatomyHeader: "Acoustic & Visual Architecture of a 24s Film (Click any phase)",
    anatomyHint: "Default 30 FPS · 960px long edge (up to 1920px HD)",
    sec2Index: "EXHIBITION I · DARK SCREENING ROOM",
    sec2Title: "27 Full-Length Sound Films · Two Gallery Wings",
    sec2Desc: "Explore the Football Legends Wing (Messi × Cristiano Ronaldo across 13 media & wooden boards) or the 14-Media Single-Portrait Study. Click any artwork to play the scored 24-second MP4 or load its exact preset into the Studio.",
    wingLegendsTitle: "Football Legends · Messi × Ronaldo",
    wingLegendsCount: "13 Sound Films",
    wingLegendsSub: "1 iconic rivalry oil centerpiece + 6 Messi moments + 6 Ronaldo moments across 13 media & studio boards",
    wingMuskTitle: "Single-Portrait Study · 14 Media",
    wingMuskCount: "14 Sound Films",
    wingMuskSub: "One reference portrait compared side-by-side across 14 distinct grounds, pigments & tools",
    legFilterAll: "All Legends (13)",
    legFilterDuo: "Iconic Duo (1)",
    legFilterMessi: "Lionel Messi (6)",
    legFilterRonaldo: "Cristiano Ronaldo (6)",
    featuredKicker: "CENTERPIECE · RIVALRY MASTERWORK",
    filterAll: "All Works (14)",
    filterLine: "Line & Relief (3)",
    filterInk: "Ink & Gongbi (2)",
    filterPaint: "Paint & Pastel (5)",
    filterConstruct: "Collage & Construct (4)",
    playFilmBtn: "▶ Watch with Sound",
    useStyleBtn: "Use Preset",
    creditLegendsHtml: "The 13 Legends Wing films adapt Wikimedia Commons photographs by Fanny Schertzer, Bryan Berlin, YantsImages, Josep Tomàs, Anish Morarji, Agência Brasil, Chensiyuan, Biser Todorov, Ardfern, Hayden Schiff & Hossein Zohrevand under <a href='https://creativecommons.org/licenses/by-sa/4.0/' target='_blank' rel='noopener'>CC BY / CC BY-SA 4.0</a>.",
    creditMuskHtml: "These 14 films adapt <a href='https://commons.wikimedia.org/wiki/File:Elon_Musk_Royal_Society.jpg' target='_blank' rel='noopener'>Elon Musk Royal Society.jpg</a> by Duncan.Hull / The Royal Society under <a href='https://creativecommons.org/licenses/by-sa/4.0/' target='_blank' rel='noopener'>CC BY-SA 4.0</a>.",
    creditFilmsHtml: "All sound drawing films adapt open-licensed Wikimedia Commons photography under <a href='https://creativecommons.org/licenses/by-sa/4.0/' target='_blank' rel='noopener'>CC BY-SA 4.0</a>.",
    sec3Index: "CATALOGUE II · COMPLETE 20-MEDIA TAXONOMY",
    sec3Title: "One Reference, 20 Ways to Draw It",
    sec3Desc: "Jump through chapters of the 4-up comparison reel on the left, or explore all 20 tactile grounds, tools, and preset IDs below. Click any card to load it into the Studio.",
    atlasModeVideo: "4-Up Comparison Film (30s)",
    atlasModeSheet: "20-Preset Still Contact Sheet",
    chapterHeading: "Jump to 4-Up Comparison Chapters",
    chapterSub: "Spot a texture you love? Note its two-digit number (e.g., 04 colored-pencil or 17 sand) for any prompt or CLI command.",
    ch1: "Contour · Hatching · Charcoal · Colored Pencil",
    ch2: "Ink Wash · Watercolor · Gongbi · Realist",
    ch3: "Impasto · Soft Pastel · Crayon · Flat Illustration",
    ch4: "Woodcut · Block Print · Stipple · Collage",
    ch5: "Backlit Sand · Marbling · Facets · Pixel Art",
    sec4Index: "SPECIAL FEATURE III · WEBGL 3D IMPASTO",
    sec4Title: "Classic Vertical 3D Oil & Optical Loupe",
    sec4Desc: "The standalone paint_video.py engine computes six curved stroke layers over raw umber canvas with specular bristle relief and camera choreography.",
    loupeHint: "Move cursor (or drag finger) to inspect 3D impasto ridges at 2.6× magnification",
    impastoSubTitle: "Close-Up Eye Detail to Full Portrait Pullback",
    impastoSpec1: "Six progressive layers of curved bristle strokes over a warm raw-umber canvas.",
    impastoSpec2: "WebGL 2 specular ridge lighting preserved in both 9:16 cinema MP4 and high-res still PNG.",
    impastoSpec3: "14 slow opening strokes with brush foley, live stroke counter, eye close-up, and final reveal.",
    impastoTryBtn: "Load Classic 3D Oil into Prompt Studio →",
    sec5Index: "ATLAS IV · 68 ENTRANCE & EXIT TRANSITIONS",
    sec5Title: "68 Curated Transitions Atlas",
    sec5Desc: "10 bespoke transitions crafted specifically for paper & pigment, plus 58 numbered FFmpeg xfade presets. Click any transition to apply it to the Studio.",
    transVideo10: "10 Bespoke Painting Transitions (31s)",
    transVideo68: "Complete 68-Transition Atlas (60s)",
    ffmpegDrawerTitle: "FFmpeg Presets Index (No. 11–68 · Click to select)",
    searchPlaceholder: "Filter by number or name (e.g. wipe, circle, 30)...",
    sec6Index: "ATELIER V · INTERACTIVE PROMPT & CLI STUDIO",
    sec6Title: "Compose Your Film Prompt & CLI",
    sec6Desc: "Pick a medium, transition, and acoustic profile to generate a ready-to-paste AI assistant prompt (Codex / Claude Code / Antigravity) alongside the exact Python CLI command.",
    lblEngine: "Renderer Mode",
    engPortable: "20-Style Portable Renderer (render_art.py)",
    engClassic: "Vertical 3D Classic Oil Cinema (paint_video.py)",
    lblStyle: "Drawing Preset (01–20)",
    lblTransIn: "Entrance (--transition)",
    lblTransOut: "Exit (--transition-out)",
    optRandom: "Random per film (Default)",
    optSameIn: "Match entrance transition",
    lblBoard: "Drawing Board (--board)",
    brdAuto: "Auto Studio Wood Board (Default)",
    brdTape: "Corner Masking Tape (tape)",
    brdClip: "Brass Sketchboard Clip (clip)",
    brdEasel: "Walnut Studio Easel (easel)",
    brdClean: "Clean Wood Board (clean)",
    brdNone: "Full-Bleed No Board (--no-board)",
    lblOrientation: "Screen Orientation (--orientation)",
    oriAuto: "Match Source Orientation (Default)",
    oriLandscape: "Landscape 16:9 (landscape)",
    oriPortrait: "Portrait 9:16 (portrait)",
    oriSquare: "Square 1:1 (square)",
    lblAspect: "Image Aspect Ratio (--aspect)",
    aspOrig: "Keep Original Ratio (Default)",
    lblDuration: "Runtime",
    lblAudio: "Acoustic Profile",
    audDefault: "3 Opening Foley Marks + Solo Piano (Default)",
    audFoleyOnly: "Drawing Foley Only (--no-music)",
    audSilent: "Silent Film (--silent)",
    lblExtras: "Refinements",
    extSlowOpen: "6s Slow Opening",
    extRichPigment: "Rich Pigment (1.25×)",
    extHD: "Full HD 1920px",
    extHideTool: "Hide Active Tool",
    extNoPreview: "Skip Opening Preview",
    outPromptLabel: "AI Assistant Prompt · Attach Photo & Send",
    outCliLabel: "Local Python CLI · Deterministic & Reproducible",
    copyBtn: "Copy",
    copiedToast: "Copied to clipboard",
    styleLoadedToast: "Loaded preset into Studio: ",
    transLoadedToast: "Selected entrance transition: ",
    lbPrev: "← Previous",
    lbNext: "Next →",
    lbUseStyle: "Build Prompt with This Style",
    lbClose: "Close Esc",
    footerCopy: "ArtInMotion · Local algorithmic stroke-by-stroke drawing film studio. Zero models, zero API keys."
  }
};

/* ==========================================================================
   Application State
   ========================================================================== */

const state = {
  lang: "zh",
  theme: "paper",
  heroReelIdx: 0,
  anatomyIdx: 3,
  filmWing: "legends",
  filmFilter: "all",
  lightboxWing: "legends",
  lightboxFilmIdx: 0,
  studio: {
    engine: "portable",
    styleId: "colored-pencil",
    transIn: "random",
    transOut: "same",
    board: "auto",
    orientation: "auto",
    aspect: "original",
    seconds: "24",
    audio: "default",
    slowOpen: false,
    richPigment: false,
    hd: false,
    hideTool: false,
    noPreview: false
  }
};

const FILM_PRESETS = PRESETS.filter((p) => p.hasFilm);

function t(key) {
  return I18N[state.lang][key] || key;
}

function showToast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => el.classList.remove("show"), 2200);
}

function formatTime(sec) {
  if (!isFinite(sec) || sec < 0) return "00:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

/* ==========================================================================
   Hero Video Stage
   ========================================================================== */

function initHeroStage() {
  const video = document.getElementById("heroVideo");
  const playBtn = document.getElementById("heroPlayBtn");
  const scrubber = document.getElementById("heroScrubber");
  const timecode = document.getElementById("heroTimecode");
  const soundBtn = document.getElementById("heroSoundBtn");
  const fsBtn = document.getElementById("heroFsBtn");

  renderHeroTabs();
  loadHeroReel(0, false);

  playBtn.addEventListener("click", () => {
    if (video.paused) video.play();
    else video.pause();
  });

  video.addEventListener("play", updateHeroPlayIcon);
  video.addEventListener("pause", updateHeroPlayIcon);

  video.addEventListener("timeupdate", () => {
    if (video.duration) {
      scrubber.value = ((video.currentTime / video.duration) * 100).toFixed(2);
      timecode.textContent = `${formatTime(video.currentTime)} / ${formatTime(video.duration)}`;
    }
  });

  video.addEventListener("loadedmetadata", () => {
    timecode.textContent = `00:00 / ${formatTime(video.duration)}`;
    const viewport = video.parentElement;
    if (viewport && video.videoWidth && video.videoHeight) {
      viewport.classList.toggle("is-portrait", video.videoHeight > video.videoWidth);
    }
  });

  scrubber.addEventListener("input", () => {
    if (video.duration) {
      video.currentTime = ( parseFloat(scrubber.value) / 100 ) * video.duration;
    }
  });

  soundBtn.addEventListener("click", () => {
    video.muted = !video.muted;
    if (!video.muted && video.paused) video.play();
    updateSoundBadge();
  });

  fsBtn.addEventListener("click", () => {
    if (video.requestFullscreen) video.requestFullscreen();
    else if (video.webkitEnterFullscreen) video.webkitEnterFullscreen();
  });
}

function renderHeroTabs() {
  const wrap = document.getElementById("heroReelTabs");
  wrap.innerHTML = HERO_REELS.map((r, idx) => `
    <button type="button" class="reel-tab ${idx === state.heroReelIdx ? "active" : ""}" data-idx="${idx}">
      ${state.lang === "zh" ? r.zhTab : r.enTab}
    </button>
  `).join("");

  wrap.querySelectorAll(".reel-tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      loadHeroReel(parseInt(btn.dataset.idx, 10), true);
    });
  });
}

function loadHeroReel(idx, autoPlay) {
  state.heroReelIdx = idx;
  const reel = HERO_REELS[idx];
  const video = document.getElementById("heroVideo");
  const caption = document.getElementById("heroCaption");
  const viewport = video.parentElement;
  if (viewport) {
    viewport.classList.toggle("is-portrait", Boolean(reel.portrait));
  }

  const wasMuted = video.muted;
  video.src = reel.src;
  video.muted = wasMuted;
  caption.textContent = state.lang === "zh" ? reel.zhCaption : reel.enCaption;

  document.querySelectorAll("#heroReelTabs .reel-tab").forEach((b, i) => {
    b.classList.toggle("active", i === idx);
  });

  video.play().catch(() => {
    if (autoPlay) {
      video.muted = true;
      updateSoundBadge();
      video.play().catch(() => {});
    }
  });
  updateHeroPlayIcon();
  updateSoundBadge();
}

function updateHeroPlayIcon() {
  const video = document.getElementById("heroVideo");
  const btn = document.getElementById("heroPlayBtn");
  btn.innerHTML = video.paused
    ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`
    : `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M6 5h4v14H6zm8 0h4v14h-4z"/></svg>`;
}

function updateSoundBadge() {
  const video = document.getElementById("heroVideo");
  const soundBtn = document.getElementById("heroSoundBtn");
  const label = document.getElementById("heroSoundLabel");
  soundBtn.classList.toggle("unmuted", !video.muted);
  label.textContent = video.muted ? t("soundMuted") : t("soundUnmuted");
}

/* ==========================================================================
   24-Second Anatomy Timeline
   ========================================================================== */

function renderAnatomy() {
  const bar = document.getElementById("anatomyBar");
  const detail = document.getElementById("anatomyDetail");

  bar.innerHTML = ANATOMY_SEGMENTS.map((seg, i) => `
    <button type="button" class="anatomy-seg ${i === state.anatomyIdx ? "active" : ""}" data-idx="${i}">
      <span class="seg-time">${seg.time}</span>
      <span class="seg-name">${state.lang === "zh" ? seg.zhTitle : seg.enTitle}</span>
    </button>
  `).join("");

  const active = ANATOMY_SEGMENTS[state.anatomyIdx];
  detail.textContent = state.lang === "zh" ? active.zhDetail : active.enDetail;

  bar.querySelectorAll(".anatomy-seg").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.anatomyIdx = parseInt(btn.dataset.idx, 10);
      renderAnatomy();
    });
  });
}

/* ==========================================================================
   Dual-Wing Full-Length Sound Films Screening Room & Lightbox
   ========================================================================== */

function renderFilmWings() {
  const wrap = document.getElementById("filmWingBar");
  if (!wrap) return;
  const wings = [
    {
      key: "legends",
      title: t("wingLegendsTitle"),
      count: t("wingLegendsCount"),
      sub: t("wingLegendsSub")
    },
    {
      key: "musk",
      title: t("wingMuskTitle"),
      count: t("wingMuskCount"),
      sub: t("wingMuskSub")
    }
  ];

  wrap.innerHTML = wings.map((w) => `
    <button type="button" role="tab" aria-selected="${state.filmWing === w.key}" class="wing-btn ${state.filmWing === w.key ? "active" : ""}" data-wing="${w.key}">
      <div class="wing-top">
        <span class="wing-title">${w.title}</span>
        <span class="wing-count">${w.count}</span>
      </div>
      <div class="wing-sub">${w.sub}</div>
    </button>
  `).join("");

  wrap.querySelectorAll(".wing-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (state.filmWing === btn.dataset.wing) return;
      state.filmWing = btn.dataset.wing;
      state.filmFilter = "all";
      renderFilmWings();
      renderFilmFilters();
      renderFilmsGrid();
    });
  });
}

function renderFilmFilters() {
  const filters = state.filmWing === "legends"
    ? [
        { key: "all", label: t("legFilterAll") },
        { key: "duo", label: t("legFilterDuo") },
        { key: "messi", label: t("legFilterMessi") },
        { key: "ronaldo", label: t("legFilterRonaldo") }
      ]
    : [
        { key: "all", label: t("filterAll") },
        { key: "line", label: t("filterLine") },
        { key: "ink", label: t("filterInk") },
        { key: "paint", label: t("filterPaint") },
        { key: "construct", label: t("filterConstruct") }
      ];

  const wrap = document.getElementById("filmFilterBar");
  wrap.innerHTML = filters.map((f) => `
    <button type="button" class="filter-chip ${state.filmFilter === f.key ? "active" : ""}" data-filter="${f.key}">
      ${f.label}
    </button>
  `).join("");

  wrap.querySelectorAll(".filter-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.filmFilter = btn.dataset.filter;
      renderFilmFilters();
      renderFilmsGrid();
    });
  });
}

function updateFilmsAttribution() {
  const note = document.getElementById("creditFilmsNote");
  if (!note) return;
  note.innerHTML = state.filmWing === "legends" ? t("creditLegendsHtml") : t("creditMuskHtml");
}

function renderFilmsGrid() {
  const grid = document.getElementById("filmsGrid");
  updateFilmsAttribution();

  if (state.filmWing === "legends") {
    const items = state.filmFilter === "all"
      ? LEGEND_FILMS
      : LEGEND_FILMS.filter((item) => item.player === state.filmFilter);

    grid.innerHTML = items.map((item) => {
      const idx = LEGEND_FILMS.findIndex((lf) => lf.slug === item.slug);
      const preset = PRESETS.find((p) => p.id === item.styleId) || PRESETS[0];
      const title = state.lang === "zh" ? item.zh : item.en;
      const sub = state.lang === "zh" ? item.subZh : item.subEn;
      const presetName = state.lang === "zh" ? preset.zh : preset.en;
      const badge = state.lang === "zh" ? item.playerBadgeZh : item.playerBadgeEn;

      if (item.player === "duo") {
        const story = state.lang === "zh" ? item.storyZh : item.storyEn;
        return `
          <article class="film-card legend-featured">
            <div class="film-thumb-wrap" data-open-legend="${idx}">
              <img src="./demo/legends/previews/${item.slug}.webp?v=2" alt="${title}" loading="eager">
              <div class="film-play-veil">
                <span class="play-pill">${t("playFilmBtn")}</span>
                <span style="font-family:var(--font-mono);font-size:11px;color:#f2ede4;">24s · AAC · 960p</span>
              </div>
            </div>
            <div class="legend-featured-info">
              <div class="legend-kicker">
                <span class="player-dot duo"></span>
                <span>${t("featuredKicker")}</span>
              </div>
              <h3 class="legend-featured-title">${title}</h3>
              <p class="legend-featured-desc">${story}</p>
              <div class="legend-specs">
                <span class="legend-spec-pill">NO. ${preset.no} · ${presetName}</span>
                <span class="legend-spec-pill">--board ${item.boardCli}</span>
                <span class="legend-spec-pill">--transition ${item.transIn}</span>
                <span class="legend-spec-pill">${item.credit}</span>
              </div>
              <div class="film-actions" style="margin-top:6px;">
                <button type="button" class="film-btn primary" data-open-legend="${idx}">${t("playFilmBtn")}</button>
                <button type="button" class="film-btn" data-select-legend="${idx}">${t("useStyleBtn")}</button>
              </div>
            </div>
          </article>
        `;
      }

      return `
        <article class="film-card">
          <div class="film-card-meta-top">
            <span class="player-tag">
              <span class="player-dot ${item.player}"></span>
              <span>${badge}</span>
            </span>
            <span class="ground-badge">
              <span class="ground-dot" style="background:${preset.ground}"></span>
              <span>${preset.no} · ${presetName}</span>
            </span>
          </div>
          <div class="film-thumb-wrap legend-thumb" data-open-legend="${idx}">
            <img src="./demo/legends/previews/${item.slug}.webp?v=2" alt="${title}" loading="lazy">
            <div class="film-play-veil">
              <span class="play-pill">${t("playFilmBtn")}</span>
              <span style="font-family:var(--font-mono);font-size:11px;color:#f2ede4;">24s · AAC</span>
            </div>
          </div>
          <div class="film-card-body">
            <div class="film-title-row">
              <span class="film-name">${title}</span>
            </div>
            <div class="film-subnote">${sub}</div>
            <div class="film-actions">
              <button type="button" class="film-btn primary" data-open-legend="${idx}">${t("playFilmBtn")}</button>
              <button type="button" class="film-btn" data-select-legend="${idx}">${t("useStyleBtn")}</button>
            </div>
          </div>
        </article>
      `;
    }).join("");

    grid.querySelectorAll("[data-open-legend]").forEach((el) => {
      el.addEventListener("click", () => openLightbox("legends", parseInt(el.dataset.openLegend, 10)));
    });

    grid.querySelectorAll("[data-select-legend]").forEach((el) => {
      el.addEventListener("click", () => selectLegendPresetAndScroll(parseInt(el.dataset.selectLegend, 10)));
    });
    return;
  }

  const items = state.filmFilter === "all"
    ? FILM_PRESETS
    : FILM_PRESETS.filter((p) => p.family === state.filmFilter);

  grid.innerHTML = items.map((p) => {
    const filmIdx = FILM_PRESETS.findIndex((fp) => fp.id === p.id);
    const title = state.lang === "zh" ? p.zh : p.en;
    const tool = state.lang === "zh" ? p.toolZh : p.toolEn;
    return `
      <article class="film-card">
        <div class="film-card-meta-top">
          <span>NO. ${p.no} · ${tool}</span>
          <span class="ground-badge">
            <span class="ground-dot" style="background:${p.ground}"></span>
            <span>${p.ground}</span>
          </span>
        </div>
        <div class="film-thumb-wrap" data-open-film="${filmIdx}">
          <img src="./demo/musk-styles/previews/${p.no}-${p.id}.webp?v=5" alt="${title}" loading="lazy">
          <div class="film-play-veil">
            <span class="play-pill">${t("playFilmBtn")}</span>
            <span style="font-family:var(--font-mono);font-size:11px;color:#f2ede4;">24s · AAC</span>
          </div>
        </div>
        <div class="film-card-body">
          <div class="film-title-row">
            <span class="film-name">${title}</span>
            <span class="film-id">${p.id}</span>
          </div>
          <div class="film-actions">
            <button type="button" class="film-btn primary" data-open-film="${filmIdx}">${t("playFilmBtn")}</button>
            <button type="button" class="film-btn" data-select-style="${p.id}">${t("useStyleBtn")}</button>
          </div>
        </div>
      </article>
    `;
  }).join("");

  grid.querySelectorAll("[data-open-film]").forEach((el) => {
    el.addEventListener("click", () => openLightbox("musk", parseInt(el.dataset.openFilm, 10)));
  });

  grid.querySelectorAll("[data-select-style]").forEach((el) => {
    el.addEventListener("click", () => selectStyleAndScroll(el.dataset.selectStyle));
  });
}

function selectLegendPresetAndScroll(legendIdx) {
  const item = LEGEND_FILMS[legendIdx];
  if (!item) return;
  const p = PRESETS.find((pr) => pr.id === item.styleId);
  if (!p) return;
  state.studio.engine = "portable";
  state.studio.styleId = item.styleId;
  state.studio.board = item.boardCli || "auto";
  state.studio.transIn = item.transIn || "random";
  syncStudioForm();
  renderPresetsMatrix();
  updateStudioOutputs();
  showToast(`${t("styleLoadedToast")}${p.no} · ${state.lang === "zh" ? p.zh : p.en} (--board ${state.studio.board})`);
  document.getElementById("studio").scrollIntoView({ behavior: "smooth", block: "start" });
}

function initLightbox() {
  const modal = document.getElementById("lightbox");
  const video = document.getElementById("lightboxVideo");
  const prevBtn = document.getElementById("lbPrevBtn");
  const nextBtn = document.getElementById("lbNextBtn");
  const useBtn = document.getElementById("lbUseBtn");
  const closeBtn = document.getElementById("lbCloseBtn");

  closeBtn.addEventListener("click", closeLightbox);
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeLightbox();
  });

  prevBtn.addEventListener("click", () => {
    const list = state.lightboxWing === "legends" ? LEGEND_FILMS : FILM_PRESETS;
    openLightbox(state.lightboxWing, (state.lightboxFilmIdx - 1 + list.length) % list.length);
  });

  nextBtn.addEventListener("click", () => {
    const list = state.lightboxWing === "legends" ? LEGEND_FILMS : FILM_PRESETS;
    openLightbox(state.lightboxWing, (state.lightboxFilmIdx + 1) % list.length);
  });

  useBtn.addEventListener("click", () => {
    closeLightbox();
    if (state.lightboxWing === "legends") {
      selectLegendPresetAndScroll(state.lightboxFilmIdx);
    } else {
      const p = FILM_PRESETS[state.lightboxFilmIdx];
      if (p) selectStyleAndScroll(p.id);
    }
  });

  document.addEventListener("keydown", (e) => {
    if (!modal.classList.contains("open")) return;
    if (e.key === "Escape") closeLightbox();
    if (e.key === "ArrowLeft") prevBtn.click();
    if (e.key === "ArrowRight") nextBtn.click();
  });

  // Pause background hero video when lightbox plays with sound
  video.addEventListener("play", () => {
    const heroVideo = document.getElementById("heroVideo");
    if (!heroVideo.paused) heroVideo.pause();
  });
}

function openLightbox(wing, filmIdx) {
  state.lightboxWing = wing;
  state.lightboxFilmIdx = filmIdx;
  const modal = document.getElementById("lightbox");
  const video = document.getElementById("lightboxVideo");
  const box = video.parentElement;
  const titleEl = document.getElementById("lightboxTitle");
  const metaEl = document.getElementById("lightboxMeta");

  box.classList.remove("is-landscape", "is-portrait");

  if (wing === "legends") {
    const item = LEGEND_FILMS[filmIdx];
    const preset = PRESETS.find((pr) => pr.id === item.styleId) || PRESETS[0];
    const title = state.lang === "zh" ? item.zh : item.en;
    box.classList.add(item.aspect === "landscape" ? "is-landscape" : "is-portrait");
    titleEl.textContent = `${item.no} · ${title}`;
    metaEl.textContent = `--style ${item.styleId} (${state.lang === "zh" ? preset.zh : preset.en})  ·  --board ${item.boardCli}  ·  ${item.credit}`;
    video.src = `./demo/legends/${item.slug}.mp4?v=2`;
  } else {
    const p = FILM_PRESETS[filmIdx];
    titleEl.textContent = `${p.no} · ${state.lang === "zh" ? p.zh : p.en}`;
    metaEl.textContent = `--style ${p.id}  ·  24s Sound Film`;
    video.src = `./demo/musk-styles/${p.no}-${p.id}.mp4?v=5`;
  }

  video.muted = false;
  modal.classList.add("open");
  video.play().catch(() => {});
}

function closeLightbox() {
  const modal = document.getElementById("lightbox");
  const video = document.getElementById("lightboxVideo");
  video.pause();
  video.removeAttribute("src");
  video.load();
  modal.classList.remove("open");
}

/* ==========================================================================
   20 Media Atlas & Complete Swatch Matrix
   ========================================================================== */

function initAtlasExplorer() {
  const video = document.getElementById("atlasVideo");
  const sheetImg = document.getElementById("atlasSheetImg");
  const modeVideoBtn = document.getElementById("atlasModeVideo");
  const modeSheetBtn = document.getElementById("atlasModeSheet");

  modeVideoBtn.addEventListener("click", () => {
    modeVideoBtn.classList.add("active");
    modeSheetBtn.classList.remove("active");
    video.style.display = "block";
    sheetImg.style.display = "none";
    video.play().catch(() => {});
  });

  modeSheetBtn.addEventListener("click", () => {
    modeSheetBtn.classList.add("active");
    modeVideoBtn.classList.remove("active");
    video.pause();
    video.style.display = "none";
    sheetImg.style.display = "block";
  });

  document.querySelectorAll(".chapter-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const sec = parseFloat(btn.dataset.seek);
      modeVideoBtn.click();
      video.currentTime = sec;
      video.play().catch(() => {});
      document.querySelectorAll(".chapter-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
    });
  });
}

function renderPresetsMatrix() {
  const matrix = document.getElementById("presetsMatrix");
  matrix.innerHTML = PRESETS.map((p) => {
    const selected = state.studio.engine === "portable" && state.studio.styleId === p.id;
    const title = state.lang === "zh" ? p.zh : p.en;
    const tool = state.lang === "zh" ? p.toolZh : p.toolEn;
    const note = state.lang === "zh" ? p.noteZh : p.noteEn;
    return `
      <button type="button" class="preset-tile ${selected ? "selected" : ""}" data-preset="${p.id}">
        <div class="preset-top">
          <span class="preset-no">NO. ${p.no}</span>
          <span class="preset-swatch-tag">
            <span>${tool}</span>
            <span class="swatch-chip" style="background:${p.ground}"></span>
          </span>
        </div>
        <div class="preset-title">${title}</div>
        <div class="preset-code">--style ${p.id}</div>
        <div class="preset-note">${note}</div>
      </button>
    `;
  }).join("");

  matrix.querySelectorAll(".preset-tile").forEach((tile) => {
    tile.addEventListener("click", () => selectStyleAndScroll(tile.dataset.preset));
  });
}

function selectStyleAndScroll(styleId) {
  const p = PRESETS.find((item) => item.id === styleId);
  if (!p) return;
  state.studio.engine = "portable";
  state.studio.styleId = styleId;
  syncStudioForm();
  renderPresetsMatrix();
  updateStudioOutputs();
  showToast(`${t("styleLoadedToast")}${p.no} · ${state.lang === "zh" ? p.zh : p.en}`);
  document.getElementById("studio").scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ==========================================================================
   3D Impasto Optical Loupe Magnifier
   ========================================================================== */

function initImpastoLoupe() {
  const container = document.getElementById("loupeContainer");
  const img = document.getElementById("loupeImg");
  const lens = document.getElementById("loupeLens");
  const zoom = 2.6;

  lens.style.backgroundImage = `url('${img.getAttribute("src")}')`;

  function moveLens(clientX, clientY) {
    const rect = container.getBoundingClientRect();
    const x = Math.max(0, Math.min(rect.width, clientX - rect.left));
    const y = Math.max(0, Math.min(rect.height, clientY - rect.top));

    lens.style.left = `${x}px`;
    lens.style.top = `${y}px`;
    lens.style.backgroundSize = `${rect.width * zoom}px ${rect.height * zoom}px`;

    const bgX = -(x * zoom - lens.offsetWidth / 2);
    const bgY = -(y * zoom - lens.offsetHeight / 2);
    lens.style.backgroundPosition = `${bgX}px ${bgY}px`;
  }

  container.addEventListener("mousemove", (e) => moveLens(e.clientX, e.clientY));
  container.addEventListener("touchstart", (e) => {
    container.classList.add("touching");
    if (e.touches[0]) moveLens(e.touches[0].clientX, e.touches[0].clientY);
  }, { passive: true });
  container.addEventListener("touchmove", (e) => {
    if (e.touches[0]) moveLens(e.touches[0].clientX, e.touches[0].clientY);
  }, { passive: true });
  container.addEventListener("touchend", () => container.classList.remove("touching"));

  document.getElementById("impastoTryBtn").addEventListener("click", () => {
    state.studio.engine = "classic";
    syncStudioForm();
    updateStudioOutputs();
    document.getElementById("studio").scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

/* ==========================================================================
   68 Transitions Selector & Search
   ========================================================================== */

function initTransitionsSection() {
  const video = document.getElementById("transVideo");
  const btn10 = document.getElementById("transBtn10");
  const btn68 = document.getElementById("transBtn68");
  const search = document.getElementById("xfadeSearch");

  btn10.addEventListener("click", () => {
    btn10.classList.add("active");
    btn68.classList.remove("active");
    video.src = "./demo/painting-transitions.mp4?v=2";
    video.play().catch(() => {});
  });

  btn68.addEventListener("click", () => {
    btn68.classList.add("active");
    btn10.classList.remove("active");
    video.src = "./demo/transition-atlas.mp4?v=2";
    video.play().catch(() => {});
  });

  search.addEventListener("input", () => renderFfmpegChips(search.value.trim()));
  renderBespokeTransitions();
  renderFfmpegChips("");
}

function renderBespokeTransitions() {
  const wrap = document.getElementById("bespokeTenGrid");
  wrap.innerHTML = BESPOKE_TRANSITIONS.map((tr) => {
    const selected = state.studio.transIn === tr.id;
    return `
      <button type="button" class="trans-card ${selected ? "selected" : ""}" data-trans="${tr.id}">
        <div class="trans-card-head">
          <span class="trans-title">${tr.no} · ${state.lang === "zh" ? tr.zh : tr.en}</span>
          <span class="trans-code">${tr.id}</span>
        </div>
        <div class="trans-desc">${state.lang === "zh" ? tr.descZh : tr.descEn}</div>
      </button>
    `;
  }).join("");

  wrap.querySelectorAll(".trans-card").forEach((card) => {
    card.addEventListener("click", () => applyTransitionSelection(card.dataset.trans));
  });
}

function renderFfmpegChips(query) {
  const wrap = document.getElementById("ffmpegChips");
  const q = query.toLowerCase();
  const filtered = FFMPEG_TRANSITIONS.filter(([no, zh, id]) =>
    !q || no.includes(q) || zh.includes(q) || id.toLowerCase().includes(q)
  );

  wrap.innerHTML = filtered.map(([no, zh, id]) => `
    <button type="button" class="xfade-chip ${state.studio.transIn === id ? "selected" : ""}" data-trans="${id}">
      <span><strong>${no}</strong> · ${state.lang === "zh" ? zh : id}</span>
      <code>${id}</code>
    </button>
  `).join("");

  wrap.querySelectorAll(".xfade-chip").forEach((chip) => {
    chip.addEventListener("click", () => applyTransitionSelection(chip.dataset.trans));
  });
}

function applyTransitionSelection(transId) {
  state.studio.transIn = transId;
  state.studio.noPreview = false;
  syncStudioForm();
  renderBespokeTransitions();
  renderFfmpegChips(document.getElementById("xfadeSearch").value.trim());
  updateStudioOutputs();
  showToast(`${t("transLoadedToast")}${transId}`);
}

/* ==========================================================================
   Interactive Prompt & CLI Studio
   ========================================================================== */

function initStudio() {
  populateStudioDropdowns();

  document.getElementById("stEngine").addEventListener("change", (e) => {
    state.studio.engine = e.target.value;
    syncStudioForm();
    renderPresetsMatrix();
    updateStudioOutputs();
  });

  document.getElementById("stStyle").addEventListener("change", (e) => {
    state.studio.styleId = e.target.value;
    renderPresetsMatrix();
    updateStudioOutputs();
  });

  document.getElementById("stTransIn").addEventListener("change", (e) => {
    state.studio.transIn = e.target.value;
    renderBespokeTransitions();
    renderFfmpegChips(document.getElementById("xfadeSearch").value.trim());
    updateStudioOutputs();
  });

  document.getElementById("stTransOut").addEventListener("change", (e) => {
    state.studio.transOut = e.target.value;
    updateStudioOutputs();
  });

  document.getElementById("stBoard").addEventListener("change", (e) => {
    state.studio.board = e.target.value;
    updateStudioOutputs();
  });

  document.getElementById("stOrientation").addEventListener("change", (e) => {
    state.studio.orientation = e.target.value;
    updateStudioOutputs();
  });

  document.getElementById("stAspect").addEventListener("change", (e) => {
    state.studio.aspect = e.target.value;
    updateStudioOutputs();
  });

  document.getElementById("stDuration").addEventListener("change", (e) => {
    state.studio.seconds = e.target.value;
    updateStudioOutputs();
  });

  document.getElementById("stAudio").addEventListener("change", (e) => {
    state.studio.audio = e.target.value;
    updateStudioOutputs();
  });

  document.querySelectorAll("[data-toggle-opt]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const key = btn.dataset.toggleOpt;
      state.studio[key] = !state.studio[key];
      btn.classList.toggle("active", state.studio[key]);
      updateStudioOutputs();
    });
  });

  document.getElementById("copyPromptBtn").addEventListener("click", () => {
    navigator.clipboard.writeText(document.getElementById("promptOutput").textContent);
    showToast(t("copiedToast"));
  });

  document.getElementById("copyCliBtn").addEventListener("click", () => {
    navigator.clipboard.writeText(document.getElementById("cliOutput").textContent);
    showToast(t("copiedToast"));
  });

  syncStudioForm();
  updateStudioOutputs();
}

function populateStudioDropdowns() {
  const styleSel = document.getElementById("stStyle");
  styleSel.innerHTML = PRESETS.map((p) =>
    `<option value="${p.id}">${p.no} · ${state.lang === "zh" ? p.zh : p.en} (${p.id})</option>`
  ).join("");

  const allTrans = [
    ...BESPOKE_TRANSITIONS.map((tr) => ({ no: tr.no, id: tr.id, label: state.lang === "zh" ? tr.zh : tr.en })),
    ...FFMPEG_TRANSITIONS.map(([no, zh, id]) => ({ no, id, label: state.lang === "zh" ? zh : id }))
  ];

  const transInSel = document.getElementById("stTransIn");
  transInSel.innerHTML = `<option value="random">${t("optRandom")}</option>` +
    allTrans.map((tr) => `<option value="${tr.id}">${tr.no} · ${tr.label} (${tr.id})</option>`).join("");

  const transOutSel = document.getElementById("stTransOut");
  transOutSel.innerHTML = `<option value="same">${t("optSameIn")}</option>` +
    allTrans.map((tr) => `<option value="${tr.id}">${tr.no} · ${tr.label} (${tr.id})</option>`).join("");
}

function syncStudioForm() {
  const s = state.studio;
  const isPort = s.engine === "portable";
  document.getElementById("stEngine").value = s.engine;
  document.getElementById("stStyle").value = s.styleId;
  ["stStyleField", "stBoardField", "stOrientField", "stAspectField"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.style.opacity = isPort ? "1" : "0.45";
  });
  ["stStyle", "stBoard", "stOrientation", "stAspect"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.disabled = !isPort;
  });
  document.getElementById("stTransIn").value = s.transIn;
  document.getElementById("stTransOut").value = s.transOut;
  document.getElementById("stBoard").value = s.board;
  document.getElementById("stOrientation").value = s.orientation;
  document.getElementById("stAspect").value = s.aspect;
  document.getElementById("stDuration").value = s.seconds;
  document.getElementById("stAudio").value = s.audio;

  document.querySelectorAll("[data-toggle-opt]").forEach((btn) => {
    btn.classList.toggle("active", Boolean(s[btn.dataset.toggleOpt]));
  });
}

function findTransLabel(id) {
  const b = BESPOKE_TRANSITIONS.find((x) => x.id === id);
  if (b) return state.lang === "zh" ? `${b.no} 号「${b.zh}」(${b.id})` : `${b.no} ${b.en} (${b.id})`;
  const f = FFMPEG_TRANSITIONS.find((x) => x[2] === id);
  if (f) return state.lang === "zh" ? `${f[0]} 号「${f[1]}」(${f[2]})` : `${f[0]} (${f[2]})`;
  return id;
}

function updateStudioOutputs() {
  const s = state.studio;
  const preset = PRESETS.find((p) => p.id === s.styleId) || PRESETS[3];

  let prompt = "";
  let cli = "";

  if (s.engine === "classic") {
    const secs = s.seconds === "24" ? "32.5" : s.seconds;
    if (state.lang === "zh") {
      const transText = s.noPreview
        ? "跳过开场成画预览，直接从熟褐色画布开始落笔。"
        : (s.transIn === "random"
          ? "开头先用转场展示成画，再转回画布。"
          : `开头用 ${findTransLabel(s.transIn)} 展示成画，${s.transOut !== "same" ? `再用 ${findTransLabel(s.transOut)} ` : "再"}转回熟褐色画布。`);
      const audioText = s.audio === "silent"
        ? "导出无声视频。"
        : "开头前三笔叠加刷笔声，之后保留内置钢琴配乐。";
      prompt = [
        `请用 $art-in-motion 把我附的照片做成约 ${secs} 秒的经典竖屏 3D 厚涂油画视频。`,
        `如果还没安装，请先从 https://github.com/DeaglePC/ArtInMotion 安装技能并配好依赖。`,
        transText,
        `镜头推近人物眼部刻画细节，带实时笔数计数，最后拉回展示完整肖像。${audioText}`
      ].join("\n");
    } else {
      const transText = s.noPreview
        ? "Skip the finished-art preview and start directly on the raw umber canvas."
        : (s.transIn === "random"
          ? "Open on the finished portrait before transitioning back to the canvas."
          : `Use transition ${findTransLabel(s.transIn)} for the opening preview${s.transOut !== "same" ? ` and ${findTransLabel(s.transOut)} for the exit` : ""}.`);
      const audioText = s.audio === "silent"
        ? "Export as a silent MP4."
        : "Play brush foley on the first three opening strokes, then let the piano score carry the film.";
      prompt = [
        `Use $art-in-motion to render my attached photo as a ${secs}-second classic 9:16 3D impasto oil film.`,
        `If missing, install the skill from https://github.com/DeaglePC/ArtInMotion first.`,
        transText,
        `Move the camera in on the eyes for fine detail with the live stroke counter, then pull back to reveal the full painting. ${audioText}`
      ].join("\n");
    }

    const args = [`python scripts/paint_video.py "photo.jpg" "classic_oil.mp4"`];
    if (s.seconds !== "24") args.push(`--seconds ${s.seconds}`);
    if (s.noPreview) args.push(`--no-preview`);
    else {
      if (s.transIn !== "random") args.push(`--transition ${s.transIn}`);
      if (s.transOut !== "same") args.push(`--transition-out ${s.transOut}`);
    }
    if (s.audio === "silent") args.push(`--silent`);
    cli = args.join(" ");
  } else {
    if (state.lang === "zh") {
      const boardMapZh = {
        auto: "",
        tape: "视频装裱在贴有美纹纸胶带的木纹画板上。",
        clip: "视频装裱在带金属写生夹的木纹画板上。",
        easel: "视频装裱在深色木质画架托槽上。",
        clean: "视频装裱在极简无夹木纹画板上。",
        none: "不使用画板边框，画面铺满全屏。"
      };
      const oriMapZh = {
        auto: "",
        landscape: "输出为横屏（16:9）画幅，",
        portrait: "输出为竖屏（9:16）画幅，",
        square: "输出为方屏（1:1）画幅，"
      };
      const aspectZh = s.aspect === "original"
        ? "保留原图比例"
        : `图片比例裁为 ${s.aspect}`;
      const openPart = s.noPreview
        ? "跳过开场预览，直接从空白纸面开始绘制。"
        : (s.transIn === "random"
          ? "开头先展示成画，再转回纸面。"
          : `开头用 ${findTransLabel(s.transIn)} 展示成画，${s.transOut !== "same" ? `再用 ${findTransLabel(s.transOut)} ` : "再"}转回纸面。`);
      const toolPart = s.hideTool ? "绘制过程隐藏笔尖工具。" : "绘制时让我看清画具落笔轨迹。";
      const pacePart = s.slowOpen ? "开头慢画延长到 6 秒再逐渐提速。" : "";
      const pigPart = s.richPigment ? "颜料浓度调高到 1.25，色彩更饱满。" : "";
      const hdPart = s.hd ? "输出长边设为 1920 高清分辨率。" : "";
      const audioPart = s.audio === "default"
        ? "只有前三笔配真实落笔声，之后只留钢琴独奏。"
        : (s.audio === "foley" ? "只保留绘画落笔声，不加背景音乐。" : "全片导出为静音视频。");

      prompt = [
        `请用 $art-in-motion 把我附的原照按 ${preset.no} 号「${preset.zh}」(${preset.id}) 画成 ${s.seconds} 秒的视频，${oriMapZh[s.orientation]}${aspectZh}。`,
        `如果还没安装，请先从 https://github.com/DeaglePC/ArtInMotion 安装技能并配好依赖。`,
        `${boardMapZh[s.board]}${openPart}${toolPart}${pacePart}${pigPart}${hdPart}`,
        `${audioPart}完成后给我 MP4 视频和 PNG 成画。`
      ].join("\n");
    } else {
      const boardMapEn = {
        auto: "",
        tape: "Mount the paper on a wooden drawing board with corner masking tape. ",
        clip: "Mount the paper on a wooden sketchboard with a top brass clip. ",
        easel: "Present the canvas on a studio wooden easel ledge. ",
        clean: "Mount on a clean wooden drawing board. ",
        none: "Export full-bleed without a drawing board. "
      };
      const oriMapEn = {
        auto: "",
        landscape: " in 16:9 landscape orientation,",
        portrait: " in 9:16 portrait orientation,",
        square: " in 1:1 square format,"
      };
      const aspectEn = s.aspect === "original"
        ? "keeping the original aspect ratio"
        : `cropped to ${s.aspect} aspect ratio`;
      const openPart = s.noPreview
        ? "Start directly on blank paper without an opening preview. "
        : (s.transIn === "random"
          ? "Show the finished piece first, then transition back to paper. "
          : `Open with ${findTransLabel(s.transIn)}${s.transOut !== "same" ? ` and exit via ${findTransLabel(s.transOut)}` : ""} back to paper. `);
      const toolPart = s.hideTool ? "Hide the active drawing tool. " : "Keep the drawing tool visible as it works. ";
      const pacePart = s.slowOpen ? "Spend 6 seconds on the slow opening strokes. " : "";
      const pigPart = s.richPigment ? "Raise pigment richness to 1.25. " : "";
      const hdPart = s.hd ? "Render at 1920px on the long edge. " : "";
      const audioPart = s.audio === "default"
        ? "Play foley on the first three strokes only, then let the solo piano play."
        : (s.audio === "foley" ? "Keep drawing foley only with no background music." : "Export as a silent video.");

      prompt = [
        `Use $art-in-motion to turn my attached photo into a ${s.seconds}-second film in style ${preset.no}, ${preset.en} (${preset.id}),${oriMapEn[s.orientation]} ${aspectEn}.`,
        `If the skill is missing, install it from https://github.com/DeaglePC/ArtInMotion and set up its dependencies first.`,
        `${boardMapEn[s.board]}${openPart}${toolPart}${pacePart}${pigPart}${hdPart}`.trim(),
        `${audioPart} Give me both the MP4 film and the clean PNG still.`
      ].join("\n");
    }

    const flags = [
      `python scripts/render_art.py`,
      `--input "photo.jpg"`,
      `--style ${preset.id}`,
      `--seconds ${s.seconds}`
    ];
    if (s.board === "none") flags.push(`--no-board`);
    else if (s.board !== "auto") flags.push(`--board ${s.board}`);
    if (s.orientation !== "auto") flags.push(`--orientation ${s.orientation}`);
    if (s.aspect !== "original") flags.push(`--aspect ${s.aspect}`);
    if (s.slowOpen) flags.push(`--opening-seconds 6`);
    if (s.richPigment) flags.push(`--pigment 1.25`);
    if (s.hd) flags.push(`--size 1920`);
    if (s.noPreview) flags.push(`--no-preview`);
    else {
      if (s.transIn !== "random") flags.push(`--transition ${s.transIn}`);
      if (s.transOut !== "same") flags.push(`--transition-out ${s.transOut}`);
    }
    if (s.hideTool) flags.push(`--no-tool`);
    if (s.audio === "foley") flags.push(`--no-music`);
    if (s.audio === "silent") flags.push(`--silent`);
    flags.push(`--video "output.mp4"`, `--image "output.png"`);
    cli = flags.join(" ");
  }

  document.getElementById("promptOutput").textContent = prompt;
  document.getElementById("cliOutput").textContent = cli;
}

/* ==========================================================================
   Language & Theme Switching
   ========================================================================== */

function applyLanguage() {
  document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.dataset.i18n;
    el.textContent = t(key);
  });

  document.querySelectorAll("[data-i18n-html]").forEach((el) => {
    const key = el.dataset.i18nHtml;
    el.innerHTML = t(key);
  });

  document.getElementById("xfadeSearch").placeholder = t("searchPlaceholder");
  document.getElementById("langToggleBtn").textContent = state.lang === "zh" ? "EN / 中文" : "中文 / EN";
  document.getElementById("themeToggleLabel").textContent = state.theme === "paper" ? t("themeDark") : t("themePaper");

  renderHeroTabs();
  const reel = HERO_REELS[state.heroReelIdx];
  document.getElementById("heroCaption").textContent = state.lang === "zh" ? reel.zhCaption : reel.enCaption;
  updateSoundBadge();
  renderAnatomy();
  renderFilmWings();
  renderFilmFilters();
  renderFilmsGrid();
  renderPresetsMatrix();
  renderBespokeTransitions();
  renderFfmpegChips(document.getElementById("xfadeSearch").value.trim());
  populateStudioDropdowns();
  syncStudioForm();
  updateStudioOutputs();
}

function initTopControls() {
  document.getElementById("langToggleBtn").addEventListener("click", () => {
    state.lang = state.lang === "zh" ? "en" : "zh";
    applyLanguage();
  });

  document.getElementById("themeToggleBtn").addEventListener("click", () => {
    state.theme = state.theme === "paper" ? "dark" : "paper";
    document.documentElement.setAttribute("data-theme", state.theme);
    document.getElementById("themeToggleLabel").textContent = state.theme === "paper" ? t("themeDark") : t("themePaper");
  });
}

function initInkNibTrail() {
  const canvas = document.getElementById("inkTrailCanvas");
  if (!canvas) return;
  if (!window.matchMedia("(pointer: fine)").matches || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return;
  }

  const ctx = canvas.getContext("2d");
  let dpr = Math.min(window.devicePixelRatio || 1, 2);
  let points = [];
  let rafId = 0;
  let isPressed = false;
  const maxAge = 360;

  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(window.innerWidth * dpr);
    canvas.height = Math.floor(window.innerHeight * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  resize();
  window.addEventListener("resize", resize);

  window.addEventListener("mousedown", () => { isPressed = true; });
  window.addEventListener("mouseup", () => { isPressed = false; });

  window.addEventListener("mousemove", (e) => {
    const target = e.target;
    if (target && (target.tagName === "VIDEO" || target.closest(".loupe-container"))) {
      points.push({ x: e.clientX, y: e.clientY, t: performance.now(), brk: true, pressed: isPressed });
      return;
    }
    const now = performance.now();
    const last = points[points.length - 1];
    if (last && !last.brk && Math.hypot(e.clientX - last.x, e.clientY - last.y) < 2.2) {
      return;
    }
    const overDark = state.theme === "dark" || Boolean(target && target.closest(".screening-section, .output-card, .lightbox"));
    points.push({ x: e.clientX, y: e.clientY, t: now, brk: false, pressed: isPressed, dark: overDark });
    if (points.length > 64) points.shift();
    if (!rafId) rafId = requestAnimationFrame(render);
  }, { passive: true });

  function render(now) {
    ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
    points = points.filter((p) => now - p.t < maxAge);

    if (points.length >= 2) {
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      for (let i = 1; i < points.length; i++) {
        const p0 = points[i - 1];
        const p1 = points[i];
        if (p0.brk || p1.brk) continue;
        const life = 1 - (now - p1.t) / maxAge;
        if (life <= 0) continue;

        ctx.beginPath();
        ctx.moveTo(p0.x, p0.y);
        ctx.lineTo(p1.x, p1.y);

        if (p1.pressed) {
          ctx.strokeStyle = `rgba(182, 59, 43, ${(life * 0.42).toFixed(3)})`;
          ctx.lineWidth = 0.8 + life * 1.45;
        } else if (p1.dark) {
          ctx.strokeStyle = `rgba(218, 178, 122, ${(life * 0.22).toFixed(3)})`;
          ctx.lineWidth = 0.6 + life * 0.95;
        } else {
          ctx.strokeStyle = `rgba(36, 30, 25, ${(life * 0.17).toFixed(3)})`;
          ctx.lineWidth = 0.6 + life * 0.95;
        }
        ctx.stroke();
      }
    }

    if (points.length > 0) {
      rafId = requestAnimationFrame(render);
    } else {
      rafId = 0;
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initTopControls();
  initHeroStage();
  renderAnatomy();
  renderFilmWings();
  renderFilmFilters();
  renderFilmsGrid();
  initLightbox();
  initAtlasExplorer();
  renderPresetsMatrix();
  initImpastoLoupe();
  initTransitionsSection();
  initStudio();
  initInkNibTrail();
  applyLanguage();
});
