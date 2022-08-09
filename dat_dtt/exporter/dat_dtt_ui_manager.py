import os
import time

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

from ...utils.util import triangulate_meshes, centre_origins


class ExportAllSteps(bpy.types.PropertyGroup):
    useWmbStep: bpy.props.BoolProperty(
        name = "Export WMB",
        default = True
    )
    useWtpStep: bpy.props.BoolProperty(
        name = "Export WTP",
        default = True
    )
    useWtaStep: bpy.props.BoolProperty(
        name = "Export WTA",
        default = True
    )
    useColStep: bpy.props.BoolProperty(
        name = "Export COL",
        default = False
    )
    useLayStep: bpy.props.BoolProperty(
        name = "Export LAY",
        default = False
    )
    useSarStep: bpy.props.BoolProperty(
        name = "Export SAR",
        default = False
    )
    useGaStep: bpy.props.BoolProperty(
        name = "Export GAArea",
        default = False
    )
    useDatStep: bpy.props.BoolProperty(
        name = "Export DAT",
        default = True
    )
    useDttStep: bpy.props.BoolProperty(
        name = "Export DTT",
        default = True
    )

    triangulateMeshes: bpy.props.BoolProperty(
        name = "Triangulate Meshes",
        default = True
    )
    centerOrigins: bpy.props.BoolProperty(
        name = "Center Origin",
        default = True,
        description = "Set object origins to world origin"
    )
    deleteLoose: bpy.props.BoolProperty(
        name = "Delete Loose Geometry",
        default = True
    )

class ExportDATOperator(bpy.types.Operator, ExportHelper):
    '''Export DAT'''
    bl_idname = "na.export_dat"
    bl_label = "Export DAT"
    filename_ext = ".dat"
    filter_glob: StringProperty(default="*.dat", options={'HIDDEN'})

    def execute(self, context):
        from . import export_dat
        export_dat.main(context.scene.DatDir, self.filepath)
        return {'FINISHED'}

class ExportDTTOperator(bpy.types.Operator, ExportHelper):
    '''Export DTT'''
    bl_idname = "na.export_dtt"
    bl_label = "Export DTT"
    filename_ext = ".dtt"
    filter_glob: StringProperty(default="*.dtt", options={'HIDDEN'})

    def execute(self, context):
        from . import export_dat
        export_dat.main(context.scene.DttDir, self.filepath)
        return {'FINISHED'}

class DAT_DTT_PT_Export(bpy.types.Panel):
    bl_label = "NieR:Automata Export"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        row = box.row(align=True)
        row.scale_y = 1.125
        row.ui_units_y = 1.125
        row.label(text="DAT Directory:")
        row.prop(context.scene, "DatDir", text="")
        row.operator("na.folder_select", icon="FILE_FOLDER", text="").target = "dat"

        row = box.row(align=True)
        row.scale_y = 1.125
        row.ui_units_y = 1.125
        row.label(text="DTT Directory:")
        row.prop(context.scene, "DttDir", text="")
        row.operator("na.folder_select", icon="FILE_FOLDER", text="").target = "dtt"

        row = box.row(align=True)
        row.scale_y = 1.125
        row.ui_units_y = 1.125
        row.label(text="Base Name")
        row.prop(context.scene, "ExportFileName", text="")
        row.operator("na.get_base_name", icon="LOOP_BACK", text="")
        row = box.row(align=True)
        row.scale_y = 1.125
        row.ui_units_y = 1.125
        row.label(text="DAT/DTT Export Directory")
        row.prop(context.scene, "DatDttExportDir", text="")
        row.operator("na.folder_select", icon="FILE_FOLDER", text="").target = "datdttdir"

        box = layout.box()
        row = box.row()
        row.alignment = "CENTER"
        row.label(text="Export Steps")
        row = box.row(align=True)
        row.scale_y = 1.125
        row.prop(context.scene.ExportAllSteps, "useWmbStep", text="WMB", icon="PANEL_CLOSE" if context.scene.ExportAllSteps.useWmbStep else "ADD")
        row.prop(context.scene.ExportAllSteps, "useWtpStep", text="WTP", icon="PANEL_CLOSE" if context.scene.ExportAllSteps.useWtpStep else "ADD")
        row.prop(context.scene.ExportAllSteps, "useWtaStep", text="WTA", icon="PANEL_CLOSE" if context.scene.ExportAllSteps.useWtaStep else "ADD")
        row = box.row(align=True)
        row.scale_y = 1.125
        secondRowItemCount = 0
        if context.scene.ExportAllSteps.useColStep or "COL" in bpy.data.collections:
            row.prop(context.scene.ExportAllSteps, "useColStep", text="COL", icon="PANEL_CLOSE" if context.scene.ExportAllSteps.useColStep else "ADD")
            secondRowItemCount += 1
        if context.scene.ExportAllSteps.useLayStep or "LAY" in bpy.data.collections:
            row.prop(context.scene.ExportAllSteps, "useLayStep", text="LAY", icon="PANEL_CLOSE" if context.scene.ExportAllSteps.useLayStep else "ADD")
            secondRowItemCount += 1
        if context.scene.ExportAllSteps.useSarStep or "SAR" in bpy.data.collections:
            row.prop(context.scene.ExportAllSteps, "useSarStep", text="SAR", icon="PANEL_CLOSE" if context.scene.ExportAllSteps.useSarStep else "ADD")
            secondRowItemCount += 1
        if context.scene.ExportAllSteps.useGaStep or "GaArea" in bpy.data.collections:
            row.prop(context.scene.ExportAllSteps, "useGaStep", text="GAArea", icon="PANEL_CLOSE" if context.scene.ExportAllSteps.useGaStep else "ADD")
            secondRowItemCount += 1
        if secondRowItemCount >= 3:
            row = box.row(align=True)
            row.scale_y = 1.125
        row.prop(context.scene.ExportAllSteps, "useDatStep", text="DAT", icon="PANEL_CLOSE" if context.scene.ExportAllSteps.useDatStep else "ADD")
        row.prop(context.scene.ExportAllSteps, "useDttStep", text="DTT", icon="PANEL_CLOSE" if context.scene.ExportAllSteps.useDttStep else "ADD")
        row = box.row(align=True)
        row.prop(context.scene.ExportAllSteps, "triangulateMeshes", text="Triangulate", icon="MOD_TRIANGULATE")
        row.prop(context.scene.ExportAllSteps, "centerOrigins", text="Center Origins", icon="OBJECT_ORIGIN")
        row.prop(context.scene.ExportAllSteps, "deleteLoose", text="Delete Loose", icon="SNAP_VERTEX")

        layout.separator()

        row = layout.row()
        row.scale_y = 2.0
        row.operator("na.export_all", text="One Click Export All", icon="EXPORT")


