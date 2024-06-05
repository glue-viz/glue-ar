# glue-ar

This package is an experimental plugin for [glue](<ttps://glueviz.org/>) that allows exporting augmented reality (AR)
figures out of the 3D scatter and volume viewers from [vispy viewer](https://github.com/glue-viz/glue-vispy-viewers>).
Currently this ability is exposed via viewer tools that save a 3D file representing the current view. Currently supported
file formats include [OBJ](https://en.wikipedia.org/wiki/Wavefront_.obj_file) and [glTF](https://www.khronos.org/gltf/).
This export is performed used [pyvista](https://pyvista.org/), which provides a Python interface to the [Visualization Toolkit (VTK)](https://vtk.org/).


## Installation

This package is not (yet) listed on PyPI, so to install you'll need to clone this repository and install from source.

```
git clone https://github.com/Carifio24/glue-ar
cd glue-ar
pip install .  # Use `pip install -e .` to install in [editable mode](https://setuptools.pypa.io/en/latest/userguide/development_mode.html)
```


## Viewer tools

The AR export tools are exposed in the toolbar as subtools of the "save" meta-tool, and can be accessed from its dropdown menu.

![Qt viewer tool](https://raw.githubusercontent.com/Carifio24/glue-ar/main/doc/viewer_tool.gif)

## Sharing figures

### model-viewer

If glTF is selected as the output file format, an HTML file is exported in addition to the glTF. This HTML file provides a display
of the exported figure using the [model-viewer](https://modelviewer.dev) web component. This model-viewer page provides a THREE.js-powered
glTF viewer that, on an Android or iOS device, allows viewing the glTF file using the hardware AR capability. Additionally, this exported HTML
has no additional dependencies and can be served using static file hosting.

## Draco compression

The files exported by glue-ar can, in their original form, be quite large. In order to mitigate this problem, glue-ar allows using 
[Draco compression](https://google.github.io/draco/) via the [gltf-pipeline](https://github.com/CesiumGS/gltf-pipeline) package. Using Draco compression
allows for a considerable reduction in file size (often an order of magnitude or more), and Draco-compressed files can be read by model-viewer.

## CoSpaces

Another popular option for sharing 3D files in augmented reality is [CoSpaces](https://www.cospaces.io), which allows viewing 3D files in a browser
or on a mobile device via a dedicated app. The CoSpaces app allows viewing figures in AR on a flat surface directly, or using the [Merge Cube](https://mergeedu.com/cube)
to allow for a more tangible AR experience.

CoSpaces supports both OBJ and glTF file formats, so the outputs of glue-ar can be used in CoSpaces without modification. It is our aim to eventually allow
automatic CoSpaces upload, but for now sharing your AR figures to CoSpaces requires some manual steps (as well as a CoSpaces account).

To create a scene with your newly-exported figure, do the following:
1. Go to the CoSpaces website and log in to your account
2. On the left side menu, navigate to "CoSpaces"
3. Click the "Create CoSpace" button
4. Select the environment you want:
    * 3D environment > Empty scene for tabletop AR
    * MERGE Cube > Empty scene to use the MERGE Cube (note that creating a MERGE Cube requires a plan addon)
5. In the bottom left corner, select Upload > 3D models, then press the Upload button to the right
6. Select your 3D model
    * Note that CoSpaces currently does not support the extension needed for Draco compression
7. Done!
