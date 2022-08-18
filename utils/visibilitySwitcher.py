from typing import List, Dict
import bpy
import re


def isVisibilitySelectorSupported() -> bool:
    return ("WMB" in bpy.data.collections and len(bpy.data.collections["WMB"].all_objects) > 0) or\
           ("COL" in bpy.data.collections and len(bpy.data.collections["COL"].all_objects) > 0)

def getObjectName(obj: bpy.types.Object) -> str:
    name = re.match(r"^\d+-(.*)", obj.name)
    if name:
        return name.group(1)
    else:
        return obj.name

def objectNameSortKey(name: str) -> str:
    nameAndLod = re.match(r"^(.*)-(\d+)$", name.lower())
    if nameAndLod:
        lod = int(nameAndLod.group(2))
        return f"{lod:04d}-{nameAndLod.group(1)}"
    else:
        return name

def getMeshParts(collection: str) -> List[str]:
    names: List[str] = []
    for obj in list(bpy.data.collections[collection].all_objects):
        if obj.type != "MESH":
            continue
        objName = getObjectName(obj)
        if objName not in names:
            names.append(objName)
    names.sort(key=objectNameSortKey)
    return names

def getMeshPartGroups(collection: str) -> Dict[str, List[str]]:
    partGroups: Dict[str, List[str]] = {
        "All": getMeshParts(collection),
    }
    if collection == "WMB":
        wmbCollChildren = bpy.data.collections["WMB"].children
        if "pl000d" in wmbCollChildren or "pl0000" in wmbCollChildren:
            partGroups.update(outfitToParts["2B"])
        elif "pl020d" in wmbCollChildren or "pl0200" in wmbCollChildren:
            partGroups.update(outfitToParts["9S"])
        elif "pl010d" in wmbCollChildren or "pl0100" in wmbCollChildren:
            partGroups.update(outfitToParts["A2"])
    if len(partGroups) == 1:
        for obj in list(bpy.data.collections[collection].all_objects):
            if obj.type != "MESH":
                continue
            objLod = re.search(r"-(\d+)$", obj.name)
            if objLod:
                objLod = objLod.group(1)
            else:
                objLod = "0"

            lodName = f"Group_{objLod}"
            objName = getObjectName(obj)

            if lodName not in partGroups:
                partGroups[lodName] = []
            if objName not in partGroups[lodName]:
                partGroups[lodName].append(objName)

    return partGroups

def setMeshPartVisibility(collection: str, objName: str, visible: bool):
    for obj in list(bpy.data.collections[collection].all_objects):
        if obj.type != "MESH":
            continue
        if objName == getObjectName(obj):
            obj.hide_set(not visible)
            obj.hide_viewport = not visible
            obj.hide_render = not visible

def focusOnMeshParts(collection: str, names: List[str]):
    for obj in list(bpy.data.collections[collection].all_objects):
        if obj.type != "MESH":
            continue
        objName = getObjectName(obj)
        setMeshPartVisibility(collection, objName, objName in names)

def focusOnMeshGroup(collection: str, group: str):
    groupParts = getMeshPartGroups(collection)[group]
    for obj in list(bpy.data.collections[collection].all_objects):
        if obj.type != "MESH":
            continue
        objName = getObjectName(obj)
        isVisible = objName in groupParts
        obj.hide_set(not isVisible)
        obj.hide_viewport = not isVisible
        obj.hide_render = not isVisible

def selectMeshPart(collection: str, name: str, selectType: str):
    for obj in list(bpy.data.collections[collection].all_objects):
        if obj.type != "MESH":
            continue
        objName = getObjectName(obj)
        if selectType == "SELECT":
            obj.select_set(objName == name)
        elif selectType == "DESELECT" and objName == name:
            obj.select_set(False)
        elif selectType == "ADD" and objName == name:
            obj.select_set(True)

    if bpy.context.object not in bpy.context.selected_objects and len(bpy.context.selected_objects) > 0:
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]

