# Dynamic UV

import bpy
from bpy.types import Operator, Menu
from bpy.app.handlers import persistent 
from mathutils import Vector
import os

class bcolors:
    SUCCESS = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    RESET = '\033[0m'

bl_info = {
    "name": "Dynamic UV",
    "author": "Sören Schmidt-Clausen",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "3DView",
    "description": "Adds Dynamic UV Operators",
    "warning": "Beta",
    "support": "COMMUNITY",
    "wiki_url": "",
    "tracker_url": "",
    "category": "UV"
}

def select_object(context, obj):
    context.view_layer.objects.active = obj
    obj.select_set(True)

def get_mean_location(objects):
    location_accu = Vector((0.0, 0.0, 0.0))
    count = 0
    for obj in objects:
        count += 1
        location_accu += obj.location

    return location_accu / count

def createHelper(context, type, name, selected_objects, scale):
    bpy.ops.object.empty_add(type=type, align="WORLD", location=get_mean_location(selected_objects))
    bpy.ops.transform.resize(value=scale)
    context.object.name = name
    context.object.duv_type = "HELPER"
    return context.object

def get_max_distance(position, objects):
    max_distance = 0

    for obj in objects:
        max_distance = mathutils.max(mathutils.distance(obj.location, position), max_distance)

    return max_distance

def append_nodegroup(name):
    python_file = __file__
    folder = os.path.join(*os.path.split(python_file)[:1])
    file_name = "nodegroups.blend"
    inner_folder = "NodeTree"
    
    bpy.ops.wm.append(
        filepath=os.path.join(folder, file_name, inner_folder, name), 
        directory=os.path.join(folder, file_name, inner_folder),
        filename=name,
        set_fake=True
    )

def add_modifier(context, obj, helper, name):
    select_object(context, obj)

    obj.duv_type = "MESH"

    if name not in bpy.data.node_groups:
        append_nodegroup(name)

    bpy.ops.object.modifier_add(type='NODES')
    modifier_stack = obj.modifiers
    geo_modifier = modifier_stack[len(modifier_stack)-1]
    geo_modifier.node_group = bpy.data.node_groups[name]

    geo_modifier["Input_2"] = helper

class DYNUV_OT_create_planar_maper(Operator):
    bl_idname = "object.createplanemapping"
    bl_label = "Create planar mapping setup"
    bl_description= "Adds a dynamic planar uv mapping to the selected objects"

    def execute(self, context):
        selected_objects = context.selected_objects

        if len(selected_objects) == 0:
            self.report({"INFO"},"No Object selected")
            return {"CANCELLED"}

        planar_mapper = createHelper(context, "CUBE", "Planar-Projection-Helper", selected_objects, [1,1,0.0001])

        for obj in selected_objects:
            add_modifier(context, obj, planar_mapper, "DUV_Planar_Project")

        select_object(context, planar_mapper)

        return {'FINISHED'}

class DYNUV_OT_create_box_maper(Operator):
    bl_idname = "object.createboxmapping"
    bl_label = "Create box mapping setup"
    bl_description = "Adds a dynamic box uv mapping to the selected objects"

    def execute(self, context):
        selected_objects = context.selected_objects

        if len(selected_objects) == 0:
            self.report({"INFO"},"No Object selected")
            return {"CANCELLED"}

        box_mapper = createHelper(context, "CUBE", "Cube-Projection-Helper", selected_objects, [1,1,1])

        for obj in selected_objects:
            add_modifier(context, obj, box_mapper, "DUV_Box_Project")

        select_object(context, box_mapper)

        return {'FINISHED'}

class DYNUV_MT_mapping_menu(bpy.types.Menu):
    bl_idname = "VIEW3D_MT_DYNAMICUV"
    bl_label = "Dynamic Unwrap"

    def draw(self, context):
        layout = self.layout

        layout.operator(operator="object.createplanemapping", text="Add Planar Mapping", icon="MESH_PLANE")
        layout.operator(operator="object.createboxmapping", text="Add Box Mapping", icon="MESH_CUBE")

classes = [
    DYNUV_OT_create_planar_maper,
    DYNUV_OT_create_box_maper,
    DYNUV_MT_mapping_menu
]

addon_keymaps = []

def register():
    # Register classes
    for cls in classes:
        bpy.utils.register_class(cls)

    # Register ui menu
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu', 'U', 'PRESS', ctrl=False, shift=False, alt=False)
        kmi.properties.name =  DYNUV_MT_mapping_menu.bl_idname
        addon_keymaps.append((km, kmi))

    # Register object property
    bpy.types.Object.duv_type = bpy.props.StringProperty(default="") # MESH & HELPER

    print("[",bcolors.SUCCESS,"OK",bcolors.RESET,"] DynamicUV_Addon registered")

def unregister():
    # Unregister classes
    for cls in classes:
        bpy.utils.unregister_class(cls)

    # Unregister ui menu
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # Unregister object property
    del bpy.types.Object.duv_type

    print("[",bcolors.SUCCESS,"OK",bcolors.RESET,"] DynamicUV_Addon unregistered")

if __name__ == "__main__":
    register()

    