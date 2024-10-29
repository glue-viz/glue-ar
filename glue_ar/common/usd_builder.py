from collections import defaultdict
from os import extsep, remove
from os.path import splitext

from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdShade, UsdUtils
from typing import Dict, Iterable, Optional, Tuple
from glue_ar.common.scatter import Point

from glue_ar.usd_utils import material_for_color, material_for_mesh
from glue_ar.utils import unique_id


MaterialInfo = Tuple[int, int, int, float, float, float]


class USDBuilder:

    def __init__(self, filepath: str):
        base, ext = splitext(filepath)
        if ext == ".usdz":
            filepath = f"{base}{extsep}usdc"
        self._create_stage(filepath)
        self._material_map: Dict[MaterialInfo, UsdShade.Shader] = {}

    def _sanitize(self, identifier: str) -> str:
        # TODO: Do this in a single pass
        for char in ("-", "(", ")"):
            identifier = identifier.replace(char, "_")
        return identifier

    def _create_stage(self, filepath: str):
        self.stage = Usd.Stage.CreateNew(self._sanitize(filepath))

        # TODO: Do we want to make changing this an option?
        UsdGeom.SetStageUpAxis(self.stage, UsdGeom.Tokens.y)

        self.default_prim_key = "/world"
        self.default_prim = UsdGeom.Xform.Define(self.stage, self.default_prim_key).GetPrim()
        self.stage.SetDefaultPrim(self.default_prim)

        self._geom_counts: Dict[str, int] = defaultdict(int)

        light = UsdLux.RectLight.Define(self.stage, "/light")
        light.CreateHeightAttr(-1)

    def _material_for_color(self,
                            color: Tuple[int, int, int],
                            opacity: float,
                            metallic: float,
                            roughness: float) -> UsdShade.Shader:

        color_key = (*color, opacity, metallic, roughness)
        material = self._material_map.get(color_key, None)
        if material is not None:
            return material

        material = material_for_color(self.stage,
                                      color=color,
                                      opacity=opacity,
                                      metallic=metallic,
                                      roughness=roughness)
        self._material_map[color_key] = material
        return material

    def add_mesh(self,
                 points: Iterable[Iterable[float]],
                 triangles: Iterable[Iterable[int]],
                 color: Tuple[int, int, int],
                 opacity: float,
                 metallic: float = 0.0,
                 roughness: float = 1.0,
                 identifier: Optional[str] = None) -> UsdGeom.Mesh:
        """
        This returns the generated mesh rather than the builder instance.
        This breaks the builder pattern but we'll potentially want this reference to it
        for other meshes that we create.
        """
        identifier = identifier or unique_id()
        identifier = self._sanitize(identifier)
        count = self._geom_counts[identifier]
        xform_key = f"{self.default_prim_key}/xform_{identifier}_{count}"
        UsdGeom.Xform.Define(self.stage, xform_key)
        mesh_key = f"{xform_key}/mesh_{identifier}_{count}"
        self._geom_counts[identifier] += 1
        mesh = UsdGeom.Mesh.Define(self.stage, mesh_key)
        mesh.CreateSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)
        mesh.CreatePointsAttr(points)
        mesh.CreateFaceVertexCountsAttr([3] * len(triangles))
        mesh.CreateFaceVertexIndicesAttr([int(idx) for tri in triangles for idx in tri])

        material = self._material_for_color(color, opacity, metallic=metallic, roughness=roughness)
        mesh.GetPrim().ApplyAPI(UsdShade.MaterialBindingAPI)
        UsdShade.MaterialBindingAPI(mesh).Bind(material)

        return mesh

    def add_translated_reference(self,
                                 mesh: UsdGeom.Mesh,
                                 translation: Tuple[float, float, float],
                                 material: Optional[UsdShade.Material] = None,
                                 identifier: Optional[str] = None) -> UsdGeom.Mesh:
        prim = mesh.GetPrim()
        identifier = identifier or unique_id()
        identifier = self._sanitize(identifier)
        count = self._geom_counts[identifier]
        xform_key = f"{self.default_prim_key}/xform_{identifier}_{count}"
        UsdGeom.Xform.Define(self.stage, xform_key)
        new_mesh_key = f"{xform_key}/mesh_{identifier}_{count}"
        self._geom_counts[identifier] += 1
        new_mesh = UsdGeom.Mesh.Define(self.stage, new_mesh_key)
        new_prim = new_mesh.GetPrim()

        references = new_prim.GetReferences()
        references.AddInternalReference(prim.GetPrimPath())

        if material is None:
            material = material_for_mesh(mesh)
        new_mesh.GetPrim().ApplyAPI(UsdShade.MaterialBindingAPI)
        UsdShade.MaterialBindingAPI(new_mesh).Bind(material)

        translate_op = new_mesh.AddTranslateOp()
        translate_op.Set(value=translation)

        return mesh

    def add_points(self,
                   points: Iterable[Point],
                   colors: Iterable[Tuple[int, int, int]],
                   identifier: Optional[str] = None) -> UsdGeom.Points:

        identifier = identifier or unique_id()
        identifier = self._sanitize(identifier)
        count = self._geom_counts[identifier]
        xform_key = f"{self.default_prim_key}/xform_{identifier}_{count}"
        UsdGeom.Xform.Define(self.stage, xform_key)
        points_key = f"{xform_key}/points_{identifier}_{count}"
        self._geom_counts[identifier] += 1
        geom = UsdGeom.Points.Define(self.stage, points_key)
        point_vecs = [Gf.Vec3f(*point) for point in points]
        geom.CreatePointsAttr(point_vecs)
        widths_var = geom.CreateWidthsAttr()
        widths = [1.0 for _ in points]
        widths_var.Set(widths)
        # primvars = UsdGeom.PrimvarsAPI(geom.GetPrim())
        # colorvar = primvars.CreatePrimvar("displayColor", Sdf.ValueTypeNames.Color3f)
        # colorvar.Set([Gf.Vec3f(*color) for color in colors])

        return geom

    def export(self, filepath: str):
        base, ext = splitext(filepath)
        if ext == ".usdz":
            usdc_path = f"{base}{extsep}usdc"
            self.stage.GetRootLayer().Export(usdc_path)
            UsdUtils.CreateNewUsdzPackage(usdc_path, filepath)
            remove(usdc_path)
        else:
            self.stage.GetRootLayer().Export(filepath)

    def build_and_export(self, filepath: str):
        self.export(filepath)
