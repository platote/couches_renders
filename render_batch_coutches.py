bl_info = {
    "name" : "RENDER COUCHES",
    "description" : "Generate COUCH Render",
    "author" : "Platote",
    "version" : (0, 0, 1),
    "blender" : (2, 80, 0),
    "location" : "View3D",
    "warning" : "",
    "support" : "COMMUNITY",
    "doc_url" : "",
    "category" : "3D View"
}

from importlib.metadata import metadata
from pydoc import describe
import json
import csv
import bpy
import os 
import requests
import math

from bpy.types import Operator
from bpy.types import (Panel, PropertyGroup)
from bpy.props import (StringProperty,
                       PointerProperty,
                       )

bpy.types.Scene.generate_batches = bpy.props.BoolProperty(
    name="Generate Batches",
    description="If checked, certain data will be processed",
    default=False
)

class MyProperties(PropertyGroup):

    id: StringProperty(
        name="id",
        description=":",
        default="",
        maxlen=1024,
        )

    id1 : StringProperty(
        name="id1",
        description=":",
        default="",
        maxlen=1024,
        )

def has_camera_in_scene(context):
    # Check if there's any object of type 'CAMERA' in the scene
    for obj in context.scene.objects:
        if obj.type == 'CAMERA':
            return True
    return False

class TLA_PT_sidebar(Panel):
    """Display test button"""
    bl_label = "COUCHES"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "COUCHES"

    def draw(self, context):
        # SETUP section
        box = self.layout.box()
        box.label(text="SETUP",  icon='TOOL_SETTINGS')
        # box.operator("scene.place_test_couch", text="Place a test couch")  # Assuming this operator exists

        info_box = box.box()  # Creates a nested box for the instructions
        info_box.label(text="1) Don't change the scale of the couch", icon='INFO')
        info_box.label(text="2) Place camera for correct render", icon='INFO')
        info_box.label(text="3) Place lights for correct render", icon='INFO')

        box.operator("scene.delete_except_camera_lights", text="Delete All Except Camera and Lights")

        # RENDER section
        box = self.layout.box()
        box.label(text="RENDER",  icon='RENDER_STILL')
        # Inside TLA_PT_sidebar's draw function:
        box.prop(context.scene, "generate_batches", text="Generate Batches")

        mytool = context.scene.my_tool
        box.prop(mytool, "id")
        box.prop(mytool, "id1")
        box.operator(TLA_OT_operator.bl_idname, text="Generate a couch")


class TLA_OT_DeleteExceptCameraLights(bpy.types.Operator):
    bl_idname = "scene.delete_except_camera_lights"
    bl_label = "Delete All Except Camera and Lights"
    bl_description = "Deletes all objects in the scene except for cameras and lights."

    def execute(self, context):
    # Loop over all objects in the scene
        for obj in context.scene.objects:
            # Check the object's type and delete if it's not a camera or light
            if obj.type not in ['CAMERA', 'LIGHT']:
                bpy.data.objects.remove(obj, do_unlink=True)

        return {'FINISHED'}


    
