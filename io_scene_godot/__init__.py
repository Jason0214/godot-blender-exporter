"""
Export to godot's escn file format - a format that Godot can work with
without significant importing (it's the same as Godot's tscn format).
"""
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from bpy_extras.io_utils import ExportHelper
from .structures import ValidationError
from . import export_godot

bl_info = {  # pylint: disable=invalid-name
    "name": "Godot Engine Exporter",
    "author": "Juan Linietsky",
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "description": ("Export Godot Scenes to a format that can be efficiently "
                    "imported."),
    "warning": "",
    "wiki_url": ("https://godotengine.org"),
    "tracker_url": "https://github.com/godotengine/blender-exporter",
    "support": "OFFICIAL",
    "category": "Import-Export"
}


class ExportGodot(bpy.types.Operator, ExportHelper):
    """Selection to Godot"""
    # XXX: Change bl_idname to make accessing addon nicer. Addon is called
    # through bpy.ops.<bl_idname>.
    bl_idname = "export_godot.escn"
    bl_label = "Export to Godot"
    bl_options = {"PRESET"}

    filename_ext = ".escn"
    filter_glob: StringProperty(default="*.escn", options={"HIDDEN"})

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling
    object_types: EnumProperty(
        name="Object Types",
        options={"ENUM_FLAG"},
        items=(
            ("EMPTY", "Empty", ""),
            ("CAMERA", "Camera", ""),
            ("LIGHT", "Light", ""),
            ("ARMATURE", "Armature", ""),
            ("GEOMETRY", "Geometry", "")
        ),
        default={
            "EMPTY",
            "CAMERA",
            "LIGHT",
            "ARMATURE",
            "GEOMETRY"
        },
    )

    use_visible_objects: BoolProperty(
        name="Only Visible Object",
        description="Export only objects which are in the current view layer "
                    "and are visible.",
        default=True,
    )
    use_export_selected: BoolProperty(
        name="Only Selected Objects",
        description="Export only selected objects",
        default=False,
    )
    use_mesh_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply modifiers to mesh objects (on a copy!).",
        default=True,
    )
    use_exclude_ctrl_bone: BoolProperty(
        name="Exclude Control Bones",
        description="Do not export control bones (bone.use_deform = false)",
        default=True,
    )
    use_export_animation: BoolProperty(
        name="Export Animation",
        description="Export all the animation actions (include actions "
                    "in nla_tracks), note that by default Blender animation "
                    "is exported as actions, so every node would have its "
                    "own AnimationPlayer holding its actions",
        default=True,
    )
    use_export_shape_key: BoolProperty(
        name="Export Shape Key",
        description="Export all the shape keys in mesh objects",
        default=True,
    )
    use_stashed_action: BoolProperty(
        name="Export Stashed Actions",
        description="Export stashed actions and muted nla_strip as separate "
                    "animation and place into AnimationPlayer",
        default=True,
    )
    use_beta_features: BoolProperty(
        name="Use Beta Features",
        description="Export using new features coming in Godot beta versions",
        default=True,
    )
    generate_external_material: BoolProperty(
        name="Generate External Material",
        description="If turned on, materials in the exported scene will "
                    "generate external .material files when imported to "
                    "Godot, thus make it easy for material reusing",
        default=False,
    )
    animation_modes: EnumProperty(
        name="Animation Modes",
        description="Configuration of how Blender animation data is "
                    "exported to Godot AnimationPlayer as well as the "
                    "placement of AnimationPlayers in the node tree.",
        default="ACTIONS",
        items=(
            (
                "ACTIONS", "Animation as Actions",
                "Each animated node will have its own AnimationPlayer"
            ),
            (
                "SCENE_ANIMATION", "Scene Animation",
                "All the animations of the whole scene will be placed "
                "into one AnimationPlayer at scene root"
            ),
            (
                "SQUASHED_ACTIONS", "Animation as Actions with Squash",
                "Animation is exported as actions of nodes, but instead "
                "of having an individual AnimationPlayer for each node, "
                "this configuration will squash children nodes' actions "
                "to their parents"
            )
        )
    )
    material_mode: EnumProperty(
        name="Material Mode",
        description="Configuration of how mesh surface Material being "
                    "exported.",
        default="SCRIPT_SHADER",
        items=(
            (
                "NONE", "None",
                "Do not export any materials"
            ),
            (
                "SPATIAL", "Spatial Material",
                "Export all eligible materials as Spatial Material"
            ),
            (
                "SCRIPT_SHADER", "Script Shader Material",
                "Export all eligible materials as Shader Material "
                "with Script Shader"
            )
        )

    )
    material_search_paths: EnumProperty(
        name="Material Search Paths",
        description="Search for existing Godot materials with names that "
                    "match the Blender material names (i.e. the file "
                    "<matname>.tres containing a material resource)",
        default="PROJECT_DIR",
        items=(
            (
                "NONE", "None",
                "Don't search for materials"
            ),
            (
                "EXPORT_DIR", "Export Directory",
                "Search the folder where the escn is exported to"
            ),
            (
                "PROJECT_DIR", "Project Directory",
                "Search for materials in the Godot project directory"
            ),
        )
    )

    @property
    def check_extension(self):
        """Checks if the file extension is valid. It appears we don't
        really care.... """
        return True

    def execute(self, context):
        """Begin the export"""
        try:
            if not self.filepath:
                raise Exception("filepath not set")

            keywords = self.as_keywords(ignore=(
                "axis_forward",
                "axis_up",
                "global_scale",
                "check_existing",
                "filter_glob",
                "xna_validate",
            ))

            return export_godot.save(self, context, **keywords)
        except ValidationError as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}


def menu_func(self, context):
    """Add to the menu"""
    self.layout.operator(ExportGodot.bl_idname, text="Godot Engine (.escn)")


def register():
    """Add addon to blender"""
    bpy.utils.register_class(ExportGodot)
    bpy.types.TOPBAR_MT_file_export.append(menu_func)


def unregister():
    """Remove addon from blender"""
    bpy.utils.unregister_class(ExportGodot)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)
