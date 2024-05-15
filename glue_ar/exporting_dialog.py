from qtpy.QtWidgets import QDialog, QLabel, QVBoxLayout
from qtpy.QtCore import Qt, QTimer

__all__ = ['ExportingDialog']


class ExportingDialog(QDialog):

    _max_dots = 3

    def __init__(self, parent=None, filetype=None):
        super(ExportingDialog, self).__init__(parent=parent, flags=Qt.FramelessWindowHint)

        target = filetype if filetype else "3D file"
        self.message = f"Exporting to {target}"
        self.label = QLabel()
        self.label.setText(self.message)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        ending_spaces = " " * self._max_dots
        if not self.label.text().endswith(ending_spaces):
            self.label.setText(self.label.text() + ending_spaces)
        self.n_dots = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_timer_update)
        self.timer.start(750)

    def _on_timer_update(self):
        self.n_dots = (self.n_dots + 1) % (self._max_dots + 1)
        text = self.message + "." * self.n_dots
        self.label.setText(text)

    def close(self):
        super(ExportingDialog, self).close()
        self.timer.stop()
