from os import remove
from os.path import join, splitext
from subprocess import run

import pyvista as pv
from gltflib.gltf import GLTF


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
    location = join("js", "node_modules", "gltf-pipeline", "bin", "gltf-pipeline.js")
    run(["node", location, "-i", filepath, "-o", filepath, "-d"], capture_output=True)


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
    if glb:
        remove(gltf_path)


def export_modelviewer(output_path, gltf_path, alt_text):
    html = f"""
        <html>
        <body>
            <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.3.0/model-viewer.min.js"></script>
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
