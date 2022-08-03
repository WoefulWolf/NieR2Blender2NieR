import os
import time

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

from ...utils.util import triangulate_meshes, centre_origins, ShowMessageBox


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
        default = True
    )
    deleteLoose: bpy.props.BoolProperty(
        name = "Delete Loose Geometry",
        default = True
    )

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
        row.prop(context.scene, "ShowDatContents", emboss=False,
            text="DAT Contents",
            icon = "TRIA_DOWN" if context.scene.ShowDatContents else "TRIA_RIGHT")
        if context.scene.ShowDatContents:
            if len(context.scene.DatContents) > 14:
                columns = box.column_flow(columns=3, align=False)
            else:
                columns = box.column_flow(columns=2, align=False)
            for file in context.scene.DatContents:
                row = columns.box().row()
                row.operator("na.show_full_filepath", emboss=False, text=os.path.basename(file.filepath)).filepath = file.filepath
                row.operator("na.remove_dat_file", icon="X", text="").filepath = file.filepath
            row = box.row()
            row.operator("na.datdtt_file_selector", text="Add File(s)").type = "dat"

        box = layout.box()
        row = box.row(align=True)
        row.scale_y = 1.125
        row.ui_units_y = 1.125
        row.prop(context.scene, "ShowDttContents", emboss=False,
            text="DTT Contents",
            icon = "TRIA_DOWN" if context.scene.ShowDttContents else "TRIA_RIGHT")
        if context.scene.ShowDttContents:
            if len(context.scene.DttContents) > 14:
                columns = box.column_flow(columns=3, align=False)
            else:
                columns = box.column_flow(columns=2, align=False)
            for file in context.scene.DttContents:
                row = columns.box().row()
                row.operator("na.show_full_filepath", emboss=False, text=os.path.basename(file.filepath)).filepath = file.filepath
                row.operator("na.remove_dtt_file", icon="X", text="").filepath = file.filepath
            row = box.row()
            row.operator("na.datdtt_file_selector", text="Add File(s)").type = "dtt"

        box = layout.box()
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
        #datDir = context.scene.DatDir
        #dttDir = context.scene.DttDir
        baseFilename = context.scene.ExportFileName
        datDttExportDir = context.scene.DatDttExportDir
        """
        if not datDir and (exportSteps.useWtaStep or exportSteps.useColStep or exportSteps.useLayStep or exportSteps.useDatStep or exportSteps.useSarStep or exportSteps.useGaStep):
            self.report({"ERROR"}, "Missing DAT Directory!")
            return {"CANCELLED"}
        if not dttDir and (exportSteps.useWtpStep or exportSteps.useWmbStep or exportSteps.useDttStep):
            self.report({"ERROR"}, "Missing DTT Directory!")
            return {"CANCELLED"}
        """
        if not datDttExportDir and (exportSteps.useDatStep or exportSteps.useDttStep):
            self.report({"ERROR"}, "Missing DAT/DTT Export Directory!")
            return {"CANCELLED"}
        if not baseFilename:
            self.report({"ERROR"}, "Missing Base Name!")
            return {"CANCELLED"}

        if exportSteps.useSarStep:
            sarColl = bpy.data.objects["Field-Root"].users_collection[0]

        for item in context.scene.DatContents:
            if item.filepath.endswith('.wta'):
                wtaFilePath = item.filepath
            elif item.filepath.endswith('.col'):
                colFilePath = item.filepath
            elif item.filepath == 'Layout.lay':
                layFilePath = item.filepath
            elif item.filepath == "GAArea.bxm":
                gaFilePath = item.filepath
            elif item.filepath.endswith('.sar'):
                sarFilePath = item.filepath

        for item in context.scene.DttContents:
            if item.filepath.endswith('.wmb'):
                wmbFilePath = item.filepath
            elif item.filepath.endswith('.wtp'):
                wtpFilePath = item.filepath        

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
            file_list = []
            for item in context.scene.DatContents:
                file_list.append(item.filepath)
            file_list.sort()
            export_dat.main(datFilePath, file_list)
            exportedFilesCount += 1
        if exportSteps.useDttStep:
            print("Exporting DTT")
            file_list = []
            for item in context.scene.DttContents:
                file_list.append(item.filepath)
            file_list.sort()
            export_dat.main(dttFilePath, file_list)
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

