from os import getcwd
from os.path import exists

from glue.config import viewer_tool
from glue.viewers.common.tool import Tool

from glue_ar.common.export import export_viewer
from glue_ar.jupyter.export_dialog import JupyterARExportDialog
from glue_ar.utils import AR_ICON, is_volume_viewer, xyz_bounds

import ipyvuetify as v  # noqa
from ipywidgets import HBox, Layout # noqa
from IPython.display import display  # noqa
from ipyfilechooser import FileChooser


__all__ = ["JupyterARExportTool"]


@viewer_tool
class JupyterARExportTool(Tool):
    icon = AR_ICON
    tool_id = "save:ar_jupyter"
    action_text = "Export 3D file"
    tool_tip = "Export the current view to a 3D file"

    def activate(self):

        done = False

        def on_cancel():
            nonlocal done
            done = True

        self.export_dialog = JupyterARExportDialog(
                                viewer=self.viewer,
                                display=True,
                                on_cancel=on_cancel,
                                on_export=self._open_file_dialog)
        with self.viewer.output_widget:
            display(self.export_dialog)

    def _open_file_dialog(self):
        file_chooser = FileChooser(getcwd(), filter_pattern=f"*.{self.export_dialog.state.filetype}")
        ok_btn = v.Btn(color='success', disabled=True, children=['Ok'])
        close_btn = v.Btn(color='error', children=['Close'])
        dialog = v.Dialog(
            width='500',
            persistent=True,
            children=[
                v.Card(children=[
                    v.CardTitle(primary_title=True,
                                children=["Select output filepath"]),
                    file_chooser,
                    HBox(children=[ok_btn, close_btn],
                         layout=Layout(justify_content='flex-end', grid_gap='5px'))
                ], layout=Layout(padding='8px'))
            ]
        )

        def on_ok_click(button, event, data):
            self.maybe_save_figure(file_chooser.selected)

        def on_close_click(button, event, data):
            self.viewer.output_widget.clear_output()
            dialog.close()

        def on_selected_change(chooser):
            ok_btn.disabled = not bool(chooser.selected_filename)

        ok_btn.on_event('click', on_ok_click)
        close_btn.on_event('click', on_close_click)
        file_chooser.register_callback(on_selected_change)

        with self.viewer.output_widget:
            dialog.v_model = True
            display(dialog)

    def maybe_save_figure(self, filepath):
        if exists(filepath):
            yes_btn = v.Btn(color='success', children=["Yes"])
            no_btn = v.Btn(color='error', children=["No"])
            check_dialog = v.Dialog(
                width='500',
                persistent=True,
                children=[
                    v.Card(children=[
                        v.CardText(children=["This filepath already exists. Are you sure you want to overwrite it?"]),
                        HBox(children=[yes_btn, no_btn], layout=Layout(justify_content='flex-end', grid_gap='5px'))
                    ])
                ]
            )

            def on_yes_click(button, event, data):
                self.save_figure(filepath)
                self.viewer.output_widget.clear_output()

            def on_no_click(button, event, data):
                check_dialog.v_model = False

            yes_btn.on_event('click', on_yes_click)
            no_btn.on_event('click', on_no_click)
            with self.viewer.output_widget:
                check_dialog.v_model = True
                display(check_dialog)
        else:
            self.save_figure(filepath)
            self.viewer.output_widget.clear_output()

    def save_figure(self, filepath):
        bounds = xyz_bounds(self.viewer.state, with_resolution=is_volume_viewer(self.viewer))
        layer_states = [layer.state for layer in self.viewer.layers if layer.enabled and layer.state.visible]
        state_dict = self.export_dialog.state_dictionary
        export_viewer(viewer_state=self.viewer.state,
                      layer_states=layer_states,
                      bounds=bounds,
                      state_dictionary=state_dict,
                      filepath=filepath,
                      compression=self.export_dialog.state.compression)
