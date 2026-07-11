"""Assemble the combined italic: per-glyph source map + weight matching.

    uv run --with fonttools --with freetype-py python scripts/build_italic_combined.py [GSC_R] [GSC_B]

Lowercase source map (user's picks); UPPERCASE + symbols stay SFMS (untouched).
GSC letters come from the GSC-Italic VF instanced at a tuned wght (thinner, to
match SFMS). Iosevka letters (q,s) are injected raw here; thickening is a small
FontForge post-pass (see poc_thicken_iosevka.py). Prints measured stems so the
weights can be dialled in.
"""
import os, sys
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.qu2cuPen import Qu2CuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.misc.transform import Transform
import freetype

HOME=os.path.expanduser("~")
SFMS=lambda s: os.path.join(HOME,f"Library/Fonts/SFMonoSquare-{s}.otf")
GSC_VF="sources/google-sans-code/GoogleSansCode-Italic[wght].ttf"
IOS={"RegularItalic":"dist-0.5em/KusunokiMonoNFLG/KusunokiMonoNFLG-Italic.ttf",
     "BoldItalic":"dist-0.5em/KusunokiMonoNFLG/KusunokiMonoNFLG-BoldItalic.ttf"}

GSC_R=int(sys.argv[1]) if len(sys.argv)>1 else 360
GSC_B=int(sys.argv[2]) if len(sys.argv)>2 else 650

SRCMAP={}
for c in "abcdefijklpvyz": SRCMAP[c]="gsc"
# qs (reverted from Iosevka: too narrow when x-matched) + ghmnortuwx
# + all uppercase + symbols => SFMS (omitted => kept)

def xheight(font):
    gs,cmap=font.getGlyphSet(),font.getBestCmap()
    p=BoundsPen(gs); gs[cmap[ord("x")]].draw(p); return p.bounds[3]-p.bounds[1]
def mono_adv(font): return font["hmtx"][font.getBestCmap()[ord("M")]][0]

def median(vals):
    s=sorted(vals); n=len(s)
    return 0 if n==0 else (s[n//2] if n%2 else (s[n//2-1]+s[n//2])/2)

def target_ink_offset(tgt):
    """Median ink-centre offset (from cell centre) of the SFMS-kept lowercase
    letters. SFMS italic sits its ink right-of-centre; grafted glyphs must match
    that offset or the monospace rhythm alternates tight/loose."""
    gs,cmap,hmtx=tgt.getGlyphSet(),tgt.getBestCmap(),tgt["hmtx"]
    offs=[]
    for c in "ghmnoqrstuwx":
        gn=cmap.get(ord(c))
        if not gn: continue
        p=BoundsPen(gs); gs[gn].draw(p)
        if p.bounds:
            xmin,_,xmax,_=p.bounds
            offs.append((xmin+xmax)/2 - hmtx[gn][0]/2.0)
    return median(offs)

def inject(tgt, source_font, cps):
    src_gs,src_cmap=source_font.getGlyphSet(),source_font.getBestCmap()
    tgt_cmap=tgt.getBestCmap()
    S=xheight(tgt)/xheight(source_font)
    adv=mono_adv(tgt)
    off=target_ink_offset(tgt)
    cff=tgt["CFF "].cff; top=cff[cff.fontNames[0]]
    cs,priv,gsubrs=top.CharStrings,top.Private,top.GlobalSubrs; hmtx=tgt["hmtx"]
    for cp in cps:
        sname,tname=src_cmap.get(cp),tgt_cmap.get(cp)
        if not sname or not tname: continue
        rec=DecomposingRecordingPen(src_gs); src_gs[sname].draw(rec)
        # position by INK centre -> match SFMS's offset (not advance-box centring)
        sb=BoundsPen(None); rec.replay(TransformPen(sb,Transform().scale(S)))
        if not sb.bounds: continue
        icx=(sb.bounds[0]+sb.bounds[2])/2.0
        dx=(adv/2.0+off)-icx
        xform=Transform().translate(dx,0).scale(S)
        pen=T2CharStringPen(adv,None)
        rec.replay(TransformPen(Qu2CuPen(pen,max_err=0.5,reverse_direction=True),xform))
        cs[tname]=pen.getCharString(private=priv,globalSubrs=gsubrs)
        bp=BoundsPen(None); rec.replay(TransformPen(bp,xform))
        hmtx[tname]=(adv,int(round(bp.bounds[0])) if bp.bounds else 0)

def build(style, gsc_wght, out):
    tgt=TTFont(SFMS(style))
    gsc=instancer.instantiateVariableFont(TTFont(GSC_VF),{"wght":gsc_wght},inplace=False)
    ios_path=IOS[style]
    if style=="RegularItalic" and os.path.exists("build/poc/_ios-italic-thick.ttf"):
        ios_path="build/poc/_ios-italic-thick.ttf"   # thickened q,s (poc_thicken_iosevka.py)
    ios=TTFont(ios_path)
    inject(tgt, gsc, [ord(c) for c,s in SRCMAP.items() if s=="gsc"])
    inject(tgt, ios, [ord(c) for c,s in SRCMAP.items() if s=="iosevka"])
    n=tgt["name"]
    fam=f"SFMS Combined {'Bold ' if 'Bold' in style else ''}Italic"
    n.setName("SFMS Combined Italic",1,3,1,0x409); n.setName(fam,4,3,1,0x409)
    n.setName("SFMSCombined-"+style,6,3,1,0x409)
    tgt.save(out); return out

def stem(path, ch, frac=0.5):
    face=freetype.Face(path); face.set_pixel_sizes(0,1000)
    face.load_char(ch,freetype.FT_LOAD_RENDER); bm=face.glyph.bitmap
    if not bm.width or not bm.rows: return None
    row=min(int(bm.rows*(1-frac)),bm.rows-1); r=bm.buffer[row*bm.pitch:row*bm.pitch+bm.width]
    best=cur=0
    for v in r:
        if v>96: cur+=1; best=max(best,cur)
        else: cur=0
    return best

os.makedirs("build/poc",exist_ok=True)
out_r=build("RegularItalic",GSC_R,"build/poc/Combined-Italic.otf")
out_b=build("BoldItalic",GSC_B,"build/poc/Combined-BoldItalic.otf")
print(f"built (GSC_R={GSC_R}, GSC_B={GSC_B})")
for label,path in [("Regular",out_r),("Bold",out_b)]:
    sf=sum(stem(path,c) for c in "nuqs")/4         # SFMS-sourced (n,u,q,s)
    gs=sum(stem(path,c) for c in "lp")/2           # GSC-sourced (l,p)
    print(f"  {label:7} stems  SFMS(n,u,q,s)={sf:.0f}  GSC(l,p)={gs:.0f}")
