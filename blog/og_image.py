import hashlib
import os
from io import BytesIO

import requests
from django.conf import settings
from PIL import Image

OG_WIDTH = 1200
OG_HEIGHT = 630
MARGIN = 0.05
BACKGROUND = (16, 182, 106)


def build_og_image(source):
    """Generate a 1200x630 OG image with `source` centered and margins.

    Returns a relative url path like "/media/og/<hash>.jpg" or None
    if the source image can not be loaded.
    """
    if not source:
        return None
    src_img = _load_image(source)
    if src_img is None:
        return None

    key = _source_key(source)
    filename = "{}_og.jpg".format(key)
    abs_path = os.path.join(settings.MEDIA_ROOT, 'og', filename)
    if not os.path.exists(abs_path):
        canvas = Image.new('RGB', (OG_WIDTH, OG_HEIGHT), BACKGROUND)
        box_w = int(OG_WIDTH * (1 - 2 * MARGIN))
        box_h = int(OG_HEIGHT * (1 - 2 * MARGIN))
        src_img.thumbnail((box_w, box_h), Image.LANCZOS)
        x = (OG_WIDTH - src_img.width) // 2
        y = (OG_HEIGHT - src_img.height) // 2
        canvas.paste(src_img, (x, y))

        directory = os.path.dirname(abs_path)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        tmp_path = abs_path + '.tmp'
        canvas.save(tmp_path, 'JPEG', quality=88)
        os.replace(tmp_path, abs_path)

    return '/media/og/{}'.format(filename)


def _source_key(source):
    h = hashlib.md5()
    h.update(source.encode('utf-8'))
    path = _local_path(source)
    if path and os.path.exists(path):
        h.update(str(os.path.getmtime(path)).encode('utf-8'))
    return h.hexdigest()


def _local_path(source):
    if source.startswith('/media/'):
        return os.path.join(settings.MEDIA_ROOT, source[len('/media/'):])
    return None


def _load_image(source):
    if source.startswith('http'):
        try:
            data = requests.get(source, timeout=(3, 5)).content
            img = Image.open(BytesIO(data))
            img.load()
        except Exception:
            return None
    else:
        path = _local_path(source)
        if not path or not os.path.exists(path):
            return None
        try:
            img = Image.open(path)
            img.load()
        except Exception:
            return None
    img = img.convert('RGBA')
    bg = Image.new('RGBA', img.size, BACKGROUND + (255,))
    bg.paste(img, (0, 0), img)
    return bg.convert('RGB')
