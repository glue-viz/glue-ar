import os
from io import BytesIO
from PIL import Image
import socket
import segno


GLUE_LOGO = os.path.abspath(os.path.join(os.path.dirname(__file__), "logo.png"))
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


def create_qr(url):
    qr = segno.make_qr(url)
    out = BytesIO()
    qr.save(out, kind="png", scale=7, dark=GLUE_RED, light="white")
    out.seek(0)
    img = Image.open(out)
    img = img.convert("RGB")
    width, height = img.size
    logo_max_size = height // 3
    logo_img = Image.open(GLUE_LOGO)
    # Resize the logo to logo_max_size
    logo_img.thumbnail((logo_max_size, logo_max_size), Image.Resampling.LANCZOS)
    # Calculate the center of the QR code
    box = ((width - logo_img.size[0]) // 2, (height - logo_img.size[1]) // 2)
    img.paste(logo_img, box)
    return img

