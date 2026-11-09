"""
Build the Indie Runners logo asset pack.

The ir mark is drawn from real Fraunces outlines, so the final files do not
depend on any font being installed. The amber dot replaces the dot of the i.

Outputs go to ./out:
  svg/       master vector files
  instagram/ profile picture PNGs
  favicon/   browser and home screen icons plus a web manifest
  social/    Open Graph image for link previews
"""

import io
import os
import json

import cairosvg
import uharfbuzz as hb
from PIL import Image
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
OUT_DIR = os.path.join(HERE, "out")

# brand palette, taken from main.css
FOREST = "#1c2b1e"
OFF_WHITE = "#f6f4f0"
AMBER = "#e8a44a"
WHITE_MUTED = "#a9b0a7"  # off white at roughly 65 percent on forest, made opaque


class StaticFont:
    """One fixed instance of a variable font, able to shape text and give SVG paths."""

    def __init__(self, path, axes):
        print("making font instance " + os.path.basename(path) + " " + str(axes))
        varfont = TTFont(path)
        self.font = instancer.instantiateVariableFont(varfont, axes)
        buf = io.BytesIO()
        self.font.save(buf)
        self.hb_font = hb.Font(hb.Face(buf.getvalue()))
        self.glyph_set = self.font.getGlyphSet()
        self.upm = self.font["head"].unitsPerEm
        self.x_height = self.font["OS/2"].sxHeight

    def glyph_name(self, char):
        return self.font.getBestCmap()[ord(char)]

    def contours(self, glyph_name):
        """Return each contour of a glyph as its own recording, components resolved."""
        pen = DecomposingRecordingPen(self.glyph_set)
        self.glyph_set[glyph_name].draw(pen)
        result, current = [], []
        for op, args in pen.value:
            current.append((op, args))
            if op in ("closePath", "endPath"):
                result.append(current)
                current = []
        return result

    def shape(self, text, tracking=0):
        """Return (glyph_name, x, y) placements and the total advance, in font units."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb_font, buf, {"kern": True, "liga": True})
        placements, x = [], 0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            name = self.font.getGlyphOrder()[info.codepoint]
            placements.append((name, x + pos.x_offset, pos.y_offset))
            x += pos.x_advance + tracking
        return placements, x - tracking


def replay(recording, pen):
    for op, args in recording:
        getattr(pen, op)(*args)


def path_for(recordings, transform):
    """SVG path data for a list of contour recordings under an affine transform."""
    svg_pen = SVGPathPen(None)
    pen = TransformPen(svg_pen, transform)
    for rec in recordings:
        replay(rec, pen)
    return svg_pen.getCommands()


def bounds_of(recordings, transform=(1, 0, 0, 1, 0, 0)):
    bpen = BoundsPen(None)
    pen = TransformPen(bpen, transform)
    for rec in recordings:
        replay(rec, pen)
    return bpen.bounds


class IrMark:
    """The ir monogram as outlines: letters in one path, the dot as a circle."""

    def __init__(self, font, dot_scale=1.0, tracking_em=-0.03):
        self.font = font
        tracking = tracking_em * font.upm
        placements, _ = font.shape("ir", tracking=tracking)

        letter_contours = []
        stem_contours = []
        dot = None
        for name, x, y in placements:
            for contour in font.contours(name):
                moved = self._translate(contour, x, y)
                box = bounds_of([moved])
                is_i = name == font.glyph_name("i")
                if is_i and box[1] > font.x_height * 0.9:
                    dot = box
                else:
                    letter_contours.append(moved)
                    if is_i:
                        stem_contours.append(moved)

        if dot is None:
            raise ValueError("could not find the dot of the i")

        self.letters = letter_contours
        letters_box = bounds_of(self.letters)

        # amber dot sits over the middle of the i stem, slightly larger than the original dot
        cx = self._stem_centre(stem_contours, font.x_height * 0.5)
        r = max(dot[2] - dot[0], dot[3] - dot[1]) / 2 * dot_scale
        cy = (dot[1] + dot[3]) / 2
        min_gap = font.upm * 0.04
        if cy - r < letters_box[3] + min_gap:
            cy = letters_box[3] + min_gap + r
        self.dot = (cx, cy, r)

        self.box = (
            min(letters_box[0], cx - r),
            letters_box[1],
            max(letters_box[2], cx + r),
            max(letters_box[3], cy + r),
        )
        print("mark built, dot radius " + str(round(r)) + " units")

    @staticmethod
    def _stem_centre(contours, y_line):
        """Find the horizontal middle of the stem by rendering it and scanning one row."""
        x0, y0, x1, y1 = bounds_of(contours)
        scale = 0.5
        w = int((x1 - x0) * scale) + 4
        h = int((y1 - y0) * scale) + 4
        t = (scale, 0, 0, -scale, -x0 * scale + 2, y1 * scale + 2)
        svg = '<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}"><path d="{2}" fill="#000"/></svg>'.format(
            w, h, path_for(contours, t))
        img = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert("RGBA")
        row = int(-scale * y_line + y1 * scale + 2)
        filled = [px for px in range(w) if img.getpixel((px, row))[3] > 128]
        left, right = filled[0], filled[-1]
        return ((left + right) / 2 - 2) / scale + x0

    @staticmethod
    def _translate(contour, dx, dy):
        out = []
        for op, args in contour:
            out.append((op, tuple((p[0] + dx, p[1] + dy) for p in args)))
        return out

    def place(self, cx, cy, height):
        """SVG elements for the mark centred at (cx, cy) with total height in px. Letters use currentColor."""
        x0, y0, x1, y1 = self.box
        s = height / (y1 - y0)
        mid_x = (x0 + x1) / 2
        mid_y = (y0 + y1) / 2
        # font space is y up, svg is y down
        t = (s, 0, 0, -s, cx - mid_x * s, cy + mid_y * s)
        d = path_for(self.letters, t)
        dcx, dcy, r = self.dot
        sx = t[0] * dcx + t[4]
        sy = t[3] * dcy + t[5]
        return d, (round(sx, 2), round(sy, 2), round(r * s, 2))


class TextLine:
    """A line of text turned into an SVG path."""

    def __init__(self, font, text, tracking_em=0.0):
        self.font = font
        self.placements, self.advance = font.shape(text, tracking=tracking_em * font.upm)

    def path(self, x, baseline, size):
        s = size / self.font.upm
        svg_pen = SVGPathPen(None)
        for name, gx, gy in self.placements:
            t = (s, 0, 0, -s, x + gx * s, baseline - gy * s)
            self.font.glyph_set[name].draw(TransformPen(svg_pen, t))
        return svg_pen.getCommands()

    def width(self, size):
        return self.advance * size / self.font.upm


class AssetBuilder:
    """Composes SVGs from the mark and exports every file in the pack."""

    def __init__(self, mark, small_mark, wordmark_font, body_font):
        self.mark = mark
        self.small_mark = small_mark
        self.wordmark_font = wordmark_font
        self.body_font = body_font

    # svg composition

    def mark_svg(self, mark, size, bg, fg, shape, mark_ratio):
        """shape is circle, square or none. mark_ratio is mark height relative to size."""
        c = size / 2
        d, (dx, dy, dr) = mark.place(c, c * 1.02, size * mark_ratio)
        if shape == "circle":
            back = '<circle cx="{0}" cy="{0}" r="{0}" fill="{1}"/>'.format(c, bg)
        elif shape == "square":
            back = '<rect width="{0}" height="{0}" fill="{1}"/>'.format(size, bg)
        else:
            back = ""
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s} {s}" width="{s}" height="{s}">'
            "{back}"
            '<path d="{d}" fill="{fg}"/>'
            '<circle cx="{dx}" cy="{dy}" r="{dr}" fill="{amber}"/>'
            "</svg>"
        ).format(s=size, back=back, d=d, fg=fg, dx=dx, dy=dy, dr=dr, amber=AMBER)

    def og_svg(self):
        w, h = 1200, 630
        d, (dx, dy, dr) = self.mark.place(230, 315, 230)
        name = TextLine(self.wordmark_font, "Indie Runners", tracking_em=-0.01)
        tag = TextLine(self.body_font, "Find out where your friends are running.")
        url = TextLine(self.body_font, "indierunners.co")
        x = 420
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            '<rect width="{w}" height="{h}" fill="{forest}"/>'
            '<circle cx="230" cy="315" r="170" fill="#2d4430"/>'
            '<path d="{d}" fill="{off}"/>'
            '<circle cx="{dx}" cy="{dy}" r="{dr}" fill="{amber}"/>'
            '<path d="{name}" fill="#ffffff"/>'
            '<path d="{tag}" fill="{muted}"/>'
            '<path d="{url}" fill="{amber}"/>'
            "</svg>"
        ).format(
            w=w, h=h, forest=FOREST, off=OFF_WHITE, amber=AMBER, muted=WHITE_MUTED,
            d=d, dx=dx, dy=dy, dr=dr,
            name=name.path(x, 300, 92),
            tag=tag.path(x + 4, 368, 30),
            url=url.path(x + 4, 430, 26),
        )

    # writing files

    @staticmethod
    def write(path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)
        print("wrote " + os.path.relpath(path, OUT_DIR))

    @staticmethod
    def png(svg_text, path, size):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        cairosvg.svg2png(bytestring=svg_text.encode(), write_to=path, output_width=size[0], output_height=size[1])
        print("wrote " + os.path.relpath(path, OUT_DIR))

    def build(self):
        svg_dir = os.path.join(OUT_DIR, "svg")
        masters = {
            "ir-mark-circle.svg": self.mark_svg(self.mark, 1000, FOREST, OFF_WHITE, "circle", 0.5),
            "ir-mark-circle-inverse.svg": self.mark_svg(self.mark, 1000, OFF_WHITE, FOREST, "circle", 0.5),
            "ir-mark-dark.svg": self.mark_svg(self.mark, 1000, None, FOREST, "none", 0.8),
            "ir-mark-light.svg": self.mark_svg(self.mark, 1000, None, OFF_WHITE, "none", 0.8),
            "ir-mark-small-circle.svg": self.mark_svg(self.small_mark, 1000, FOREST, OFF_WHITE, "circle", 0.6),
        }
        for name, svg in masters.items():
            self.write(os.path.join(svg_dir, name), svg)

        # instagram crops to a circle itself, so give it a full bleed square
        avatar = self.mark_svg(self.mark, 1000, FOREST, OFF_WHITE, "square", 0.5)
        self.write(os.path.join(svg_dir, "ir-avatar-square.svg"), avatar)
        for size in (320, 1080):
            self.png(avatar, os.path.join(OUT_DIR, "instagram", "profile-" + str(size) + ".png"), (size, size))

        # favicons use the sturdier small size cut
        fav_dir = os.path.join(OUT_DIR, "favicon")
        fav_svg = masters["ir-mark-small-circle.svg"]
        self.write(os.path.join(fav_dir, "favicon.svg"), fav_svg)
        self.png(fav_svg, os.path.join(fav_dir, "favicon-32.png"), (32, 32))
        self.png(fav_svg, os.path.join(fav_dir, "favicon-16.png"), (16, 16))

        ico_frames = []
        for size in (16, 32, 48):
            data = cairosvg.svg2png(bytestring=fav_svg.encode(), output_width=size, output_height=size)
            ico_frames.append(Image.open(io.BytesIO(data)).convert("RGBA"))
        ico_frames[-1].save(os.path.join(fav_dir, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)], append_images=ico_frames[:-1])
        print("wrote favicon/favicon.ico")

        # home screen icons are full bleed squares, the platform rounds them
        square = self.mark_svg(self.mark, 1000, FOREST, OFF_WHITE, "square", 0.46)
        self.png(square, os.path.join(fav_dir, "apple-touch-icon.png"), (180, 180))
        self.png(square, os.path.join(fav_dir, "icon-192.png"), (192, 192))
        self.png(square, os.path.join(fav_dir, "icon-512.png"), (512, 512))

        manifest = {
            "name": "Indie Runners",
            "short_name": "Indie Runners",
            "icons": [
                {"src": "/static/favicon/icon-192.png", "sizes": "192x192", "type": "image/png"},
                {"src": "/static/favicon/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
            ],
            "theme_color": FOREST,
            "background_color": FOREST,
            "display": "browser",
        }
        self.write(os.path.join(fav_dir, "site.webmanifest"), json.dumps(manifest, indent=2))

        og = self.og_svg()
        self.write(os.path.join(svg_dir, "og-image.svg"), og)
        self.png(og, os.path.join(OUT_DIR, "social", "og-image.png"), (1200, 630))


def main():
    fraunces = os.path.join(FONT_DIR, "Fraunces.ttf")
    jakarta = os.path.join(FONT_DIR, "Jakarta.ttf")

    display = StaticFont(fraunces, {"wght": 700, "opsz": 72, "SOFT": 0, "WONK": 0})
    small = StaticFont(fraunces, {"wght": 700, "opsz": 9, "SOFT": 0, "WONK": 0})
    body = StaticFont(jakarta, {"wght": 400})

    mark = IrMark(display, dot_scale=1.25)
    small_mark = IrMark(small, dot_scale=1.45)

    AssetBuilder(mark, small_mark, display, body).build()
    print("done, asset pack is in " + OUT_DIR)


if __name__ == "__main__":
    main()
