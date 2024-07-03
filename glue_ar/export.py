from os import remove
from os.path import abspath, dirname, join, split, splitext
from subprocess import run

import pyvista as pv
from gltflib.gltf import GLTF

from glue_vispy_viewers.scatter.scatter_viewer import Vispy3DScatterViewerState
from glue_vispy_viewers.volume.layer_state import VolumeLayerState

from glue_ar.scatter import scatter_layer_as_multiblock
from glue_ar.utils import bounds_3d_from_layers, xyz_bounds
from glue_ar.volume import bounds_3d, meshes_for_volume_layer


GLTF_PIPELINE_FILEPATH = join(dirname(abspath(__file__)), "js",
                              "node_modules", "gltf-pipeline",
                              "bin", "gltf-pipeline.js")


def export_meshes(meshes, output_path):
    plotter = pv.Plotter()
    for info in meshes.values():
        plotter.add_mesh(info["mesh"], color=info["color"], name=info["name"], opacity=info["opacity"])

    # TODO: What's the correct way to deal with this?
    if output_path.endswith(".obj"):
        plotter.export_obj(output_path)
    elif output_path.endswith(".gltf"):
        plotter.export_gltf(output_path)
    else:
        raise ValueError("Unsupported extension!")


def compress_gl(filepath):
    run(["node", GLTF_PIPELINE_FILEPATH, "-i", filepath, "-o", filepath, "-d"], capture_output=True)


def export_gl_by_extension(exporter, filepath):
    _, ext = splitext(filepath)
    if ext == ".glb":
        exporter.export_glb(filepath)
    elif ext == ".gltf":
        exporter.export_gltf(filepath)
    else:
        raise ValueError("File extension should be either .glb or .gltf")


# pyvista (well, VTK) doesn't set alphaMode in the exported GLTF
# which means that our opacity won't necessarily be respected.
# Maybe we could fix this upstream? But for now, let's just take
# matters into our own hands.
# We want alphaMode as BLEND
# see https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#alpha-coverage
def export_gl(plotter, filepath, with_alpha=True, compress=True):
    path, ext = splitext(filepath)
    gltf_path = filepath
    glb = ext == ".glb"
    if glb:
        gltf_path = path + ".gltf"

    plotter.export_gltf(gltf_path)

    gl = GLTF.load_gltf(gltf_path)
    if with_alpha and gl.model.materials is not None:
        for material in gl.model.materials:
            material.alphaMode = "BLEND"
    export_gl_by_extension(gl, filepath)
    if compress:
        compress_gl(filepath)
    if glb:
        remove(gltf_path)


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


    plotter = pv.Plotter()
    layer_states = [layer.state for layer in viewer.layers if layer.enabled and layer.state.visible]
    scatter_viewer = isinstance(viewer.state, Vispy3DScatterViewerState)
    if scatter_viewer:
        bounds = xyz_bounds(viewer.state)
    elif viewer.state.clip_data:
        bounds = bounds_3d(viewer.state)
    else:
        bounds = bounds_3d_from_layers(viewer.state, layer_states)
    frbs = {}
    for layer_state in layer_states:
        layer_info = state_dictionary.get(layer_state.layer.label, {})
        if layer_info:
            layer_info = layer_info.as_dict()
        if isinstance(layer_state, VolumeLayerState):
            meshes = meshes_for_volume_layer(viewer.state, layer_state,
                                             bounds=bounds,
                                             precomputed_frbs=frbs,
                                             **layer_info)
        else:
            meshes = scatter_layer_as_multiblock(viewer.state, layer_state,
                                                 scaled=scatter_viewer,
                                                 clip_to_bounds=viewer.state.clip_data,
                                                 **layer_info)
        for mesh_info in meshes:
            mesh = mesh_info.pop("mesh")
            if len(mesh.points) > 0:
                plotter.add_mesh(mesh, **mesh_info)

    return plotter


def export_to_ar(viewer, filepath, state_dict, compress=True):
    dir, base = split(filepath)
    name, ext = splitext(base)
    plotter = create_plotter(viewer, state_dict)
    html_path = join(dir, f"{name}.html")
    if ext in [".gltf", ".glb"]:
        export_gl(plotter, filepath, with_alpha=True, compress=compress)
        if compress:
            compress_gl(filepath)
        export_modelviewer(html_path, base, viewer.state.title)
    else:
        plotter.export_obj(filepath)
