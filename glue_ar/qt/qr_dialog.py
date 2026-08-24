from os.path import dirname

from glue_qt.utils import load_ui
from PIL.ImageQt import ImageQt
from qtpy.QtGui import QPixmap
from qtpy.QtWidgets import QDialog

from glue_ar.common.qr import create_qr


class QRDialog(QDialog):

    def __init__(self, parent, url=None, img=None):

        super().__init__(parent=parent)
        img = create_qr(url)
        self.img = ImageQt(img)
        self.pix = QPixmap.fromImage(self.img)
        self.ui = load_ui("qr_dialog.ui", self, directory=dirname(__file__))
        self.ui.label_url.setText(f"<a href=\"{url}\">Open 3D view</a>")
        self.ui.label_image.setPixmap(self.pix)
        width, height = img.size
        self.setFixedSize(width, height + 60)
