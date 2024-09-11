from qtpy.QtWidgets import QComboBox


def auto_accept_selectdialog(*args):
    def exec_replacement(dialog):
        dialog.select_all()
        dialog.accept()
    return exec_replacement


def auto_accept_messagebox(*args):
    def exec_replacement(box):
        box.accept()
    return exec_replacement


def dialog_auto_accept_with_options(**kwargs):
    def exec_replacement(dialog):
        if "layer" in kwargs:
            dialog.state.layer = kwargs["layer"]
        dialog.state.filetype = kwargs.get("filetype", "glTF")
        dialog.state.compression = kwargs.get("compression", "None")
        if "method" in kwargs:
            dialog.state.method = kwargs["method"]
        dialog.accept()
    return exec_replacement

def combobox_options(box: QComboBox):
    return [box.itemText(i) for i in range(box.count())]