class TLA_OT_operator(Operator):
    """ tooltip goes here """
    bl_idname = "demo.operator"
    bl_label = "Generate a couch"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout

    def execute(self, context):

        if not has_camera_in_scene(context):
            self.report({'ERROR'}, "Please add a camera to the scene first!")
            return {'CANCELLED'}


        base_matcap_file = "T_Matcap_MC.png"
        body_bright_matcap = "Body/Body_Bright.png"
        body_dark_matcap = "Body/Body_Dark.png"
        body_PaleA_matcap = "Body/Body_Pale_A.png"
        body_PaleB_matcap = "Body/Body_Pale_B.png"
        eye_matcap_paleA = "Eyes/EyeGlossA.png"
        eye_matcap_paleB = "Eyes/EyeGlossB.png"
        eye_matcap_bright = "Eyes/EyeGlossBright.png"
        sigil_matcap = "Sigils/Sigil C.jpg"
        beak_matcap = "beak_matcap.png"

        def create_emission_material(_path):
            mat = bpy.data.materials.new(name="Emission")
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            nodes.clear()

            # Create a Principled BSDF shader and connect it to the Material Output
            principled = nodes.new(type='ShaderNodeBsdfPrincipled')
            output = nodes.new(type='ShaderNodeOutputMaterial')
            links.new(principled.outputs['BSDF'], output.inputs['Surface'])

            texImage = nodes.new('ShaderNodeTexImage')
            texImage.image = bpy.data.images.load(_path)
            links.new(texImage.outputs['Color'], principled.inputs['Base Color'])
            links.new(texImage.outputs['Color'], principled.inputs['Emission'])

            # Set shiny glass properties
            principled.inputs['Metallic'].default_value = 0
            principled.inputs["Specular"].default_value = 0.2
            principled.inputs['Roughness'].default_value = 0.2

            return mat
        
        def applyingPrincipledBSDF(_mat, _path, obj):

            _mat.use_nodes = True
            nodes = _mat.node_tree.nodes
            links = _mat.node_tree.links
            links.clear()
            nodes.clear()

            # Create a Principled BSDF shader and connect it to the Material Output
            principled = nodes.new(type='ShaderNodeBsdfPrincipled')
            output = nodes.new(type='ShaderNodeOutputMaterial')
            links.new(principled.outputs['BSDF'], output.inputs['Surface'])

            # Create a Texture Image node and load the image into it
            texImage = nodes.new('ShaderNodeTexImage')
            texImage.image = bpy.data.images.load(_path)
            links.new(texImage.outputs['Color'], principled.inputs['Base Color'])

            # Applying metallic
            if any(keyword in _path for keyword in ["Key", "Cans", "Charging", "Ledger", "EtherHalo"]):
                _mat.name = f"metallic_{obj.name}"
                principled.inputs['Metallic'].default_value = 1.0
                principled.inputs['Specular'].default_value = 1.0
                principled.inputs['Roughness'].default_value = 0.4
            
            # Applying Matte
            if any(keyword in _path for keyword in ["EtherBill", "Socks", "Close", "Sticky", "Newspaper", "Cushion", "Pizza", "Notebooks", "Fries", "Cheese", "Loot", "Silk", "Carpet", "Book", "CL"]) or "BaseCouch" in obj.name:
                _mat.name = f"matte_{obj.name}"
                principled.inputs['Metallic'].default_value = 0
                principled.inputs['Specular'].default_value = 0.250
                principled.inputs['Roughness'].default_value = 0.5
            
            # Applying Plastic
            if any(keyword in _path for keyword in ["Toy", "Games", "Guitar", "Plug", "Loombook", "Sauce", "Eggplant", "Fridge", "Speaker", "Crate", "TV", "Cup", "Rubik", "Headphone", "Ducky", "Clock"]) or "CouchFace" in obj.name:
                _mat.name = f"plastic_{obj.name}"
                principled.inputs['Metallic'].default_value = 0
                principled.inputs['Specular'].default_value = 0.2
                principled.inputs['Roughness'].default_value = 0.2

            # Applying Wassie
            if "Wassie" in obj.name:
                _mat.name = f"wassie_{obj.name}"
                principled.inputs['Metallic'].default_value = 0
                principled.inputs['Specular'].default_value = 0.250
                principled.inputs['Roughness'].default_value = 0.5

            # Applying Emission
            if "Disco" in obj.name:
                _mat.name = f"emission_{obj.name}"
                principled.inputs['Metallic'].default_value = 0
                principled.inputs["Specular"].default_value = 0.2
                principled.inputs['Roughness'].default_value = 0.2
                links.new(texImage.outputs['Color'], principled.inputs['Emission'])

        def applyingTexture(path, obj, outline, matcap_file, outline_color = (0,0,0,1)):
            mat = bpy.data.materials.new(name="Base Material")
            applyingPrincipledBSDF(mat, path, obj)
            obj.data.materials[0] = mat

            if any(keyword in path for keyword in ["EtherHalo", "Charging", "Ledger", "TraderKeyboard"]):
                emission_material = create_emission_material(path)
                emission_material.name = f"emission_{obj.name}"
                obj.data.materials[1] = emission_material

            obj.data.materials[0] = mat

        fbx_to_vrm_scale = 0.15
        metadata_file = "metadata.csv"

        rugs = ["Disco", "Loot", "SilkRug", "Carpet"]

        texture_mapping = open(os.path.join(os.path.dirname(bpy.data.filepath), "texture_mapping.csv"))
        traits_mapping = open(os.path.join(os.path.dirname(bpy.data.filepath), "traits_mapping.csv"))

        metadata_mapping = open(os.path.join(os.path.dirname(bpy.data.filepath), metadata_file))

        csvreader = csv.reader(texture_mapping)
        header = []
        header = next(csvreader)
        rows = []
        for row in csvreader:
            rows.append(row)

        csvreader2 = csv.reader(metadata_mapping)
        header2 = []
        header2 = next(csvreader2)
        rows2 = []
        for row in csvreader2:
            rows2.append(row)
        
        index = 1 if not int(context.scene.my_tool.id) else int(context.scene.my_tool.id) 
        index_1 = 10 if not int(context.scene.my_tool.id1) else int(context.scene.my_tool.id1)

        def isWassieCreated(id):

            export_fp_base = f"exports/final_prod/Wassie {id}.vrm"
            export_fp = os.path.join(os.path.dirname(bpy.data.filepath), export_fp_base)
            return os.path.isfile(export_fp)

        def isWassieClothes(_clothes_type, id):
            clothes_type = rows2[id+1][4].replace(' ', '').replace(')', '').replace('(', '')
            if clothes_type == _clothes_type:
                return True

        for id in range(index, index_1+1): 

            hat = None
            clothes = None
            wieldable = None
            sigil = None
            armature_feet = None
            eyes = None
            feet = None
            sigil_ornament = None
            body = None
            armature = None
            toiletPaper = None

            wassie_race = True   

            if (rows2[id+1][1].replace(' ', '') in rugs):
                wassie_race = False

            if wassie_race:

                print("This is not a couch, not rendering : " + str(id))
                
            else:

                print("This is a couch")

                base_couch = None
                seat = None
                left_arm = None
                right_arm = None
                couch_hat = None

                wassie_types = ['Precarious', 'Struggling', 'Draped', 'Sleeping', 'DroppedRemote', 'Lounging', 'Sitting']

                wassie_beak_texture_fp =  os.path.join(os.path.dirname(bpy.data.filepath), "Couches/CouchWassies/CouchWassieBeak.png")
                wassie_eyes_texture_fp =  os.path.join(os.path.dirname(bpy.data.filepath), "Couches/CouchWassies/CouchWassieEyes.png")
                wassie_feet_texture_fp =  os.path.join(os.path.dirname(bpy.data.filepath), "Couches/CouchWassies/CouchWassieFeet.png")

                couch_rug_type = rows2[id+1][1].replace(' ', '') 
                couch_colour = rows2[id+1][2].replace(' ', '') 
                couch_face_type = rows2[id+1][3].replace(' ', '') 
                couch_hat_type = rows2[id+1][4].replace(' ', '') 
                couch_wassie_colour_type = rows2[id+1][5].replace(' ', '') 
                couch_right_arm_type = rows2[id+1][6].replace(' ', '') 
                couch_left_arm_type = rows2[id+1][7].replace(' ', '') 
                couch_seat_type = rows2[id+1][8].replace(' ', '') 
                couch_bottom_type = rows2[id+1][9].replace(' ', '') 

                # rug, couch_colour, face, hat, wassie colour, right arm, left arm, seat, couch bottom

                base_couch_fp = os.path.join(os.path.dirname(bpy.data.filepath), "Couches/Couch/BaseCouch.fbx")
                couch_rug_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchRugs/CouchRug_{couch_rug_type}.fbx")
                couch_face_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchFaces/CouchFace_{couch_face_type}.fbx")
                couch_bottom_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchBottom/CouchBottom_{couch_bottom_type}.fbx")

                

                # The function that goes into the wassie directory for left arm, right arm, hat, and seat
                def import_wassie(asset_type, position):
                    wassie_beak_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchWassies/Couch{position}_{asset_type}Wassie_Beak.fbx")
                    wassie_body_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchWassies/Couch{position}_{asset_type}Wassie_Body.fbx")
                    wassie_eyes_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchWassies/Couch{position}_{asset_type}Wassie_Eyes.fbx")
                    wassie_feet_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchWassies/Couch{position}_{asset_type}Wassie_Feet.fbx")

                    bpy.ops.import_scene.fbx(filepath=wassie_beak_fp)
                    bpy.ops.import_scene.fbx(filepath=wassie_body_fp)
                    bpy.ops.import_scene.fbx(filepath=wassie_eyes_fp)
                    bpy.ops.import_scene.fbx(filepath=wassie_feet_fp)

                if couch_hat_type in wassie_types:
                    import_wassie(couch_hat_type, 'Hat')
                else:
                    couch_hat_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchHats/CouchHat_{couch_hat_type}.fbx")
                    bpy.ops.import_scene.fbx(filepath=couch_hat_fp)

                if couch_left_arm_type in wassie_types:
                    import_wassie(couch_left_arm_type, 'LeftArm')
                else:
                    couch_left_arm_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchLeftArm/CouchLeftArm_{couch_left_arm_type}.fbx")
                    bpy.ops.import_scene.fbx(filepath=couch_left_arm_fp)

                if couch_right_arm_type in wassie_types: 
                    import_wassie(couch_right_arm_type, 'RightArm')
                else:
                    couch_right_arm_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchRightArm/CouchRightArm_{couch_right_arm_type}.fbx")
                    bpy.ops.import_scene.fbx(filepath=couch_right_arm_fp)

                if couch_seat_type in wassie_types:
                    if couch_seat_type == "Lounging" or couch_seat_type == "Sleeping":
                        seat = None
                    else:
                        import_wassie(couch_seat_type, 'Seat')
                else:
                    couch_seat_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchSeat/CouchSeat_{couch_seat_type}.fbx")
                    bpy.ops.import_scene.fbx(filepath=couch_seat_fp)

                bpy.ops.import_scene.fbx(filepath=base_couch_fp)
                bpy.ops.import_scene.fbx(filepath=couch_face_fp)
                bpy.ops.import_scene.fbx(filepath=couch_rug_fp)
                bpy.ops.import_scene.fbx(filepath=couch_bottom_fp)
                

                objects = bpy.data.objects

                for o in objects:
                    if ('Rug' in o.name):
                        rug = o
                    if('BaseCouch' in o.name):
                        base_couch = o
                    if('CouchFace' in o.name):
                        couch_face = o
                    if('CouchHat' in o.name and (not('Body' in o.name) and not('Feet' in o.name) and not('Eyes' in o.name) and not('Beak' in o.name))):
                        couch_hat = o
                    if('Beak' in o.name):
                        wassie_beak = o
                    if('Body' in o.name):
                        wassie_body = o
                    if('Eyes' in o.name):
                        wassie_eyes = o
                    if('Feet' in o.name):
                        wassie_feet = o
                    if('LeftArm' in o.name and (not('Body' in o.name) and not('Feet' in o.name) and not('Eyes' in o.name) and not('Beak' in o.name))):
                        left_arm = o
                    if('RightArm' in o.name and (not('Body' in o.name) and not('Feet' in o.name) and not('Eyes' in o.name) and not('Beak' in o.name))):
                        right_arm = o
                    if('Seat' in o.name and (not('Body' in o.name) and not('Feet' in o.name) and not('Eyes' in o.name) and not('Beak' in o.name))):
                        seat = o
                    if('Bottom' in o.name):
                        couch_bottom = o
                    if ('Armature' in o.name):
                        couch_armature = o
                    
                couch_colour_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/Couch/CouchTexture_{couch_colour}.png")
                couch_face_texture_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchFaces/CouchFace_{couch_face_type}_TXTR.png")


                if any(s in wassie_body.name for s in ["Struggling", "Precarious", "Draped", "Sleeping"]):
                    couch_wassie_colour_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchWassies/reverse/CouchWassieTX_{couch_wassie_colour_type}_White.png")
                else:
                    couch_wassie_colour_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchWassies/CouchWassieTX_{couch_wassie_colour_type}_White.png")

                couch_bottom_texture_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchBottom/CouchBottom_{couch_bottom_type}_TXTR.png")
                couch_rug_texture_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchRugs/CouchRug_{couch_rug_type}_TXTR.png")

                if couch_hat: 
                    couch_hat_texture_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchHats/CouchHat_{couch_hat_type}_TXTR.png")
                    applyingTexture(couch_hat_texture_fp, couch_hat, True, base_matcap_file)

                if base_couch:
                    applyingTexture(couch_colour_fp, base_couch, True, base_matcap_file)

                if wassie_beak:
                    applyingTexture(wassie_beak_texture_fp, wassie_beak, True, base_matcap_file)
                
                if wassie_eyes:
                    applyingTexture(wassie_eyes_texture_fp, wassie_eyes, False, base_matcap_file)
                
                if wassie_feet:
                    applyingTexture(wassie_feet_texture_fp, wassie_feet, True, base_matcap_file)

                if wassie_body:
                    applyingTexture(couch_wassie_colour_fp, wassie_body, True, base_matcap_file)

                if right_arm:
                    couch_right_arm_texture_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchRightArm/CouchRightArm_{couch_right_arm_type}_TXTR.png")
                    applyingTexture(couch_right_arm_texture_fp, right_arm, False, base_matcap_file)

                if left_arm:
                    couch_left_arm_texture_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchLeftArm/CouchLeftArm_{couch_left_arm_type}_TXTR.png")
                    applyingTexture(couch_left_arm_texture_fp , left_arm, False, base_matcap_file)

                if seat:
                    couch_seat_texture_fp = os.path.join(os.path.dirname(bpy.data.filepath), f"Couches/CouchSeat/CouchSeat_{couch_seat_type}_TXTR.png")
                    applyingTexture(couch_seat_texture_fp, seat, False, base_matcap_file)
                
                applyingTexture(couch_face_texture_fp, couch_face, False, base_matcap_file)
                applyingTexture(couch_bottom_texture_fp, couch_bottom, True, base_matcap_file)
                applyingTexture(couch_rug_texture_fp, rug, False, base_matcap_file )


                def smooth_if_exist(object):
                    if (object):
                        object.data.use_auto_smooth = 0

                ruled_mesh = [rug, base_couch, couch_face, couch_hat, wassie_beak, wassie_body, wassie_eyes, wassie_feet, left_arm, right_arm, seat, couch_bottom]
                mesh_to_parent = [rug, couch_face, couch_hat, wassie_beak, wassie_body, wassie_eyes, wassie_feet, left_arm, right_arm, seat, couch_bottom]

                for item in ruled_mesh:
                    smooth_if_exist(item)

                def parentAtoB(a, b, mode):
                    bpy.ops.object.select_all(action='DESELECT')
                    a.select_set(True)
                    b.select_set(True)
                    bpy.context.view_layer.objects.active = b
                    bpy.ops.object.parent_set(type=mode)
                    bpy.ops.object.select_all(action='DESELECT')

                def parentObjectAtoBifExist(a, b):
                    if(a):
                        parentAtoB(a, b, 'OBJECT')
                
                for item in mesh_to_parent:
                    parentObjectAtoBifExist(item, couch_armature)

                bpy.ops.object.select_all(action='DESELECT')
                couch_armature.select_set(True)
                bpy.context.view_layer.objects.active = couch_armature
                bpy.ops.transform.resize(value=(fbx_to_vrm_scale, fbx_to_vrm_scale, fbx_to_vrm_scale))
                bpy.ops.object.select_all(action='DESELECT')
                couch_armature.location.z += -1.49362

                
                dict = {0: ['A'], 1: ['E'], 2: ['U'], 3: ['I'], 4: ['O'], 5: ['Blink', 'Close Both'], 6: ['Joy', 'Happy'], 7: ['Angry', 'Angry'], 8: ['Sorrow', 'Sad'], 9: ['Fun', 'Happy'] }

                bpy.ops.object.select_all(action='DESELECT')
                couch_armature.select_set(True)
                for i in dict:
                    bpy.ops.vrm.add_vrm0_blend_shape_group(armature_name=couch_armature.name, name=dict[i][0])
                    bpy.ops.vrm.add_vrm0_blend_shape_bind(armature_name=couch_armature.name, blend_shape_group_index=i)
                    if i < 5:
                        blend_shape_groups = bpy.context.object.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups[i].binds[0]
                        blend_shape_groups.mesh.value = couch_face.data.name
                        blend_shape_groups.index = dict[i][0]
                        blend_shape_groups.weight = 1
                    else:
                        blend_shape_groups = bpy.context.object.data.vrm_addon_extension.vrm0.blend_shape_master.blend_shape_groups[i].binds[0]
                        blend_shape_groups.mesh.value = couch_face.data.name
                        blend_shape_groups.index = dict[i][1]
                        blend_shape_groups.weight = 1
                bpy.ops.object.select_all(action='DESELECT')

                
                bpy.context.scene.camera = bpy.data.objects['Camera']

                export_fp_base = f"pngcouches/Couch {id}.png"
                export_fp = os.path.join(os.path.dirname(bpy.data.filepath), export_fp_base)

                bpy.context.scene.render.filepath = export_fp
                bpy.context.scene.render.image_settings.file_format = 'PNG'
                bpy.context.scene.render.image_settings.color_mode = 'RGBA'
                bpy.context.scene.render.image_settings.color_depth = '8'  # You can change to '16' for 16-bit PNGs

                bpy.ops.render.render(write_still=True)


                if context.scene.generate_batches:

                    for material in bpy.data.materials:
                        if material.name == "Sage" or material.name == "Shaman" or material.name == "transpraent" or material.name == "transparent_Dissected":
                            print(f"keeping the {material.name}")
                        else:
                            material.user_clear()
                            bpy.data.materials.remove(material)
                            
                    for mesh in bpy.data.meshes:
                        bpy.data.meshes.remove(mesh)

                        
                    for object in bpy.data.objects:
                        if object.type not in ['CAMERA', 'LIGHT']:
                            bpy.data.objects.remove(object, do_unlink=True)

                    for armature in bpy.data.armatures:
                        bpy.data.armatures.remove(armature)
                        
                    for image in bpy.data.images:
                        if image.name == "sage_base.png" or image.name == "sage_shade.png" or image.name == "gold_shade.png" or image.name == "gold_base.png" or image.name == "metallic.jpg" or image.name == "gold.jpg":
                            print(f"keeping the {image.name}")
                        else:
                            bpy.data.images.remove(image)





        self.report({'INFO'},
            f"execute()")

        return {'FINISHED'}



classes = [
    MyProperties,
    TLA_OT_operator,
    TLA_PT_sidebar,
]

def register():

    # bpy.utils.register_class(TLA_OT_PlaceTestCouch)
    bpy.utils.register_class(TLA_OT_DeleteExceptCameraLights)

    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)
        
def unregister():

    # bpy.utils.unregister_class(TLA_OT_PlaceTestCouch)
    bpy.utils.unregister_class(TLA_OT_DeleteExceptCameraLights)
    del bpy.types.Scene.generate_batches
    del bpy.types.Scene.my_tool
    for c in classes:
        bpy.utils.unregister_class(c)

if __name__ == '__main__':
    register()