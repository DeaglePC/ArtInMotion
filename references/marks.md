# Custom drawing plans

Use a UTF-8 JSON plan when the desired medium, motif or sequence needs individual art direction. An agent can author paths from a text brief, or calculate them from a local photograph. The same renderer animates and exports them. A text brief needs an authored plan before rendering.

```json
{
  "size": [640, 480],
  "ground": [251, 248, 238],
  "tool": "pencil",
  "marks": [
    {"shape": "line", "points": [[100,315],[195,190],[265,270],[330,210],[470,315]], "color": [54,83,97], "width": 4},
    {"shape": "dot", "points": [[443,124]], "color": [191,111,70], "width": 44},
    {"shape": "line", "points": [[75,327],[190,329],[340,325],[510,327]], "color": [88,134,151], "width": 3, "opacity": 150}
  ]
}
```

`size` is [width,height], both even, 2–4096. Points are integer pixels within the canvas, origin at the top left. Colors are integer RGB in 0–255. Marks accumulate in array order. Lines follow a polyline, dots use their first point and width (diameter), polygons need three or more vertices, and tiles need top-left and bottom-right corners. Polygons and tiles land as a unit. Width defaults to 1 and opacity to 255. Tools: pen, pencil, chalk, brush, gouge, roller, stylus, piece, grain, tile. The last three show a placement cursor.

For a new reusable photo medium, add a named entry to `STYLES` in `scripts/art_styles.py`, implement its mark generator, and route it in `Study.plan`. Sample colors and edges from the supplied image and scale dimensions to its short side. Return ordered marks, never a completed image to dissolve into. A new style should pass still/movie final-canvas parity and be visually distinguishable at the intended viewing size.