class MeshPartSetVisibility(bpy.types.Operator):
    bl_idname = "na.mesh_part_set_visibility"
    bl_label = "Set Visibility"
    bl_options = {"UNDO"}

    partName: bpy.props.StringProperty(name="Part Name")
    visibilityType: bpy.props.StringProperty(name="Visibility Type")
    collection: bpy.props.StringProperty(name="Collection")

    def execute(self, context):
        if self.visibilityType == "show" or self.visibilityType == "hide":
            setMeshPartVisibility(self.collection, self.partName, self.visibilityType == "show")
        elif self.visibilityType == "focus":
            focusOnMeshParts(self.collection, [self.partName])
        else:
            raise Exception(f"Unknown visibility type {self.visibilityType}")

        return {"FINISHED"}

class MeshPartSelect(bpy.types.Operator):
    bl_idname = "na.mesh_part_select"
    bl_label = "Select"
    bl_options = {"UNDO"}

    partName: bpy.props.StringProperty(name="Part Name")
    collection: bpy.props.StringProperty(name="Collection")

    def invoke(self, context, event):
        if event.shift and not event.ctrl:
            selectType = "ADD"
        elif event.ctrl and not event.shift:
            selectType = "DESELECT"
        elif not event.shift and not event.ctrl:
            selectType = "SELECT"
        selectMeshPart(self.collection, self.partName, selectType)
        return {"FINISHED"}

class MeshGroupSetVisibility(bpy.types.Operator):
    bl_idname = "na.mesh_group_set_visibility"
    bl_label = "Set Visibility"
    bl_options = {"UNDO"}

    groupName: bpy.props.StringProperty(name="Group Name")
    visibilityType: bpy.props.StringProperty(name="Visibility Type")
    collection: bpy.props.StringProperty(name="Collection")

    def execute(self, context):
        if self.visibilityType == "show" or self.visibilityType == "hide":
            for part in getMeshPartGroups(self.collection)[self.groupName]:
                setMeshPartVisibility(self.collection, part, self.visibilityType == "show")
        elif self.visibilityType == "focus":
            focusOnMeshGroup(self.collection, self.groupName)
        else:
            raise Exception(f"Unknown visibility type {self.visibilityType}")

        return {"FINISHED"}

class MeshGroupSelect(bpy.types.Operator):
    bl_idname = "na.mesh_group_select"
    bl_label = "Select"
    bl_options = {"UNDO"}

    groupName: bpy.props.StringProperty(name="Group Name")
    collection: bpy.props.StringProperty(name="Collection")

    def invoke(self, context, event):
        if event.shift and not event.ctrl:
            selectType = "ADD"
        elif event.ctrl and not event.shift:
            selectType = "DESELECT"
        else:
            selectType = "SELECT"
        if selectType == "SELECT":
            bpy.ops.object.select_all(action="DESELECT")
            selectType = "ADD"
        for part in getMeshPartGroups(self.collection)[self.groupName]:
            selectMeshPart(self.collection, part, selectType)
        return {"FINISHED"}

class Mesh_PT_VisibilitySelectorToplevel(bpy.types.Panel):
    bl_label = "Mesh Visibility"
    bl_idname = "MESH_PT_visibility_selector_toplevel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "NA: Mesh Visibility"

    def draw(self, context):
        if not isVisibilitySelectorSupported():
            self.layout.label(text="No meshes found")
            return

class Mesh_PT_IndividualVisibilitySelector(bpy.types.Panel):
    bl_label = "Individual Visibility"
    bl_idname = "MESH_PT_individual_visibility_selector"
    bl_parent_id = Mesh_PT_VisibilitySelectorToplevel.bl_idname
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        if not isVisibilitySelectorSupported():
            return

        layout = self.layout
        for part in getMeshParts("WMB"):
            row = layout.row(align=True)

            selectOp = row.operator(MeshPartSelect.bl_idname, text=part, emboss=False)
            selectOp.partName = part
            selectOp.collection = "WMB"

            viewOp = row.operator(MeshPartSetVisibility.bl_idname, text="", icon="HIDE_OFF")
            viewOp.partName = part
            viewOp.visibilityType = "show"
            viewOp.collection = "WMB"

            viewOp = row.operator(MeshPartSetVisibility.bl_idname, text="", icon="HIDE_ON")
            viewOp.partName = part
            viewOp.visibilityType = "hide"
            viewOp.collection = "WMB"

            col = row.column(align=True)
            col.ui_units_x = 1.5
            viewOp = col.operator(MeshPartSetVisibility.bl_idname, text="", icon="PROP_OFF")
            viewOp.partName = part
            viewOp.visibilityType = "focus"
            viewOp.collection = "WMB"

