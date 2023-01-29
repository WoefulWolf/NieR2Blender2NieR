from typing import Tuple
import bpy
from .syncedObjects import initSyncedObjects
from .shared import setDropDownOperatorAndIcon, removeDropDownOperatorAndIcon
from .syncClient import connectToWebsocket, disconnectFromWebsocket, isConnectedToWs
from ..utils.util import ShowMessageBox

class StartSyncOperator(bpy.types.Operator):
    """Start Sync"""
    bl_idname = "n2b2n.start_sync"
    bl_label = "Sync with F-SERVO"
    bl_description = "Start Sync"
    bl_options = {"REGISTER"}

    connectionSuccess: bool

    def execute(self, context):
        self.connectionSuccess = False
        connectToWebsocket(self.onResult)
        return {"FINISHED"}

    def onResultDelayed(self):
        if self.connectionSuccess:
            initSyncedObjects()
            ShowMessageBox("Connected!", "Success")
        else:
            ShowMessageBox("Couldn't connect to websocket server", "Error")

    def onResult(self, success: bool):
        self.connectionSuccess = success
        bpy.app.timers.register(self.onResultDelayed, first_interval=0.005, persistent=False)

class StopSyncOperator(bpy.types.Operator):
    """Stop Sync"""
    bl_idname = "n2b2n.stop_sync"
    bl_label = "Stop Sync"
    bl_description = "Stop Sync"
    bl_options = {"REGISTER"}

    def execute(self, context):
        disconnectFromWebsocket()
        return {"FINISHED"}

def getDropDownButton() -> Tuple[str, str]:
    if isConnectedToWs():
        return (StopSyncOperator.bl_idname, "CANCEL")
    else:
        return (StartSyncOperator.bl_idname, "UV_SYNC_SELECT")

def registerSync():
    bpy.utils.register_class(StartSyncOperator)
    bpy.utils.register_class(StopSyncOperator)

    setDropDownOperatorAndIcon(getDropDownButton)

def unregisterSync():
    bpy.utils.unregister_class(StartSyncOperator)
    bpy.utils.unregister_class(StopSyncOperator)

    removeDropDownOperatorAndIcon(getDropDownButton)

    if isConnectedToWs():
        disconnectFromWebsocket()
