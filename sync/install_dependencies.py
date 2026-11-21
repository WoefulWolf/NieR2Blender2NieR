#    Copyright (C) 2020  Robert Guetzkow
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>

from typing import Tuple
import bpy
import importlib
from collections import namedtuple

from .shared import dependencies_installed, setDropDownOperatorAndIcon, removeDropDownOperatorAndIcon

Dependency = namedtuple("Dependency", ["module", "package", "name"])

# The modules Sync needs. They ship with the extension as wheels (blender_manifest.toml "wheels"): Blender installs
# them into the extension's site-packages when the extension is installed, so nothing is downloaded or installed at
# run time. The package and (global) name can be None if they are equal to the module name.
dependencies = (Dependency(module="websocket", package="websocket-client", name=None),)

# Why the import failed, for the Sync menu entry's error.
dependency_error = ""


def import_module(module_name, global_name=None, reload=True):
    """
    Import a module.
    :param module_name: Module to import.
    :param global_name: (Optional) Name under which the module is imported. If None the module_name will be used.
       This allows to import under a different name with the same effect as e.g. "import numpy as np" where "np" is
       the global_name under which the module can be accessed.
    :raises: ImportError and ModuleNotFoundError
    """
    if global_name is None:
        global_name = module_name

    if global_name in globals():
        importlib.reload(globals()[global_name])
    else:
        # Attempt to import the module and assign it to globals dictionary. This allow to access the module under
        # the given name, just like the regular import would.
        globals()[global_name] = importlib.import_module(module_name)


class SYNC_OT_dependency_error(bpy.types.Operator):
    bl_idname = "sync.dependency_error"
    bl_label = "Sync Unavailable"
    bl_description = ("Sync with F-SERVO needs the websocket-client module bundled with this extension, "
                      "and it could not be imported. Reinstall the extension")
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        self.report({"ERROR"}, "Sync is unavailable: the bundled websocket-client module could not be imported "
                    f"({dependency_error}). Reinstall the extension.")
        return {"CANCELLED"}


preference_classes = (
    SYNC_OT_dependency_error,
)

def getDropDownButton() -> Tuple[str, str]:
    return (
        SYNC_OT_dependency_error.bl_idname,
        "ERROR"
    )

def register():
    global dependencies_installed, dependency_error
    dependencies_installed = False
    dependency_error = ""

    for cls in preference_classes:
        bpy.utils.register_class(cls)

    try:
        for dependency in dependencies:
            import_module(module_name=dependency.module, global_name=dependency.name)
        dependencies_installed = True
        from .syncUi import registerSync
        registerSync()
    except ImportError as err:
        # Don't register other panels, operators etc.
        dependency_error = str(err)
        print(f"NieR2Blender2NieR: Sync is unavailable, the bundled websocket-client could not be imported: {err}")
    
    if not dependencies_installed:
        setDropDownOperatorAndIcon(getDropDownButton)


def unregister():
    for cls in preference_classes:
        bpy.utils.unregister_class(cls)

    if dependencies_installed:
        from .syncUi import unregisterSync
        unregisterSync()
    
    if not dependencies_installed:
        removeDropDownOperatorAndIcon(getDropDownButton)
