from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from pathlib import Path
font=TTFont('/usr/share/fonts/opentype/urw-base35/Z003-MediumItalic.otf');glyphs=font.getGlyphSet();cmap=font.getBestCmap();x=40;paths=[]
for char in 'OBE-TraceX':
 name=cmap[ord(char)];pen=SVGPathPen(glyphs);glyphs[name].draw(TransformPen(pen,(1,0,0,-1,x,780)));paths.append('<path pathLength="1" d="'+pen.getCommands()+'"/>');x+=font['hmtx'][name][0]
svg='<svg class="written-brand" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+str(x+80)+' 1060" role="img" aria-label="OBE-TraceX">'+''.join(paths)+'</svg>'
Path('evaluations/templates/evaluations/brand_reveal.html').write_text(svg)
