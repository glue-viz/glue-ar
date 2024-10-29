from typing import Optional, Tuple

from pxr import Sdf, Usd, UsdGeom, UsdShade

from glue_ar.utils import color_identifier


def material_for_color(stage: Usd.Stage,
                       color: Tuple[int, int, int],
                       opacity: float,
                       metallic: float = 0.0,
                       roughness: float = 1.0,
                       identifier: Optional[str] = None) -> UsdShade.Material:

    identifier = identifier or color_identifier(color, opacity)
    material_key = f"/material_{identifier}"
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


def material_for_mesh(mesh: UsdGeom.Mesh) -> UsdShade.Material:
    prim = mesh.GetPrim()
    relationship = prim.GetRelationship("material:binding")
    target = relationship.GetTargets()[0]
    material_prim = prim.GetStage().GetPrimAtPath(target)
    return UsdShade.Material(material_prim)
