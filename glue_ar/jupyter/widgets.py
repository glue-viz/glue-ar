from os.path import join
from typing import List, Tuple

from echo import CallbackProperty, HasCallbackProperties
from glue_jupyter.common.toolbar_vuetify import read_icon
from glue_jupyter.link import link
import ipyvuetify as v
from ipywidgets import DOMWidget

from glue_ar.utils import RESOURCES_DIR


def info_tooltip(cb_property: CallbackProperty) -> List[str]:
    if cb_property.__doc__:
        return cb_property.__doc__.replace(". ", ".\n").split("\n")
    else:
        return []


def info_icon(cb_property: CallbackProperty) -> v.Tooltip:
    img_path = join(RESOURCES_DIR, "info.png")
    icon_src = read_icon(img_path, "image/png")
    tooltip_children = [v.Html(tag="div", children=[text]) for text in info_tooltip(cb_property) if text]
    button = v.Tooltip(
        top=True,
        v_slots=[{
            "name": "activator",
            "variable": "tooltip",
            "children": [
                v.Img(v_on="tooltip.on", src=icon_src,
                      height=20, width=20,
                      max_width=20, max_height=20),
            ],
        }],
        children=tooltip_children,
    )
    return button


def boolean_callback_widgets(instance: HasCallbackProperties,
                             property: str,
                             display_name: str,
                             **kwargs) -> Tuple[DOMWidget]:

    instance_type = type(instance)
    cb_property = getattr(instance_type, property)

    checkbox = v.Checkbox(label=display_name)
    link((instance, property), (checkbox, 'value'))

    if cb_property.__doc__:
        icon = info_icon(cb_property)
        return (checkbox, icon)
    else:
        return (checkbox,)


def number_callback_widgets(instance: HasCallbackProperties,
                            property: str,
                            display_name: str,
                            label_for_value=False,
                            **kwargs) -> Tuple[DOMWidget]:

    value = getattr(instance, property)
    instance_type = type(instance)
    cb_property = getattr(instance_type, property)
    t = type(value)

    min = getattr(cb_property, 'min_value', 1 if t is int else 0.01)
    max = getattr(cb_property, 'max_value', 100 * min)
    step = getattr(cb_property, 'resolution', None)
    if step is None:
        step = 1 if t is int else 0.01

    slider = v.Slider(
            min=min,
            max=max,
            step=step,
            label=display_name,
            hide_details=True,
            thumb_label=f"{value:g}" if label_for_value else False,
    )
    link((instance, property),
         (slider, 'v_model'))

    if cb_property.__doc__:
        icon = info_icon(cb_property)
        return (slider, icon)
    else:
        return (slider,)


def widgets_for_callback_property(
        instance: HasCallbackProperties,
        property: str,
        display_name: str,
        **kwargs,
) -> Tuple[DOMWidget]:

    t = type(getattr(instance, property))
    if t is bool:
        return boolean_callback_widgets(instance, property, display_name)
    elif t in (int, float):
        return number_callback_widgets(instance, property, display_name)
    else:
        raise ValueError("Unsupported callback property type!")
