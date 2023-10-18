# wmbMaterialJSON.py
import bpy, json, idprop

class WMBMaterialToJSON(bpy.types.Operator):
    bl_idname = "b2n.materialtojson"
    bl_label = "Store Material As JSON"
    
    def execute(self, context):
        dictForString = []
        material = bpy.context.material
        for key, value in material.items():
            if key in ["wmb_mat_as_json", "ID"]:
                continue
            if ("Map" in key) \
              or (key[0:3] == "tex" and key[3].isnumeric()) \
              or (key in ("Shader_Name", "Texture_Flags")) \
              or (key.isnumeric()):
                if type(value) is idprop.types.IDPropertyArray:
                    dictForString.append((key, list(value)))
                else:
                    dictForString.append((key, value))
        material["wmb_mat_as_json"] = json.dumps(dictForString)
        return {'FINISHED'}

class WMBMaterialFromJSON(bpy.types.Operator):
    bl_idname = "b2n.jsontomaterial"
    bl_label = "Load Material From JSON"
    
    def execute(self, context):
        material = bpy.context.material
        # clear custom properties
        keys = list(material.keys())
        for key in keys:
            if key not in ["wmb_mat_as_json", "ID"]:
                del material[key]
        
        dictFromString = json.loads(material["wmb_mat_as_json"])
        for item in dictFromString:
            key, value = item[0], item[1]
            material[key] = value
            
        return {'FINISHED'}


class WMBCopyMaterialJSON(bpy.types.Operator):
    bl_idname = "b2n.copymaterialjson"
    bl_label = "Copy Material JSON"
    
    def execute(self, context):
        bpy.context.window_manager.clipboard = bpy.context.material["wmb_mat_as_json"]
        return {'FINISHED'}

class WMBPasteMaterialJSON(bpy.types.Operator):
    bl_idname = "b2n.pastematerialjson"
    bl_label = "Paste Material JSON"
    
    def execute(self, context):
        bpy.context.material["wmb_mat_as_json"] = bpy.context.window_manager.clipboard
        return {'FINISHED'}

class WMBMaterialJSONPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = 'material'
    bl_label = "MGRR Material Copy"

    def draw(self, context):
        layout = self.layout
        layout.operator(WMBMaterialToJSON.bl_idname, text="Update string from material")
        layout.operator(WMBCopyMaterialJSON.bl_idname, text="Copy material to clipboard")
        
        layout.prop(bpy.context.material, "wmb_mat_as_json")
        
        layout.operator(WMBPasteMaterialJSON.bl_idname, text="Paste material from clipboard")
        layout.operator(WMBMaterialFromJSON.bl_idname, text="Update material from string")