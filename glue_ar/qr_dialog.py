from os.path import dirname

from PIL.ImageQt import ImageQt
from glue_qt.utils import load_ui
from qtpy.QtWidgets import QDialog
from qtpy.QtGui import QPixmap


class QRDialog(QDialog):

    def __init__(self, parent=None, img=None):
        
        super(QRDialog, self).__init__(parent=parent)

        self.img = ImageQt(img)
        self.pix = QPixmap.fromImage(self.img)
        self.ui = load_ui("qr_dialog.ui", self, directory=dirname(__file__))
        self.ui.label_image.setPixmap(self.pix)

