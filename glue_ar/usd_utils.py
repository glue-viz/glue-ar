from typing import Tuple

from pxr import Sdf, Usd, UsdShade

from glue_ar.utils import unique_id


def material_for_color(stage: Usd.Stage,
                       color: Tuple[int, int, int],
                       opacity: float,
                       metallic: float = 0.1,
                       roughness: float = 0.4) -> UsdShade.Material:

    material_key = f"/material_{unique_id()}"
    material = UsdShade.Material.Define(stage, material_key)
    shader_key = f"{material_key}/PBRShader"
    pbr_shader = UsdShade.Shader.Define(stage, shader_key)
    pbr_shader.CreateIdAttr("UsdPreviewSurface")
    pbr_shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(metallic)
    pbr_shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
    pbr_shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(tuple(c / 255 for c in color))
    pbr_shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(opacity)
    material.CreateSurfaceOutput().ConnectToSource(pbr_shader.ConnectableAPI(), "surface")

    return material
