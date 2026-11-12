// 《算法油画》：四万多笔油画笔触（gen_oil.py 由粗到细算出来）一笔一笔落在画布上。
// 每一笔拆成若干根笔毛：颜色略有差别，另画一张“颜料厚度图”，着色器按厚度打光，出厚涂的反光。
// ?n=K 静帧：画到第 K 笔（不写 = 画完）；不带参数是成片。
(async function () {
  const q = new URLSearchParams(location.search);
  const W = 1080, H = 1920, ASP = W / H, FS = 1.0;
  const DATA = await (await fetch('oil.json')).json(), S = DATA.strokes, LAY = DATA.layers, TOTAL = S.length;
  const cl = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x)), seg = (t, a, b) => cl((t - a) / (b - a)), lerp = (a, b, u) => a + (b - a) * u;
  const eio = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2, eo = x => 1 - Math.pow(1 - x, 3);

  // ---------- 一笔 = 一把笔毛 ----------
  const mk = () => { const cv = document.createElement('canvas'); cv.width = W * FS; cv.height = H * FS; const c = cv.getContext('2d'); c.setTransform(FS, 0, 0, FS, 0, 0); c.lineCap = 'round'; c.lineJoin = 'round'; return [cv, c]; };
  const [colCv, cc] = mk(), [hgtCv, hc] = mk(), [tmpC, tc] = mk(), [tmpH, th] = mk();
  function drawStroke(c, h, s, frac = 1) {
    const R = s[0], n0 = (s.length - 4) / 2; let n = Math.max(2, Math.ceil(1 + (n0 - 1) * frac));
    let sd = (s[4] * 73856093 ^ s[5] * 19349663 ^ (R * 977)) >>> 0; const rnd = () => { sd = (sd * 1664525 + 1013904223) >>> 0; return sd / 4294967296; };
    const P = []; for (let i = 0; i < n; i++) P.push([s[4 + i * 2], s[5 + i * 2]]);
    if (frac < 1) { const f = (n0 - 1) * frac - (n - 2), a = P[n - 2], b = P[n - 1]; P[n - 1] = [lerp(a[0], b[0], f), lerp(a[1], b[1], f)]; }
    const N = P.map((p, i) => { const a = P[Math.max(0, i - 1)], b = P[Math.min(n - 1, i + 1)]; let dx = b[0] - a[0], dy = b[1] - a[1]; const l = Math.hypot(dx, dy) || 1; return [-dy / l, dx / l]; });
    const nb = Math.max(3, Math.min(13, Math.round(R / 1.6))), lw = 2 * R / nb * 1.75, thick = Math.pow(Math.min(1, R / 30), 1.15), jit = .045 + .07 * Math.min(1, R / 20);
    for (let b = 0; b < nb; b++) {
      const off = (b / (nb - 1) - .5) * 2 * R * .86, l = 1 + (rnd() - .5) * jit, tint = (rnd() - .5) * 60 * jit;
      const col = `rgb(${cl(s[1] * l + tint, 0, 255) | 0},${cl(s[2] * l, 0, 255) | 0},${cl(s[3] * l - tint, 0, 255) | 0})`;
      const edge = b === 0 || b === nb - 1, g = cl(128 + ((rnd() - .5) * 170 + (edge ? 34 : 0)) * thick, 0, 255) | 0, hcol = `rgb(${g},${g},${g})`;
      const j0 = (rnd() - .5) * R * .9, j1 = (rnd() - .5) * R * .9;                          // 笔毛长短不齐
      for (const [ctx, st] of [[c, col], [h, hcol]]) {
        ctx.strokeStyle = st; ctx.lineWidth = lw; ctx.beginPath();
        for (let i = 0; i < n; i++) {
          let x = P[i][0] + N[i][0] * off, y = P[i][1] + N[i][1] * off;
          if (i === 0) { x += N[i][1] * j0; y -= N[i][0] * j0; ctx.moveTo(x, y); }
          else if (i === n - 1) { x -= N[i][1] * j1; y += N[i][0] * j1; ctx.lineTo(x, y); }
          else { const nx = P[i + 1][0] + N[i + 1][0] * off, ny = P[i + 1][1] + N[i + 1][1] * off; ctx.quadraticCurveTo(x, y, (x + nx) / 2, (y + ny) / 2); }
        }
        ctx.stroke();
      }
    }
  }
  let liveN = 0;
  function paintTo(n) {                           // 持久画布画到第 floor(n) 笔；正在画的那一笔画在临时画布上
    const k = Math.min(TOTAL, Math.floor(n)), frac = n - k;
    if (k < liveN) { cc.clearRect(0, 0, W, H); hc.clearRect(0, 0, W, H); liveN = 0; }
    for (; liveN < k; liveN++) drawStroke(cc, hc, S[liveN]);
    if (frac > .02 && k < TOTAL) {
      for (const [x, src] of [[tc, colCv], [th, hgtCv]]) { x.save(); x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, W * FS, H * FS); x.drawImage(src, 0, 0); x.restore(); }
      drawStroke(tc, th, S[k], frac); return [tmpC, tmpH];
    }
    return [colCv, hgtCv];
  }

  // ---------- 着色器：画布纹理 + 颜料厚度打光 ----------
  const gl = document.getElementById('gl').getContext('webgl2', { preserveDrawingBuffer: true, antialias: false });
  const VS = `#version 300 es
  in vec2 p; void main(){ gl_Position=vec4(p,0.,1.); }`;
  const FSRC = `#version 300 es
  precision highp float;
  uniform vec2 uRes; uniform sampler2D uC, uHt; uniform vec3 uCam, uGround; uniform float uLA;
  out vec4 o; const float ASP = ${ASP.toFixed(6)};
  float h21(vec2 p){ p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }
  float vn(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.-2.*f);
    return mix(mix(h21(i),h21(i+vec2(1,0)),f.x), mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x), f.y); }
  float fbm(vec2 p){ float a=.5,s=0.; for(int k=0;k<4;k++){ s+=a*vn(p); p=p*2.03+vec2(17.3,9.1); a*=.5; } return s/.94; }
  float weave(vec2 px){ px += (vec2(vn(px*.05), vn(px*.05+7.))-.5)*1.6; return .5 + .25*sin(px.x*2.25)*step(0.,sin(px.y*1.125)) + .25*sin(px.y*2.25)*step(0.,sin(px.x*1.125)); }
  float hgt(vec2 uv){ vec2 p = vec2(uv.x, 1.-uv.y); vec4 t = texture(uHt, p); return t.r*t.a + (1.-t.a*.8)*weave(uv*uRes)*.16; }
  void main(){
    vec2 uv0 = gl_FragCoord.xy/uRes; vec2 uv = (uv0-.5)/uCam.z + uCam.xy; vec2 px = uv*uRes;
    vec4 pc = texture(uC, vec2(uv.x, 1.-uv.y));
    vec3 ground = uGround*(.90+.20*weave(px))*(.93+.14*fbm(uv*vec2(ASP,1.)*6.));
    vec3 col = mix(ground, pc.rgb, pc.a);
    vec2 e = vec2(1.5)/uRes;
    float hx = hgt(uv+vec2(e.x,0.))-hgt(uv-vec2(e.x,0.)), hy = hgt(uv+vec2(0.,e.y))-hgt(uv-vec2(0.,e.y));
    vec3 n = normalize(vec3(-hx*2.1, -hy*2.1, 1.));
    vec3 L = normalize(vec3(cos(uLA)*.62, sin(uLA)*.62, .72)), Hh = normalize(L+vec3(0.,0.,1.));
    float diff = dot(n,L);
    col *= .60 + .56*diff/.72*.72;
    col += pow(max(dot(n,Hh),0.), 60.)*.13*(.3+.7*pc.a);
    col = mix(col, col*col*(3.-2.*col), .18);                                   // 一点点上光油的对比
    float v = length((uv0-.5)*vec2(1.,1.12)); col *= 1.-.22*pow(v*1.3, 3.);
    o = vec4(col, 1.);
  }`;
  const sh = (t, s) => { const x = gl.createShader(t); gl.shaderSource(x, s); gl.compileShader(x); if (!gl.getShaderParameter(x, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(x)); return x; };
  const pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FSRC)); gl.linkProgram(pr); gl.useProgram(pr);
  const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(pr, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  const U = n => gl.getUniformLocation(pr, n);
  const tex = [0, 1].map(() => { const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t); for (const [k, v] of [[gl.TEXTURE_MIN_FILTER, gl.LINEAR], [gl.TEXTURE_MAG_FILTER, gl.LINEAR], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, k, v); return t; });
  function draw(cvs, cam, la) {
    cvs.forEach((cv, i) => { gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, tex[i]); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, cv); });
    gl.viewport(0, 0, W, H); gl.uniform2f(U('uRes'), W, H); gl.uniform1i(U('uC'), 0); gl.uniform1i(U('uHt'), 1);
    gl.uniform3fv(U('uCam'), cam); gl.uniform3fv(U('uGround'), DATA.ground.map(v => v / 255)); gl.uniform1f(U('uLA'), la);
    gl.drawArrays(gl.TRIANGLES, 0, 3); gl.finish();
  }

  // ---------- 时间线 ----------
  const cum = LAY.reduce((a, n) => (a.push(a[a.length - 1] + n), a), [0]);
  const SLOW = Math.min(14, LAY[0]), T = { s0: .25, sdt: .17, ends: [5.70, 9.79, 13.89, 17.98, 22.07, 27.0], reveal: 29.7, end: 32.5 };
  const tSlowEnd = T.s0 + SLOW * T.sdt;
  function nAt(t) {
    if (t < T.s0) return 0;
    if (t < tSlowEnd) { const u = (t - T.s0) / T.sdt, k = Math.floor(u); return k + eo(cl((u - k) / .8)); }      // 前 14 笔：一笔一笔看得清
    if (t < T.ends[0]) return lerp(SLOW, cum[1], Math.pow(seg(t, tSlowEnd, T.ends[0]), 2.2));                     // 越画越快
    for (let i = 1; i < 6; i++) if (t < T.ends[i]) { const u = seg(t, T.ends[i - 1], T.ends[i]); return lerp(cum[i], cum[i + 1], .25 * u + .75 * u * u); }
    return TOTAL;
  }
  const FACE = [DATA.focus[0], 1 - DATA.focus[1]], EYES = [DATA.detail[0], 1 - DATA.detail[1]];
  function camAt(t) {
    if (t < 7) return [.5, .5, 1];
    if (t < 17) { const k = eio(seg(t, 7, 17)); return [lerp(.5, FACE[0], k), lerp(.5, FACE[1], k), lerp(1, 1.32, k)]; }
    if (t < 27.52) { const k = eio(seg(t, 17, 24.5)); return [lerp(FACE[0], EYES[0], k), lerp(FACE[1], EYES[1], k), lerp(1.32, 1.62, k)]; }
    const k = eio(seg(t, 27.52, T.reveal)); return [lerp(EYES[0], .5, k), lerp(EYES[1], .5, k), lerp(1.62, 1, k)];
  }
  const ov = document.getElementById('ov').getContext('2d');
  function brush(x, y, ang, R, col, a) {            // 画笔：笔毛带着这一笔的颜色
    const w = Math.max(16, R * 2), L = 560;
    ov.save(); ov.globalAlpha = a; ov.translate(x, y); ov.rotate(ang);
    ov.fillStyle = 'rgba(0,0,0,.18)'; ov.beginPath(); ov.ellipse(w * .2, 14, w * .55, w * .16, 0, 0, 7); ov.fill();
    ov.fillStyle = col; ov.beginPath(); ov.moveTo(-w / 2, -w * 1.5); ov.quadraticCurveTo(-w * .58, -w * .5, -w * .2, 0); ov.lineTo(w * .2, 0); ov.quadraticCurveTo(w * .58, -w * .5, w / 2, -w * 1.5); ov.fill();
    ov.strokeStyle = 'rgba(0,0,0,.25)'; ov.lineWidth = 1.2; for (let i = -2; i <= 2; i++) { ov.beginPath(); ov.moveTo(i * w * .16, -w * 1.5); ov.lineTo(i * w * .07, -w * .1); ov.stroke(); }
    const g = ov.createLinearGradient(-w / 2, 0, w / 2, 0); g.addColorStop(0, '#8d8f94'); g.addColorStop(.45, '#f1f2f4'); g.addColorStop(1, '#6f7176');
    ov.fillStyle = g; ov.fillRect(-w / 2, -w * 1.5 - w * 1.1, w, w * 1.1);
    const g2 = ov.createLinearGradient(-w / 2, 0, w / 2, 0); g2.addColorStop(0, '#5a2f1a'); g2.addColorStop(.4, '#a8623a'); g2.addColorStop(1, '#4a2413');
    ov.fillStyle = g2; ov.beginPath(); ov.moveTo(-w * .42, -w * 2.6); ov.lineTo(w * .42, -w * 2.6); ov.lineTo(w * .16, -w * 2.6 - L); ov.lineTo(-w * .16, -w * 2.6 - L); ov.fill();
    ov.restore();
  }
  const fmt = n => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',');

  function frame(t) {
    const n = nAt(t), cam = camAt(t), z = cam[2];
    cam[0] = cl(cam[0], .5/z, 1-.5/z); cam[1] = cl(cam[1], .5/z, 1-.5/z); const la = 2.35 - 1.25 * eio(seg(t, T.reveal - .4, T.end)) + .08 * Math.sin(t * .7);     // 画完以后光扫过去，厚涂的反光跟着走
    draw(paintTo(n), cam, la);
    ov.setTransform(1, 0, 0, 1, 0, 0); ov.clearRect(0, 0, W, H);
    const toS = (X, Y) => [((X / W - cam[0]) * z + .5) * W, (((1 - Y / H) - cam[1]) * -z + .5) * H];
    // 画笔：跟着最新的一笔
    const ba = cl(1 - (t - 12.5) / 1.5);
    if (ba > 0 && n > 0 && n < TOTAL) {
      const k = Math.min(TOTAL - 1, Math.floor(n)), s = S[k], np = (s.length - 4) / 2, f = t < tSlowEnd ? cl(n - k) : 1, u = (np - 1) * f, i = Math.min(np - 2, Math.floor(u)), ff = u - i;
      const X = lerp(s[4 + i * 2], s[6 + i * 2], ff), Y = lerp(s[5 + i * 2], s[7 + i * 2], ff), [sx, sy] = toS(X, Y);
      brush(sx, sy, .62 + .12 * Math.sin(k * 1.7), s[0] * z, `rgb(${s[1]},${s[2]},${s[3]})`, ba);
    }
    const alpha = cl((t-.45)/.4) * cl((29.5-t)/.8);
    if (alpha > 0 && DATA.overlay) {
      ov.save(); ov.globalAlpha = alpha;
      ov.shadowColor = 'rgba(20,16,15,.85)'; ov.shadowBlur = 9; ov.shadowOffsetY = 2;
      ov.fillStyle = '#fff3de'; ov.textAlign = 'left';
      ov.font = '34px SimSun, serif'; ov.fillText(DATA.title, 64, 1616);
      ov.font = 'bold 61px Georgia'; ov.fillText(fmt(Math.floor(n)), 62, 1687);
      let nw = ov.measureText(fmt(Math.floor(n))).width;
      ov.font = '28px SimSun, serif'; ov.fillText('笔', 77 + nw, 1686);
      ov.restore();
    }
  }
  if (q.has('n') || q.has('still')) { window.DUR = 1; window.render = () => { draw(paintTo(q.has('n') ? +q.get('n') : TOTAL), q.has('z') ? [.5, FACE[1], +q.get('z')] : [.5, .5, 1], 2.35); }; }
  else { window.DUR = T.end; window.render = frame; }
  window.render(0); window.READY = true;
})();
