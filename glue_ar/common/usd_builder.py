from pxr import Sdf, Usd, UsdGeom, UsdLux, UsdShade
from typing import Iterable, Tuple

from glue_ar.utils import unique_id

from typing import Self


class USDBuilder:

    def __init__(self):
        self._create_stage()
        self._material_map = {}

    def _create_stage(self):
        self.stage = Usd.Stage.CreateNew("export.usdc")

        # TODO: Do we want to make changing this an option?
        UsdGeom.SetStageUpAxis(self.stage, UsdGeom.Tokens.y)

        self.default_prim_key = "/world"
        self.default_prim = UsdGeom.Xform.Define(self.stage, self.default_prim_key).GetPrim()

        light = UsdLux.RectLight.Define(self.stage, "/light")
        light.CreateHeightAttr(-1)

    def _material_for_color(
        self,
        color: Tuple[int, int, int],
        opacity: float,
    ) -> UsdShade.Shader:

        rgba_tpl = (*color, opacity)
        material = self._material_map.get(rgba_tpl, None)
        if material is not None:
            return material

        material_key = f"/material_{unique_id()}"
        material = UsdShade.Material.Define(self.stage, material_key)
        shader_key = f"{material_key}/PBRShader"
        pbr_shader = UsdShade.Shader.Define(self.stage, shader_key)
        pbr_shader.CreateIdAttr("UsdPreviewSurface")
        pbr_shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.4)
        pbr_shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.1)
        pbr_shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(tuple(c / 255 for c in color))
        pbr_shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(opacity)
        material.CreateSurfaceOutput().ConnectToSource(pbr_shader.ConnectableAPI(), "surface")

        self._material_map[rgba_tpl] = material
        return material

    def add_shape(
        self,
        points: Iterable[Iterable[float]],
        triangles: Iterable[Iterable[int]],
        color: Tuple[int, int, int],
        opacity: float,
    ):
        """
        This returns the generated mesh rather than the builder instance.
        This breaks the builder pattern but we'll potentially want this reference to it
        for other meshes that we create 
        """
        xform_key = f"{self.default_prim_key}/xform_{unique_id()}"
        UsdGeom.Xform.Define(self.stage, xform_key)
        mesh_key = f"{xform_key}/level_{unique_id()}"
        mesh = UsdGeom.Mesh.Define(self.stage, mesh_key)
        mesh.CreateSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)
        mesh.CreatePointsAttr(points)
        mesh.CreateFaceVertexCountsAttr([3] * len(triangles))
        mesh.CreateFaceVertexIndicesAttr([int(idx) for tri in triangles for idx in tri])

        material = self._material_for_color(color, opacity)
        mesh.GetPrim().ApplyAPI(UsdShade.MaterialBindingAPI)
        UsdShade.MaterialBindingAPI(mesh).Bind(material)

        return mesh

    def add_translated_reference(self, prim, translation):
        xform_key = f"{self.default_prim_key}/xform_{unique_id()}"
        UsdGeom.Xform.Define(self.stage, xform_key)
        mesh_key = f"{xform_key}/level_{unique_id()}"
        mesh = UsdGeom.Mesh.Define(self.stage, mesh_key)
        references = mesh.GetReferences()
        references.AddInternalReference(prim.GetPrimPath())

        translation = mesh.AddTranslateOp()
        translation.set(value=translation)

        return mesh

    def export(self, filepath):
        self.stage.GetRootLayer().Export(filepath)
