from PIL import Image, ImageEnhance, ImageOps

LONG_EDGE_PX = 600


def resize_long_edge(image: Image.Image, long_edge: int = LONG_EDGE_PX) -> Image.Image:
    w, h = image.size
    if max(w, h) <= long_edge:
        return image
    if w >= h:
        new_w = long_edge
        new_h = round(h * (long_edge / w))
    else:
        new_h = long_edge
        new_w = round(w * (long_edge / h))
    return image.resize((new_w, new_h), Image.LANCZOS)


class ImageStyler:
    def apply(self, image: Image.Image) -> Image.Image:
        raise NotImplementedError


class PassthroughStyler(ImageStyler):
    def apply(self, image: Image.Image) -> Image.Image:
        return resize_long_edge(image).convert("RGB")


class DuotoneStyler(ImageStyler):
    DEFAULT_SHADOW = (26, 40, 28)
    DEFAULT_MID = (45, 68, 48)
    DEFAULT_HIGHLIGHT = (240, 243, 234)
    DEFAULT_CONTRAST = 1.1

    def __init__(
        self,
        shadow: tuple[int, int, int] | None = None,
        mid: tuple[int, int, int] | None = None,
        highlight: tuple[int, int, int] | None = None,
        contrast: float | None = None,
    ):
        self.shadow = shadow if shadow is not None else self.DEFAULT_SHADOW
        self.mid = mid if mid is not None else self.DEFAULT_MID
        self.highlight = highlight if highlight is not None else self.DEFAULT_HIGHLIGHT
        self.contrast = contrast if contrast is not None else self.DEFAULT_CONTRAST

    def apply(self, image: Image.Image) -> Image.Image:
        img = resize_long_edge(image)
        gray = ImageOps.grayscale(img)
        gray = ImageEnhance.Contrast(gray).enhance(self.contrast)
        return ImageOps.colorize(gray, black=self.shadow, white=self.highlight, mid=self.mid)


class ColorGradeStyler(ImageStyler):
    saturation = 0.80
    contrast = 1.06
    wash = (45, 68, 48)
    wash_strength = 0.10

    def apply(self, image: Image.Image) -> Image.Image:
        img = resize_long_edge(image).convert("RGB")
        img = ImageEnhance.Color(img).enhance(self.saturation)
        img = ImageEnhance.Contrast(img).enhance(self.contrast)
        wash_layer = Image.new("RGB", img.size, self.wash)
        return Image.blend(img, wash_layer, self.wash_strength)
