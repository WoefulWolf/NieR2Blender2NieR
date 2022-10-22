import bpy
from .syncedObjects import initSyncedObjects
from .syncClient import connectToWebsocket, disconnectFromWebsocket, isConnectedToWs
from .shared import dependencies_installed
from ..utils.util import drawMultilineLabel
from ..__init__ import bl_info

class StartSyncOperator(bpy.types.Operator):
    """Start Sync"""
    bl_idname = "n2b2n.start_sync"
    bl_label = "Start Sync"
    bl_description = "Start Sync"
    bl_options = {"REGISTER"}

    def execute(self, context):
        if connectToWebsocket():
            initSyncedObjects()
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

class SYNCUI_PT_sync_ui(bpy.types.Panel):
    bl_label = "Sync"
    bl_category = "Sync"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @classmethod
    def poll(self, context):
        return not dependencies_installed

    def draw(self, context):
        layout = self.layout

        if isConnectedToWs():
            layout.label(text="Connected to websocket")
        else:
            layout.operator(StartSyncOperator.bl_idname, text="Start Sync")

def registerSync():
    bpy.utils.register_class(StartSyncOperator)
    bpy.utils.register_class(SYNCUI_PT_sync_ui)

def unregisterSync():
    bpy.utils.unregister_class(StartSyncOperator)
    bpy.utils.unregister_class(SYNCUI_PT_sync_ui)

    if isConnectedToWs():
        disconnectFromWebsocket()