class Mesh_PT_GroupVisibilitySelector(bpy.types.Panel):
    bl_label = "Group Visibility"
    bl_idname = "MESH_PT_group_visibility_selector"
    bl_parent_id = Mesh_PT_VisibilitySelectorToplevel.bl_idname
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        if not isVisibilitySelectorSupported():
            return

        layout = self.layout
        for groupName, parts in getMeshPartGroups("WMB").items():
            row = layout.row(align=True)

            selectOp = row.operator(MeshGroupSelect.bl_idname, text=groupName, emboss=False)
            selectOp.groupName = groupName
            selectOp.collection = "WMB"

            groupOp = row.operator(MeshGroupSetVisibility.bl_idname, text="", icon="HIDE_OFF")
            groupOp.groupName = groupName
            groupOp.visibilityType = "show"
            groupOp.collection = "WMB"

            groupOp = row.operator(MeshGroupSetVisibility.bl_idname, text="", icon="HIDE_ON")
            groupOp.groupName = groupName
            groupOp.visibilityType = "hide"
            groupOp.collection = "WMB"

            col = row.column(align=True)
            col.ui_units_x = 1.5
            groupOp = col.operator(MeshGroupSetVisibility.bl_idname, text="", icon="PROP_OFF")
            groupOp.groupName = groupName
            groupOp.visibilityType = "focus"
            groupOp.collection = "WMB"

def enableVisibilitySelector():
    if hasattr(bpy.types, Mesh_PT_VisibilitySelectorToplevel.bl_idname):
        return
    register()

def disableVisibilitySelector():
    if not hasattr(bpy.types, Mesh_PT_VisibilitySelectorToplevel.bl_idname):
        return
    unregister()

def register():
    if hasattr(bpy.types, Mesh_PT_VisibilitySelectorToplevel.bl_idname):
        return
    bpy.utils.register_class(MeshPartSetVisibility)
    bpy.utils.register_class(MeshPartSelect)
    bpy.utils.register_class(MeshGroupSetVisibility)
    bpy.utils.register_class(MeshGroupSelect)
    bpy.utils.register_class(Mesh_PT_VisibilitySelectorToplevel)
    bpy.utils.register_class(Mesh_PT_GroupVisibilitySelector)
    bpy.utils.register_class(Mesh_PT_IndividualVisibilitySelector)

def unregister():
    if not hasattr(bpy.types, Mesh_PT_VisibilitySelectorToplevel.bl_idname):
        return
    bpy.utils.unregister_class(MeshPartSetVisibility)
    bpy.utils.unregister_class(MeshPartSelect)
    bpy.utils.unregister_class(MeshGroupSetVisibility)
    bpy.utils.unregister_class(MeshGroupSelect)
    bpy.utils.unregister_class(Mesh_PT_VisibilitySelectorToplevel)
    bpy.utils.unregister_class(Mesh_PT_GroupVisibilitySelector)
    bpy.utils.unregister_class(Mesh_PT_IndividualVisibilitySelector)