class AddDatDttContentsFile(bpy.types.Operator, ImportHelper):
    '''Select file(s)'''
    bl_idname = "na.datdtt_file_selector"
    bl_label = "Select File(s) To Add"
    bl_options = {"UNDO"}

    files: bpy.props.CollectionProperty(
            name="File Path",
            type=bpy.types.OperatorFileListElement,
            )
    directory: bpy.props.StringProperty(
            subtype='DIR_PATH',
            )
    filter_glob: StringProperty(default="*", options={'HIDDEN'})

    type: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        dir = self.directory
        #fdir = self.properties.filepath
        for file_elem in self.files:
            path = os.path.join(dir, file_elem.name)
            if self.type == "dat":
                skip = False
                for file in context.scene.DatContents:
                    if file.filepath == path:
                        self.report({"ERROR"}, "File already added!")
                        skip = True
                        break
                if skip:
                    continue
                added_file = bpy.context.scene.DatContents.add()
                added_file.filepath = path
            elif self.type == "dtt":
                skip = False
                for file in context.scene.DttContents:
                    if file.filepath == path:
                        self.report({"ERROR"}, "File already added!")
                        skip = True
                        break
                if skip:
                    continue
                added_file = bpy.context.scene.DttContents.add()
                added_file.filepath = path
        return{'FINISHED'}

class RemoveDatFileOperator(bpy.types.Operator):
    '''Remove a file from DAT contents'''
    bl_idname = "na.remove_dat_file"
    bl_label = "Remove"
    bl_options = {"UNDO"}

    filepath : bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        index_to_remove = 0
        for i, item in enumerate(context.scene.DatContents):
            if item.filepath == self.filepath:
                index_to_remove = i
                break

        context.scene.DatContents.remove(index_to_remove)
        return {"FINISHED"}

class RemoveDttFileOperator(bpy.types.Operator):
    '''Remove a file from DTT contents'''
    bl_idname = "na.remove_dtt_file"
    bl_label = "Remove"
    bl_options = {"UNDO"}

    filepath : bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        index_to_remove = 0
        for i, item in enumerate(context.scene.DttContents):
            if item.filepath == self.filepath:
                index_to_remove = i
                break

        context.scene.DttContents.remove(index_to_remove)
        return {"FINISHED"}

class FilePathProp(bpy.types.PropertyGroup):
    filepath: bpy.props.StringProperty()
    include: bpy.props.BoolProperty(default=True)

class ShowFullFilePath(bpy.types.Operator):
    '''Show this file's full path.'''
    bl_idname = "na.show_full_filepath"
    bl_label = "Show Full Filepath"
    bl_options = {"UNDO"}

    filepath : bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        ShowMessageBox(self.filepath, os.path.basename(self.filepath))
        return {"FINISHED"}

def register():
    bpy.utils.register_class(ExportAllSteps)
    bpy.utils.register_class(DAT_DTT_PT_Export)
    bpy.utils.register_class(SelectFolder)
    bpy.utils.register_class(ExportAll)
    bpy.utils.register_class(GetBaseName)
    bpy.utils.register_class(FilePathProp)
    bpy.utils.register_class(AddDatDttContentsFile)
    bpy.utils.register_class(RemoveDatFileOperator)
    bpy.utils.register_class(RemoveDttFileOperator)
    bpy.utils.register_class(ShowFullFilePath)

    bpy.types.Scene.ExportAllSteps = bpy.props.PointerProperty(type=ExportAllSteps)
    bpy.types.Scene.ShowDatContents = bpy.props.BoolProperty (
        name = "Dat Contents",
        default = False,
    )
    bpy.types.Scene.DatContents = bpy.props.CollectionProperty(
        type = FilePathProp
    )
    bpy.types.Scene.ShowDttContents = bpy.props.BoolProperty (
        name = "Dtt Contents",
        default = False,
    )
    bpy.types.Scene.DttContents = bpy.props.CollectionProperty(
        type = FilePathProp
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
    bpy.utils.unregister_class(ExportAll)
    bpy.utils.unregister_class(GetBaseName)
    bpy.utils.unregister_class(FilePathProp)
    bpy.utils.unregister_class(AddDatDttContentsFile)
    bpy.utils.unregister_class(RemoveDatFileOperator)
    bpy.utils.unregister_class(RemoveDttFileOperator)
    bpy.utils.unregister_class(ShowFullFilePath)

    del bpy.types.Scene.ExportAllSteps
    del bpy.types.Scene.ShowDatContents
    del bpy.types.Scene.DatContents
    del bpy.types.Scene.ShowDttContents
    del bpy.types.Scene.DttContents
    del bpy.types.Scene.ExportFileName
    del bpy.types.Scene.DatDttExportDir