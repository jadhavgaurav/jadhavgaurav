"""Render the profile intro from the verified neural-network training trajectory.

Requires Node.js, Pillow and NumPy. No browser capture or external rendering service.
Run from any directory: python scripts/render_intro.py
"""
from pathlib import Path
import argparse
import json
import math
import subprocess
import shutil

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
FONTS = ROOT / 'scripts' / 'fonts'
WIDTH, HEIGHT, FPS = 1120, 570, 10
PALETTES = {
    'light': dict(paper='#f4f2ed', ink='#17251f', quiet='#56665d', line='#d3d9cf', green='#376b4c', violet='#77659a'),
    'dark': dict(paper='#101413', ink='#e7eee8', quiet='#a0afa4', line='#303c34', green='#b9f88c', violet='#c3a5e7'),
}


def color(hex_color):
    return np.array([int(hex_color[i:i+2], 16) for i in (1, 3, 5)], dtype=float)


def blend(a, b, t):
    return tuple(np.rint(a + (b-a)*t).astype(int))


def font(name, size, weight=None):
    f = ImageFont.truetype(str(FONTS / f'{name}.ttf'), size)
    if weight is not None:
        axes = f.get_variation_axes()
        f.set_variation_by_axes([weight if a['name'] == b'Weight' else a['default'] for a in axes])
    return f


def predict(weights, x, y):
    w = np.asarray(weights)
    hidden = np.tanh(np.asarray(x)[..., None]*w[:32:4] + np.asarray(y)[..., None]*w[1:32:4] + w[2:32:4])
    return 1/(1+np.exp(-(hidden@w[3:32:4]+w[32]))), hidden


def background(theme, mobile=False):
    p = {k: color(v) for k, v in PALETTES[theme].items()}
    image = Image.new('RGB', (640, 900) if mobile else (WIDTH, HEIGHT), tuple(p['paper'].astype(int)))
    d = ImageDraw.Draw(image)
    ink, quiet, green, line = [tuple(p[n].astype(int)) for n in ['ink', 'quiet', 'green', 'line']]
    mono, small = font('IBMPlexMono', 15), font('IBMPlexMono', 14)
    if mobile:
        d.text((38, 22), 'gj.', font=font('SpaceGrotesk', 38, 500), fill=ink)
        d.text((238, 33), 'ENGINEERING × IMAGINATION', font=font('IBMPlexMono', 22), fill=quiet)
        d.line((38, 86, 602, 86), fill=line)
        d.ellipse((39, 120, 46, 127), fill=green)
        d.text((61, 107), 'AI & PRODUCT ENGINEER', font=font('IBMPlexMono', 23), fill=quiet)
        d.text((35, 146), 'Gaurav', font=font('SpaceGrotesk', 100, 500), fill=ink)
        d.text((35, 241), 'Jadhav.', font=font('SpaceGrotesk', 100, 500), fill=green)
        d.text((39, 372), 'I turn complex ideas', font=font('DMSans', 32, 400), fill=ink)
        d.text((39, 414), 'into useful products.', font=font('DMSans', 32, 400), fill=ink)
        return image,p
    d.text((46, 19), 'gj.', font=font('SpaceGrotesk', 32, 500), fill=ink)
    d.text((676, 30), 'ENGINEERING × IMAGINATION', font=mono, fill=quiet)
    d.line((46, 72, WIDTH-46, 72), fill=line)
    d.ellipse((47, 113, 53, 119), fill=green)
    d.text((65, 104), 'AI & PRODUCT ENGINEER', font=mono, fill=quiet)
    d.text((43, 137), 'Gaurav', font=font('SpaceGrotesk', 92, 500), fill=ink)
    d.text((43, 224), 'Jadhav.', font=font('SpaceGrotesk', 92, 500), fill=green)
    d.text((47, 351), 'I turn complex ideas', font=font('DMSans', 25, 400), fill=ink)
    d.text((47, 386), 'into useful products.', font=font('DMSans', 25, 400), fill=ink)
    d.line((46, 467, WIDTH-46, 467), fill=line)
    d.rectangle((42, 455, 229, 479), fill=tuple(p['paper'].astype(int)))
    d.text((46, 456), 'SELECTED BUILDS', font=small, fill=quiet)
    for x, title, subtitle in [(46, 'VICTUS', 'Agents with controls'), (412, 'INNEED', 'Products for people'), (779, 'Bitling', 'Code with character')]:
        if x > 46:
            d.line((x-25, 503, x-25, 549), fill=line)
        d.text((x, 493), title, font=font('SpaceGrotesk', 22, 500), fill=ink)
        d.text((x, 526), subtitle, font=small, fill=quiet)
    return image, p