class SelectFolder(bpy.types.Operator, ImportHelper):
    '''Select Folder'''
    bl_idname = "na.folder_select"
    bl_label = "Select Directory"
    filename_ext = ""
    dirpath : StringProperty(name = "", description="Choose directory:", subtype='DIR_PATH')

    target : bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        directory = os.path.dirname(self.filepath)
        if self.target == "dat":
            context.scene.DatDir = directory
            if directory.endswith(".dtt"):
                self.report({'WARNING'}, "DTT directory selected, this field is for the DAT directory")
            elif not context.scene.DttDir:
                context.scene.DttDir = directory.replace("dat", "dtt")
            if not context.scene.ExportFileName:
                bpy.ops.na.get_base_name()
        elif self.target == "dtt":
            context.scene.DttDir = directory
            if directory.endswith(".dat"):
                self.report({'WARNING'}, "DAT directory selected, this field is for the DTT directory")
            elif not context.scene.DatDir:
                context.scene.DatDir = directory.replace("dtt", "dat")
            if not context.scene.ExportFileName:
                bpy.ops.na.get_base_name()
        elif self.target == "datdttdir":
            context.scene.DatDttExportDir = directory
        else:
            print("Invalid target", self.target)
            return {"CANCELLED"}

        return {'FINISHED'}

