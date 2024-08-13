from collections import defaultdict
from inspect import getfullargspec
from os.path import abspath, dirname, join, splitext
from subprocess import run
from typing import Dict
from glue.core.state_objects import State
from glue_vispy_viewers.scatter.viewer_state import Vispy3DViewerState
from glue_vispy_viewers.volume.layer_state import VolumeLayerState


from glue_ar.common.export_options import ar_layer_export
from glue_ar.common.gltf_builder import GLTFBuilder
from glue_ar.common.usd_builder import USDBuilder
from glue_ar.utils import Bounds, BoundsWithResolution, export_label_for_layer

from typing import List, Tuple, Union


NODE_MODULES_DIR = join(abspath(join(dirname(abspath(__file__)), "..")),
                        "js", "node_modules")


GLTF_PIPELINE_FILEPATH = join(NODE_MODULES_DIR, "gltf-pipeline", "bin", "gltf-pipeline.js")
GLTFPACK_FILEPATH = join(NODE_MODULES_DIR, "gltfpack", "cli.js")


_BUILDERS = {
    "gltf": GLTFBuilder,
    "glb": GLTFBuilder,
    "usda": USDBuilder,
    "usdc": USDBuilder
}


def export_viewer(viewer_state: Vispy3DViewerState,
                  layer_states: List[VolumeLayerState],
                  bounds: Union[Bounds, BoundsWithResolution],
                  state_dictionary: Dict[str, Tuple[str, State]],
                  filepath: str):

    ext = splitext(filepath)[1][1:]
    builder_cls = _BUILDERS[ext]
    count = len(getfullargspec(builder_cls.__init__)[0])
    builder_args = [filepath] if count > 1 else []
    builder = builder_cls(*builder_args)
    layer_groups = defaultdict(list)
    export_groups = defaultdict(list)
    for layer_state in layer_states:
        name, export_state = state_dictionary[export_label_for_layer(layer_state)]
        key = (type(layer_state), name)
        layer_groups[key].append(layer_state)
        export_groups[key].append(export_state)

    for key, layer_states in layer_groups.items():
        export_states = export_groups[key]
        layer_state_cls, name = key
        spec = ar_layer_export.export_spec(layer_state_cls, name, ext)
        if spec.multiple:
            spec.export_method(builder, viewer_state, layer_states, export_states, bounds)
        else:
            for layer_state, export_state in zip(layer_states, export_states):
                spec.export_method(builder, viewer_state, layer_state, export_state, bounds)

    builder.build_and_export(filepath)


def compress_gltf_pipeline(filepath):
    run(["node", GLTF_PIPELINE_FILEPATH, "-i", filepath, "-o", filepath, "-d"], capture_output=True)


def compress_gltfpack(filepath):
    run(["node", GLTFPACK_FILEPATH, "-i", filepath, "-o", filepath], capture_output=True)


COMPRESSORS = {
    "draco": compress_gltf_pipeline,
    "meshoptimizer": compress_gltfpack
}


def compress_gl(filepath, method="draco"):
    compressor = COMPRESSORS.get(method, None)
    if compressor is None:
        raise ValueError("Invalid compression method specified")
    compressor(filepath)


def export_modelviewer(output_path, gltf_path, alt_text):
    mv_url = "https://ajax.googleapis.com/ajax/libs/model-viewer/3.3.0/model-viewer.min.js"
    html = f"""
    <html>
        <body>
            <script type="module" src="{mv_url}"></script>
            <style>
        model-viewer {{
          width: 100%;
          height: 100%;
        }}

        /* This keeps child nodes hidden while the element loads */
        :not(:defined) > * {{
          display: none;
        }}
        .ar-button {{
          background-repeat: no-repeat;
          background-size: 20px 20px;
          background-position: 12px 50%;
          background-color: #fff;
          position: absolute;
          left: 50%;
          transform: translateX(-50%);
          bottom: 16px;
          padding: 0px 16px 0px 40px;
          font-family: Roboto Regular, Helvetica Neue, sans-serif;
          font-size: 14px;
          color:#4285f4;
          height: 36px;
          line-height: 36px;
          border-radius: 18px;
          border: 1px solid #DADCE0;
        }}
        .ar-button:active {{
          background-color: #E8EAED;
        }}
        .ar-button:focus {{
          outline: none;
        }}
        .ar-button:focus-visible {{
          outline: 1px solid #4285f4;
        }}
        .hotspot {{
          position: relative;
          background: #ddd;
          border-radius: 32px;
          box-sizing: border-box;
          border: 0;
          --min-hotspot-opacity: 0.5;
          width: 24px;
          height: 24px;
          padding: 8px;
          cursor: pointer;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.25);
        }}
        .hotspot:focus {{
          border: 4px solid rgb(0, 128, 200);
          width: 32px;
          height: 32px;
          outline: none;
        }}
        .hotspot > * {{
          transform: translateY(-50%);
          opacity: 1;
        }}
        .hotspot:not([data-visible]) > * {{
          pointer-events: none;
          opacity: 0;
          transform: translateY(calc(-50% + 4px));
          transition: transform 0.3s, opacity 0.3s;
        }}
        .info {{
          display: block;
          position: absolute;
          font-family: Futura, Helvetica Neue, sans-serif;
          color: rgba(0, 0, 0, 0.8);
          font-weight: 700;
          font-size: 18px;
          max-width: 128px;
          padding: 0.5em 1em;
          background: #ddd;
          border-radius: 4px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.25);
          left: calc(100% + 1em);
          top: 50%;
        }}
    </style>
    <model-viewer
        src="{gltf_path}"
        camera-orbit="0.9677rad 1.2427rad auto"
        shadow-intensity="1"
        ar
        ar-modes="webxr quick-look"
        camera-controls
        alt="{alt_text}"
    >
        <button slot="ar-button" class="ar-button">View in your space</button>
        </model-viewer>
        </body>
    </html>
    """

    with open(output_path, 'w') as f:
        f.write(html)