def frame(base, p, model, seconds):
    image = base.copy()
    progress = min(1, max(0, (seconds-1)/11))
    snap = model['frames'][math.floor(progress*progress*(len(model['frames'])-1))]
    weights = snap['w']
    probe = model['data'][int(seconds*3) % len(model['data'])]
    # Same fixed feature bounds as the approved preview; no interpolated weights.
    xx, yy = np.meshgrid(np.linspace(-1.8, 1.8, 128), np.linspace(1.15, -1.15, 92))
    probability, _ = predict(weights, xx, yy)
    target = p['green'] + probability[..., None]*(p['violet']-p['green'])
    strength = (.10+.19*np.abs(2*probability-1))[..., None]
    rgb = np.rint(p['paper'] + strength*(target-p['paper'])).astype(np.uint8)
    mobile = base.width == 640
    left, top, fw, fh = (65, 485, 510, 250) if mobile else (666, 119, 374, 225)
    field = Image.fromarray(rgb).resize((fw, fh), Image.Resampling.BILINEAR)
    mask = Image.new('L', (fw, fh))
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, fw-1, fh-1), 20, fill=255)
    image.paste(field, (left, top), mask)
    d = ImageDraw.Draw(image)
    def xy(x, y):
        return left+(x+1.8)/3.6*fw, top+(1.15-y)/2.3*fh
    # Marching squares, including saddle cells, for the actual p=0.5 contour.
    contour = blend(p['paper'], (p['green']+p['violet'])/2, .5)
    for j in range(91):
        for i in range(127):
            corners = [(i,j,probability[j,i]-.5),(i+1,j,probability[j,i+1]-.5),(i+1,j+1,probability[j+1,i+1]-.5),(i,j+1,probability[j+1,i]-.5)]
            crossing = []
            for n in range(4):
                a, b = corners[n], corners[(n+1)%4]
                if (a[2]>=0) != (b[2]>=0):
                    t = a[2]/(a[2]-b[2])
                    crossing.append((left+(a[0]+t*(b[0]-a[0]))/127*fw,top+(a[1]+t*(b[1]-a[1]))/91*fh))
            if len(crossing) == 2:
                d.line(crossing, fill=contour)
            elif len(crossing) == 4:
                d.line(crossing[:2], fill=contour)
                d.line(crossing[2:], fill=contour)
    paper = tuple(p['paper'].astype(int))
    for point in model['data']:
        x, y = xy(point['x'], point['y'])
        fill = tuple(p['violet' if point['label'] else 'green'].astype(int))
        if point['label']:
            d.polygon([(x,y-4),(x+4,y),(x,y+4),(x-4,y)], fill=fill, outline=paper, width=1)
        else:
            d.ellipse((x-3.5,y-3.5,x+3.5,y+3.5), fill=fill, outline=paper, width=1)
    x, y = xy(probe['x'], probe['y'])
    d.ellipse((x-8,y-8,x+8,y+8), outline=tuple(p['ink'].astype(int)), width=1)
    # Clip both the contour and markers to the same rounded field as the colors.
    box = (left, top, left+fw, top+fh)
    plot = image.crop(box)
    image.paste(base.crop(box), (left, top))
    image.paste(plot, (left, top), mask)
    d = ImageDraw.Draw(image)
    out, hidden = predict(weights, probe['x'], probe['y'])
    inputs = [(102,800),(102,844)] if mobile else [(694,389),(694,427)]
    middle = [(320,767+i*15) for i in range(8)] if mobile else [(850,365+i*12.5) for i in range(8)]
    output = (538,822) if mobile else (1012,409)
    def edge(a, b, weight):
        alpha = .08+min(.45,abs(weight)*.12)
        d.line([a,b], fill=blend(p['paper'],p['green' if weight>=0 else 'violet'],alpha), width=max(1,round(.55+min(1.6,abs(weight)*.4))))
    for i, h in enumerate(middle):
        edge(inputs[0],h,weights[i*4])
        edge(inputs[1],h,weights[i*4+1])
        edge(h,output,weights[i*4+3])
    def node(at, value, prediction=False):
        fill = blend(p['green'],p['violet'],value) if prediction else blend(p['paper'],p['green' if value>=0 else 'violet'],.22+.72*min(1,abs(value)))
        x,y=at
        d.ellipse((x-5,y-5,x+5,y+5),fill=fill,outline=paper,width=1)
    node(inputs[0],probe['x']);node(inputs[1],probe['y'])
    for at, value in zip(middle,hidden):node(at,value)
    node(output,float(out),True)
    return image


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--layout',choices=['all','desktop','mobile'],default='all')
    args=parser.parse_args()
    ASSETS.mkdir(exist_ok=True)
    node = shutil.which('node')
    if not node:
        raise SystemExit('Node.js is required to run scripts/learning-model.cjs')
    model = json.loads(subprocess.check_output([node,str(ROOT/'scripts'/'learning-model.cjs')],text=True))
    layouts=[False,True] if args.layout=='all' else [args.layout=='mobile']
    for theme,mobile in [(theme,mobile) for mobile in layouts for theme in PALETTES]:
        suffix=theme+('-mobile' if mobile else '')
        base,p=background(theme,mobile)
        # Use a global palette to keep static pixels stable across GIF frames.
        sheet=Image.new('RGB',(base.width,base.height*3))
        for i,t in enumerate([0,5,13]):sheet.paste(frame(base,p,model,t),(0,i*base.height))
        palette=sheet.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
        frames=[]
        for i in range(180):
            im=frame(base,p,model,i/FPS)
            frames.append(im.quantize(palette=palette,dither=Image.Dither.NONE))
            if i%60==0:print(f'{suffix}: frame {i}/180',flush=True)
        final=frame(base,p,model,13)
        final.save(ASSETS/f'intro-{suffix}.png',optimize=True)
        frames[0].save(ASSETS/f'intro-{suffix}.gif',save_all=True,append_images=frames[1:],duration=100,loop=0,optimize=True,disposal=1)
        print(f'{suffix}: {(ASSETS/f"intro-{suffix}.gif").stat().st_size:,} bytes',flush=True)
    print('Rendered both themes from the same verified training trajectory.',flush=True)


if __name__=='__main__':
    main()