class ExportAll(bpy.types.Operator):
    '''Export wmb, wat, wtp, dat, dtt'''
    bl_idname = "na.export_all"
    bl_label = "Export all"
    bl_description = "Export scene to wmb, wat, wtp, dat, dtt files"

    def execute(self, context):
        t1 = time.time()
        exportedFilesCount = 0
        exportSteps: ExportAllSteps = context.scene.ExportAllSteps
        datDir = context.scene.DatDir
        dttDir = context.scene.DttDir
        baseFilename = context.scene.ExportFileName
        datDttExportDir = context.scene.DatDttExportDir

        if not datDir and (exportSteps.useWtaStep or exportSteps.useColStep or exportSteps.useLayStep or exportSteps.useDatStep or exportSteps.useSarStep or exportSteps.useGaStep):
            self.report({"ERROR"}, "Missing DAT Directory!")
            return {"CANCELLED"}
        if not dttDir and (exportSteps.useWtpStep or exportSteps.useWmbStep or exportSteps.useDttStep):
            self.report({"ERROR"}, "Missing DTT Directory!")
            return {"CANCELLED"}
        if not datDttExportDir and (exportSteps.useDatStep or exportSteps.useDttStep):
            self.report({"ERROR"}, "Missing DAT/DTT Export Directory!")
            return {"CANCELLED"}
        if not baseFilename:
            self.report({"ERROR"}, "Missing Base Name!")
            return {"CANCELLED"}
        
        wmbFilePath = os.path.join(dttDir, baseFilename + ".wmb")
        wtpFilePath = os.path.join(dttDir, baseFilename + ".wtp")
        wtaFilePath = os.path.join(datDir, baseFilename + ".wta")
        colFilePath = os.path.join(datDir, baseFilename + ".col")
        layFilePath = os.path.join(datDir, "Layout" + ".lay")
        if exportSteps.useSarStep:
            sarColl = bpy.data.objects["Field-Root"].users_collection[0]
            sarFilePath = os.path.join(datDir, sarColl.name.replace("SAR_", ""))
        gaFilePath = os.path.join(datDir, "GAArea" + ".bxm")
        datFilePath = os.path.join(datDttExportDir, baseFilename + ".dat")
        dttFilePath = os.path.join(datDttExportDir, baseFilename + ".dtt")

        from ...wmb.exporter import wmb_exporter
        if exportSteps.useWmbStep:
            print("Exporting WMB")
            if exportSteps.triangulateMeshes:
                triangulate_meshes("WMB")
            if exportSteps.centerOrigins:
                centre_origins("WMB")
            if exportSteps.deleteLoose:
                bpy.ops.b2n.deleteloosegeometryall()
            wmb_exporter.main(wmbFilePath)
            exportedFilesCount += 1
        from ...wta_wtp.exporter import export_wta, export_wtp
        if exportSteps.useWtaStep:
            print("Exporting WTA")
            export_wta.main(context, wtaFilePath)
            exportedFilesCount += 1
        if exportSteps.useWtpStep:
            print("Exporting WTP")
            export_wtp.main(context, wtpFilePath)
            exportedFilesCount += 1
        from ...col.exporter import col_exporter
        if exportSteps.useColStep:
            print("Exporting COL")
            if exportSteps.triangulateMeshes:
                triangulate_meshes("COL")
            if exportSteps.centerOrigins:
                centre_origins("COL")
            if exportSteps.deleteLoose:
                bpy.ops.b2n.deleteloosegeometryall()
            col_exporter.main(colFilePath, True)
            exportedFilesCount += 1
        from ...lay.exporter import lay_exporter
        if exportSteps.useLayStep:
            print("Exporting LAY")
            lay_exporter.main(layFilePath)
            exportedFilesCount += 1
        if exportSteps.useSarStep:
            print("Exporting SAR")
            from ...bxm.exporter import sarExporter
            sarExporter.exportSar(sarFilePath)
            exportedFilesCount += 1
        if exportSteps.useGaStep:
            print("Exporting GaArea")
            from ...bxm.exporter import gaAreaExporter
            gaAreaExporter.exportGaArea(gaFilePath)
            exportedFilesCount += 1
        from . import export_dat
        if exportSteps.useDatStep:
            print("Exporting DAT")
            export_dat.main(datDir, datFilePath)
            exportedFilesCount += 1
        if exportSteps.useDttStep:
            print("Exporting DTT")
            export_dat.main(dttDir, dttFilePath)
            exportedFilesCount += 1

        tDiff = int(time.time() - t1)

        print(f"Exported {exportedFilesCount} files in {tDiff}s   :P")
        self.report({"INFO"}, f"Exported {exportedFilesCount} files")

        return {"FINISHED"}

class GetBaseName(bpy.types.Operator):
    '''Set base name to scene name'''
    bl_idname = "na.get_base_name"
    bl_label = "Get the base file name"
    bl_description = "Set base name to scene name"
        
    def execute(self, context):
        if "WMB" in bpy.data.collections and len(bpy.data.collections["WMB"].children) > 0:
            context.scene.ExportFileName = bpy.data.collections["WMB"].children[0].name
        elif context.scene.DatDir:
            context.scene.ExportFileName = os.path.basename(context.scene.DatDir).replace(".dat", "")
        elif context.scene.DttDir:
            context.scene.ExportFileName = os.path.basename(context.scene.DttDir).replace(".dtt", "")
        return {"FINISHED"}

def register():
    bpy.utils.register_class(ExportAllSteps)
    bpy.utils.register_class(DAT_DTT_PT_Export)
    bpy.utils.register_class(SelectFolder)
    bpy.utils.register_class(ExportDATOperator)
    bpy.utils.register_class(ExportDTTOperator)
    bpy.utils.register_class(ExportAll)
    bpy.utils.register_class(GetBaseName)

    bpy.types.Scene.ExportAllSteps = bpy.props.PointerProperty(type=ExportAllSteps)
    bpy.types.Scene.DatDir = bpy.props.StringProperty(
        name = "DAT Directory",
    )
    bpy.types.Scene.DttDir = bpy.props.StringProperty(
        name = "DTT Directory",
    )
    bpy.types.Scene.ExportFileName = bpy.props.StringProperty(
        name = "Base File Name",
        description = "When exporting the .wmb/.dat/... extension will be added to the base"
    )
    bpy.types.Scene.DatDttExportDir = bpy.props.StringProperty(
        name = "DAT/DTT Export Directory",
        description = "When exporting this is where the final DAT/DTT files will be placed"
    )

def unregister():
    bpy.utils.unregister_class(ExportAllSteps)
    bpy.utils.unregister_class(DAT_DTT_PT_Export)
    bpy.utils.unregister_class(SelectFolder)
    bpy.utils.unregister_class(ExportDATOperator)
    bpy.utils.unregister_class(ExportDTTOperator)
    bpy.utils.unregister_class(ExportAll)
    bpy.utils.unregister_class(GetBaseName)

    del bpy.types.Scene.ExportAllSteps
    del bpy.types.Scene.DatDir
    del bpy.types.Scene.DttDir
    del bpy.types.Scene.ExportFileName
    del bpy.types.Scene.DatDttExportDir