outfitToParts = {
    "2B": {
        "Normal": ["Body-0", "Body-1", "Eyelash-0", "Eyemask-0", "facial_normal-0", "facial_serious-0", "Feather-0", "Hair-0", "Skirt-0"],
        "Normal Broken": ["Broken-0", "Body-0", "Body-1", "Eyelash-0", "Eyemask-0", "facial_normal-0", "facial_serious-0", "Feather-0", "Hair-0"],
        "Base": ["Body-0", "Body-1", "Eyelash-0", "Eyemask-0", "facial_normal-0", "facial_serious-0", "Hair-0"],
        "Armor": ["Armor_Body-1", "Armor_Head-1"],
        "DLC": ["DLC_Body-0", "DLC_Body-1", "DLC_Skirt-0", "Eyelash-0", "facial_normal-0", "facial_serious-0", "Hair-0"],
        "DLC Broken": ["DLC_Body-0", "DLC_Body-1", "DLC_Broken-0", "Eyelash-0", "facial_normal-0", "facial_serious-0", "Hair-0"]
    },
    "9S": {
        "Normal": ["Body-0", "Body-1", "Eyelash-1", "Eyelash_serious-1", "Eyemask-1", "Leg-0", "Leg-1", "Pants-0", "Pants-1", "facial_normal-1", "facial_normal-2", "facial_serious-1", "facial_serious-2", "mesh_pl0200-0", "mesh_pl0200-1"],
        "Self Destruct": ["Body-0", "Body-1", "Eyelash-1", "Eyelash_serious-1", "Eyemask-1", "Leg-0", "Leg-1", "facial_normal-1", "facial_normal-2", "facial_serious-1", "facial_serious-2", "mesh_pl0200-0", "mesh_pl0200-1"],
        "Normal Broken Left": ["Body-0", "Body-1", "Eyelash-1", "Eyelash_serious-1", "Eyemask-1", "Leg-0", "Leg-1", "facial_normal-1", "facial_normal-2", "facial_serious-1", "facial_serious-2", "mesh_es0200-0", "mesh_es0200-1"],
        "Normal Broken Right": ["Body-0", "Body-1", "Eyelash-1", "Eyelash_serious-1", "Eyemask-1", "Leg-0", "Leg-1", "Pants-0", "Pants-1", "facial_normal-1", "facial_normal-2", "facial_serious-1", "facial_serious-2", "mesh_es0206-0", "mesh_es0206-1"],
        "Normal Broken Holes": ["Body-0", "Body-1", "Eyelash-1", "Eyelash_serious-1", "Eyemask-1", "Leg-0", "Leg-1", "Pants-0", "Pants-1", "facial_normal-1", "facial_normal-2", "facial_serious-1", "facial_serious-2", "mesh_es0201-0", "mesh_es0201-1"],
        "Normal Broken 2B Hand": ["Body-0", "Body-1", "Eyelash-1", "Eyelash_serious-1", "Eyemask-1", "Leg-0", "Leg-1", "Pants-0", "Pants-1", "facial_normal-1", "facial_normal-2", "facial_serious-1", "facial_serious-2", "mesh_es0202-0", "mesh_es0202-1"],
        "DLC": ["DLC_Body-0", "DLC_Body-1", "DLC_Leg-0", "DLC_Leg-1", "DLC_Pants-1", "DLC_mesh_pl0200-0", "DLC_mesh_pl0200-1", "Eyelash-1", "Eyelash_serious-1", "Eyemask-1", "facial_normal-1", "facial_normal-2", "facial_serious-1", "facial_serious-2",],
        "DLC Broken Left": ["DLC_Body-0", "DLC_Body-1", "DLC_Leg-0", "DLC_Leg-1", "DLC_mesh_es0200-0", "DLC_mesh_es0200-1", "Eyelash-1", "Eyelash_serious-1", "Eyemask-1", "facial_normal-1", "facial_normal-2", "facial_serious-1", "facial_serious-2"],
        "DLC Broken Right": ["DLC_Body-0", "DLC_Body-1", "DLC_Leg-0", "DLC_Leg-1", "DLC_Pants-1", "DLC_mesh_es0206-0", "DLC_mesh_es0206-1", "Eyelash-1", "Eyelash_serious-1", "Eyemask-1", "facial_normal-1", "facial_normal-2", "facial_serious-1", "facial_serious-2"],
        "DLC Broken Holes": ["DLC_Body-0", "DLC_Body-1", "DLC_Leg-0", "DLC_Leg-1", "DLC_Pants-1", "DLC_mesh_es0201-0", "DLC_mesh_es0201-1", "Eyelash-1", "Eyelash_serious-1", "Eyemask-1", "facial_normal-1", "facial_normal-2", "facial_serious-1", "facial_serious-2"],
        "DLC Broken 2B Hand": ["DLC_Body-0", "DLC_Body-1", "DLC_Leg-0", "DLC_Leg-1", "DLC_Pants-1", "DLC_mesh_es0202-0", "DLC_mesh_es0202-1", "Eyelash-1", "Eyelash_serious-1", "Eyemask-1", "facial_normal-1", "facial_normal-2", "facial_serious-1", "facial_serious-2"]
    },
    "A2": {
        "Normal": ["Body-0", "Body-1", "Cloth-0", "Hair-0", "facial_normal-0", "facial_serious-0"],
        "Beserk": ["Body-0", "Body-1", "Hair-0", "facial_normal-0", "facial_serious-0"],
        "DLC": ["DLC_Body-0", "DLC_Body-1", "DLC_Cloth-0", "Hair-0", "facial_normal-0", "facial_serious-0"]
    }
}
