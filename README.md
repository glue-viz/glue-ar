# glue-ar

Right now, this is primarily just for experimenting with exporting AR-compatible files from glue, along with creating utilities to view other 3D file formats in AR. All of the code here is very rough. This is still at a "let's get this to work" point - we can think about things like overall code structure once we have some working implementations that we're satisfied with.

The only particular principle I've been trying to follow is to make anything glue-related depend only on state (viewer and/or layer), unless that absolutely can't happen for some reason. From my experience with glue-plotly, this will help us to reuse as much as possible between different glue frontends (e.g. glue-qt and glue-jupyter). The approach I've been taking so far is to use pyvista's `Plotter` to export to a 3D-compatible format - in particular, pyvista can export to OBJ and glTF.


## Relevant file formats

Obviously various file formats and what we do/don't want to support is something we want to think about. Relevant file formats include:

* [glTF](https://en.wikipedia.org/wiki/GlTF)
* [USDZ](https://en.wikipedia.org/wiki/Universal_Scene_Description)
* [OBJ/MTL](https://en.wikipedia.org/wiki/Wavefront_.obj_file)
* [STL](https://en.wikipedia.org/wiki/STL_(file_format))

### Conversion tools

Some of these are just for quick testing purposes, others might be things we could incorporate into a toolchain

* [glTF to USDZ converter](https://products.aspose.app/3d/conversion/gltf-to-usdz) (under 100 MB)
* [gltz2usd](https://github.com/kcoley/gltf2usd)


## Relevant libraries/software

* [model-viewer](https://modelviewer.dev/) - This is a super-cool web component that allows for easily displaying a model in AR via a web page. It only supports GLTF/GLB and USDZ, but it's really easy to use and seems to work pretty well. I've been using this to test out gltf files that I've been creating.
* [gltflib](https://github.com/lukas-shawford/gltflib)A - Python library for creating/manipulating glTF files

## Other cool stuff

* [glTF Viewer](https://gltf-viewer.donmccurdy.com/) - As the name implies, used for viewer glTF files
