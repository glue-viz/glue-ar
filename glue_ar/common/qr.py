import os
from io import BytesIO
from PIL import Image
import socket
import segno


GLUE_LOGO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logo.png"))
GLUE_RED = "#eb1c24"


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def create_qr(url, with_logo=True, color=GLUE_RED, error_level="H"):
    qr = segno.make_qr(url, error=error_level)
    out = BytesIO()
    qr.save(out, kind="png", scale=10, dark=color, light="white")
    out.seek(0)
    img = Image.open(out)
    img = img.convert("RGB")
    if with_logo:
        width, height = img.size
        logo_max_size = height // 3
        logo_img = Image.open(GLUE_LOGO)
        # Resize the logo to logo_max_size
        logo_img.thumbnail((logo_max_size, logo_max_size), resample=Image.Resampling.LANCZOS)
        # Calculate the center of the QR code
        box = ((width - logo_img.size[0]) // 2, (height - logo_img.size[1]) // 2)
        img.paste(logo_img, box)
    return img
