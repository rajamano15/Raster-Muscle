"""Export hero head frames.  Needs: pip install numpy pillow scipy

Usage:
  ffmpeg -i Animate_human_muscle_fiber_head_202609042214.mp4 -vsync 0 head-src/f%03d.png
  python3 tools-export-head-frames.py
Then paste head-poses.json into js/main.js as POSES, and keep #headCanvas and
.fig-poster in index.html at the same SIZE as below.

Export hero head frames from Animate_human_muscle_fiber_head_202609042214.mp4.

Choreography (0-based frame -> gaze), read at full resolution and cross-checked
against measured signals (darkCx = dark facial features' horizontal offset,
+right/-left; paleFrac = bare-cranium area, low=up high=down):

  front -> LEFT profile (18-24) -> up-left (44) -> UP (48) -> up-right (56)
  -> RIGHT profile (72-80) -> front (88) -> LEFT (96-104) -> RIGHT (112-120)
  -> down-right (126-130) -> DOWN (136-142) -> down-left (150-158)
  -> LEFT profile (162-176) -> front (191)

Two horizontal sweeps per side, which is the "additional movement on the right"
the user flagged. darkCx is NOT trusted in the pitched-down stretch (126-162):
shadowed brows shift it wildly -- it reads -0.51 at f133 where the head is in
fact front-to-right, and +0.36..+0.59 across f145-f153 where the head is in fact
turning LEFT. Everything from 118 on is landmarked from 430px head crops only.

The clip's ONE down-right pass is f122-f134; after the chin drops at f136-f142
the head turns left and stays left to the end. So the deepest down-right pose
available is ~(0.6, 0.45) at f128 -- a cursor in the bottom-right corner settles
there, which is as far as the source goes.
"""
import json, math, pathlib, numpy as np
from PIL import Image
from scipy import ndimage

HERE = pathlib.Path(__file__).resolve().parent
FR   = sorted((HERE/"head-src").glob("f*.png"))
OUT  = HERE / "assets/img/head"
N   = len(FR) or 192          # poses-only run when head-src/ has been cleared

# The source is framed wider than the previous clip (figure down to the thighs),
# which left the head only 31% of the frame. Crop to a waist cut so the head is
# 40% — matching the old rig — and keep the 1.047 aspect so the hero layout and
# .figure-wrap's bottom mask fade are unchanged. Width 811 clears the arms at
# the cut line (figure spans ~575..1345 there).
CROP = (554, 36, 554 + 811, 36 + 775)
SIZE = (640, 612)

LAND = [(0,0,0),(18,-1,0),(24,-1,0),(44,-0.35,-0.9),(48,0,-1),(56,0.25,-0.95),
        (72,1,0),(80,1,0),(88,0,0),(96,-1,0),(104,-1,0),(112,1,0),(120,1,0.15),
        (128,0.6,0.45),(136,0.1,0.85),(142,0,1),(152,-0.45,0.85),(160,-0.88,0.32),
        (168,-1,0.1),(176,-0.9,0),(184,-0.3,0),(191,0,0)]

def gaze(i):
    if i <= LAND[0][0]:  return LAND[0][1], LAND[0][2]
    if i >= LAND[-1][0]: return LAND[-1][1], LAND[-1][2]
    for (a,ax,ay),(b,bx,by) in zip(LAND, LAND[1:]):
        if a <= i <= b:
            t = 0 if b == a else (i-a)/(b-a)
            return ax+(bx-ax)*t, ay+(by-ay)*t
    return 0.0, 0.0
POSES = [[round(x,3), round(y,3)] for x, y in (gaze(i) for i in range(N))]

def ss(e0,e1,x):
    t = np.clip((x-e0)/(e1-e0),0,1); return t*t*(3-2*t)

if FR:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.webp"): old.unlink()  # remove the existing animation

total = 0
for i, f in enumerate(FR):
    rgb = np.asarray(Image.open(f).convert("RGB")).astype(np.float32)
    soft = ss(14., 44., rgb.max(axis=2))
    mask = soft >= 0.5
    lab, n = ndimage.label(mask)
    if n:
        sz = ndimage.sum(mask, lab, range(1, n+1))
        mask = lab == (int(np.argmax(sz)) + 1)   # largest component: drops specks
    mask = ndimage.binary_dilation(mask, iterations=3)
    a = soft * mask
    straight = np.clip(rgb / np.maximum(a, 1e-3)[..., None], 0, 255)
    im = Image.fromarray(np.dstack([straight, a*255.]).astype(np.uint8), "RGBA")
    im = im.crop(CROP).resize(SIZE, Image.LANCZOS)
    p = OUT / f"p{i}.webp"
    im.save(p, "WEBP", quality=(72 if i == 0 else 46), method=6)
    total += p.stat().st_size
    if i % 48 == 0: print("  ", i, "->", p.name, flush=True)

(HERE/"head-poses.json").write_text(json.dumps(POSES))   # paste into js/main.js as POSES
print("frames: %d  total: %.1f MB" % (len(FR), total/1e6) if FR
      else "poses only (head-src empty): %d entries" % N)
for k in (0,18,48,72,88,104,112,128,142,152,168,191):
    print("   p%-4d %s" % (k, POSES[k]))
