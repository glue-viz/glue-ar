import ipyvuetify as v  # noqa
from ipyvuetify.VuetifyTemplate import VuetifyTemplate
from ipywidgets import DOMWidget, VBox, widget_serialization
from os.path import dirname, join
import traitlets
from typing import Callable, List, Optional

from echo import HasCallbackProperties
from glue.core.state_objects import State
from glue.viewers.common.viewer import Viewer
from glue_jupyter.link import link
from glue_jupyter.utils import ipyvue
from glue_jupyter.state_traitlets_helpers import GlueState
from glue_jupyter.vuetify_helpers import link_glue_choices

from glue_ar.common.export_dialog_base import ARExportDialogBase


# We need to register our int-field component
ipyvue.register_component_from_file( 
    None, "int-field", join(dirname(__file__), "int_field.vue"))


def widgets_for_property(instance: HasCallbackProperties,
                        property: str,
                        display_name: str) -> List[DOMWidget]:

    value = getattr(instance, property)
    t = type(value)
    if t is bool:
        widget = v.Checkbox(label=display_name)
        link((instance, property), (widget, 'value'))
        return [widget]
    elif t in (int, float):
        # TODO: How to do text field validation Python-side?
        # Are the `link` conversion functions enough?
        widget = v.TextField(label=display_name)
        link((instance, property),
             (widget, 'v_model'),
             lambda value: str(value),
             lambda text: t(text))
        return [widget]
    else:
        return []


class JupyterARExportDialog(ARExportDialogBase, VuetifyTemplate):

    template_file = (__file__, "export_dialog.vue")
    dialog_state = GlueState().tag(sync=True)
    dialog_open = traitlets.Bool().tag(sync=True)

    layer_items = traitlets.List().tag(sync=True)
    layer_selected = traitlets.Int().tag(sync=True)

    compression_items = traitlets.List().tag(sync=True)
    compression_selected = traitlets.Int().tag(sync=True)

    filetype_items = traitlets.List().tag(sync=True)
    filetype_selected = traitlets.Int().tag(sync=True)

    method_items = traitlets.List().tag(sync=True)
    method_selected = traitlets.Int().tag(sync=True)

    layer_layout = traitlets.Instance(DOMWidget).tag(sync=True, **widget_serialization)

    def __init__(self,
                 viewer: Viewer,
                 display: Optional[bool] = False,
                 on_cancel: Optional[Callable] = None,
                 on_export: Optional[Callable] = None):
        ARExportDialogBase.__init__(self, viewer=viewer)
        self.layer_layout = VBox()
        VuetifyTemplate.__init__(self)

        self._on_layer_change(self.state.layer)

        link_glue_choices(self, self.state, 'layer')
        link_glue_choices(self, self.state, 'compression')
        link_glue_choices(self, self.state, 'filetype')
        link_glue_choices(self, self.state, 'method')

        self.dialog_open = display
        self.on_cancel = on_cancel
        self.on_export = on_export
        self.dialog_state = self.state

    def _update_layer_ui(self, state: State):
        if self.layer_layout is not None:
            for widget in self.layer_layout.children:
                widget.close()

        widgets = []
        for property, _ in state.iter_callback_properties():
            name = self.display_name(property)
            widgets.extend(widgets_for_property(state, property, name))
        self.layer_layout = VBox(children=widgets)

    def _on_method_change(self, method_name: str):
        super()._on_method_change(method_name)
        state = self._layer_export_states[self.state.layer][method_name]
        self._update_layer_ui(state)

    def vue_cancel_dialog(self, *args):
        self.state = None
        self.state_dictionary = {}
        self.dialog_open = False
        if self.on_cancel:
            self.on_cancel()

    def vue_export_viewer(self, *args):
        self.dialog_open = False
        if self.on_export:
            self.on_export()
