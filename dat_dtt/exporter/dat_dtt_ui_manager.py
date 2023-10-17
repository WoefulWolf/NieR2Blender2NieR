import os
import time
import json

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper
from ...consts import DAT_EXTENSIONS
from ...utils.ioUtils import read_uint32

from ...utils.util import importContentsFileFromFolder, readFileOrderMetadata, readJsonDatInfo, saveDatInfo, triangulate_meshes, centre_origins, ShowMessageBox


class ExportAllSteps(bpy.types.PropertyGroup):
    useWmbStep: bpy.props.BoolProperty(
        name = "Export WMB4",
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

class DAT_DTT_PT_Export(bpy.types.Panel):
    bl_label = "Metal Gear Rising Revengeance Export"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        
        datTypes = [
            {
                "name": context.scene.DatExtension,
                "type": "dat",
                "showVarName": "ShowDatContents",
                "showVar": context.scene.ShowDatContents,
                "contentsVar": context.scene.DatContents
            },
            {
                "name": "dtt",
                "type": "dtt",
                "showVarName": "ShowDttContents",
                "showVar": context.scene.ShowDttContents,
                "contentsVar": context.scene.DttContents
            }
        ]

        for datType in datTypes:
            box = layout.box()
            row = box.row()
            row.scale_y = 1.125
            row.ui_units_y = 1.125
            subRow = row.row()
            subRow.prop(context.scene, datType["showVarName"], emboss=False,
                text= f"{datType['name'].upper()} Contents ({len(datType['contentsVar'])})",
                icon = "TRIA_DOWN" if datType["showVar"] else "TRIA_RIGHT")
            subRow = row.row(align=True)
            subRow.scale_x = 1.1
            subRow.scale_y = 1.05
            subRow.operator(AddDatDttContentsFile.bl_idname, text="", icon="FILE_NEW").type = datType["type"]
            subRow.operator(ImportDatDttContentsFile.bl_idname, text="", icon="FILE_FOLDER").type = datType["type"]
            if len(datType["contentsVar"]) > 0:
                subRow.operator(ClearDatDttAllContentsOperator.bl_idname, text="", icon="X").type = datType["type"]

            if datType["showVar"]:
                box = box.box()
                if len(datType["contentsVar"]) > 0:
                    columns = int(context.region.width / bpy.context.preferences.system.ui_scale // 170)
                    columns = max(columns, 1)
                    column = 0
                    for file in datType["contentsVar"]:
                        if column % columns == 0:
                            row = box.row()
                        cell = row.box().row()
                        cell.operator(ShowFullFilePath.bl_idname, emboss=False, text=os.path.basename(file.filepath)).filepath = file.filepath
                        remove_op = cell.operator("na.remove_datdtt_file", icon="X", text="")
                        remove_op.filepath = file.filepath
                        remove_op.type = datType["type"]
                        column += 1
                else:
                    row = box.row()
                    row.alignment = "CENTER"
                    row.label(text="No files added")

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
        ext = os.path.splitext(self.filepath)[1]
        # if self.target == "dat":
        #     context.scene.DatDir = directory
        #     if ext == ".dtt":
        #         self.report({'WARNING'}, "DTT directory selected, this field is for the DAT directory")
        #     # elif not context.scene.DttDir and directory.endswith(".dat"):
        #         # context.scene.DttDir = directory[:-4] + ".dtt"
        #     elif not context.scene.DttCon
        #     if not context.scene.ExportFileName:
        #         bpy.ops.na.get_base_name()
        # elif self.target == "dtt":
        #     context.scene.DttDir = directory
        #     if ext in DAT_EXTENSIONS:
        #         self.report({'WARNING'}, "DAT directory selected, this field is for the DTT directory")
        #     # elif not context.scene.DatDir and directory.endswith(".dtt"):
        #         # context.scene.DatDir = directory[:-4] + ".dat"
        #     if not context.scene.ExportFileName:
        #         bpy.ops.na.get_base_name()
        if self.target == "datdttdir":
            context.scene.DatDttExportDir = directory
        else:
            print("Invalid target", self.target)
            return {"CANCELLED"}

        return {'FINISHED'}

class ExportAll(bpy.types.Operator):
    '''Export Wmb4,Wta,Wtp,Dat,Dtt'''
    bl_idname = "na.export_all"
    bl_label = "Export all"
    bl_description = "Export scene to wmb4 not working, wat, wtp, dat, dtt files"

    def execute(self, context):
        t1 = time.time()
        exportedFilesCount = 0
        exportSteps: ExportAllSteps = context.scene.ExportAllSteps
        baseFilename = context.scene.ExportFileName
        datDttExportDir = context.scene.DatDttExportDir
        datExt = context.scene.DatExtension
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
            elif item.filepath.endswith('Layout.lay'):
                layFilePath = item.filepath
            elif item.filepath.endswith("GAArea.bxm"):
                gaFilePath = item.filepath
            elif item.filepath.endswith('.sar'):
                sarFilePath = item.filepath
            elif item.filepath.endswith('.wmb'):
                wmbFilePath = item.filepath

        for item in context.scene.DttContents:
            if item.filepath.endswith('.wtp'):
                wtpFilePath = item.filepath        

        datFileName = baseFilename + "." + datExt
        dttFileName = baseFilename + ".dtt"
        datFilePath = os.path.join(datDttExportDir, datFileName)
        dttFilePath = os.path.join(datDttExportDir, dttFileName)

        from ...wmb.exporter import wmb_exporter
        if exportSteps.useWmbStep:
            print("Exporting WMB4 not working")
            if exportSteps.triangulateMeshes:
                triangulate_meshes("WMB")
            if exportSteps.centerOrigins:
                centre_origins("WMB")
            if exportSteps.deleteLoose:
                bpy.ops.b2n.deleteloosegeometryall()
            wmb_exporter.main(wmbFilePath, True)
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
            if len(context.scene.DatContents) == 0:
                self.report({"ERROR"}, "No DAT contents to export!")
                print("No DAT contents to export!")
                return {"CANCELLED"}
            print("Exporting DAT")
            # get files list
            file_list = [item.filepath for item in context.scene.DatContents]
            file_list.sort()
            # save info file
            datInfoFilePath = os.path.join(os.path.dirname(file_list[0]), "dat_info.json")
            fileNames = [os.path.basename(file_path) for file_path in file_list]
            saveDatInfo(datInfoFilePath, fileNames, datFileName)
            # export dtt
            export_dat.main(datFilePath, file_list)
            exportedFilesCount += 1
        if exportSteps.useDttStep:
            if len(context.scene.DttContents) == 0:
                self.report({"ERROR"}, "No DTT contents to export!")
                print("No DTT contents to export!")
                return {"CANCELLED"}
            print("Exporting DTT")
            # get files list
            file_list = [item.filepath for item in context.scene.DttContents]
            file_list.sort()
            # save info file
            datInfoFilePath = os.path.join(os.path.dirname(file_list[0]), "dat_info.json")
            fileNames = [os.path.basename(file_path) for file_path in file_list]
            saveDatInfo(datInfoFilePath, fileNames, dttFileName)
            # export dtt
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
        else:
            self.report({"WARNING"}, "Couldn't auto fill base name")
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
        contentsList: bpy.types.CollectionProperty
        if self.type == "dat":
            contentsList = context.scene.DatContents
        elif self.type == "dtt":
            contentsList = context.scene.DttContents
        else:
            raise Exception("Invalid type")

        dir = self.directory
        #fdir = self.properties.filepath
        warnings = set()
        skippedFiles = 0
        for file_elem in self.files:
            path = os.path.join(dir, file_elem.name)
            name, ext = os.path.splitext(path)
            skip = False
            for file in contentsList:
                if file.filepath == path or os.path.basename(file.filepath) == os.path.basename(path):
                    warnings.add("File already added!")
                    skip = True
                    break
            if len(ext) > 4:
                warnings.add("File extension too long!")
                skip = True
            if skip:
                skippedFiles += 1
                continue
            added_file = contentsList.add()
            added_file.filepath = path

        if len(warnings) == 1:
            self.report({"WARNING"}, f"{skippedFiles} files skipped ({next(iter(warnings))})")
        elif len(warnings) > 1:
            print(f"{len(warnings)} warnings:")
            print("\n".join(warnings))
            self.report({"WARNING"}, f"{skippedFiles} files skipped ({'; '.join(warnings)})")
        
        return {'FINISHED'}

class RemoveDatDttFileOperator(bpy.types.Operator):
    '''Remove a file from DAT/DTT contents'''
    bl_idname = "na.remove_datdtt_file"
    bl_label = "Remove"
    bl_options = {"UNDO"}

    filepath : bpy.props.StringProperty(options={'HIDDEN'})
    type: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        contentsList: bpy.types.CollectionProperty
        if self.type == "dat":
            contentsList = context.scene.DatContents
        elif self.type == "dtt":
            contentsList = context.scene.DttContents
        else:
            raise Exception("Invalid type")

        index_to_remove = 0
        for i, item in enumerate(contentsList):
            if item.filepath == self.filepath:
                index_to_remove = i
                break
        contentsList.remove(index_to_remove)
        return {"FINISHED"}

class ClearDatDttAllContentsOperator(bpy.types.Operator):
    '''Clear DAT/DTT contents'''
    bl_idname = "na.clear_datdtt_contents"
    bl_label = "Clear Contents"
    bl_options = {"UNDO"}

    type: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        if self.type == "dat":
            context.scene.DatContents.clear()
        elif self.type == "dtt":
            context.scene.DttContents.clear()
        return {"FINISHED"}

class ImportDatDttContentsFile(bpy.types.Operator, ImportHelper):
    '''Import the contents of a "file_order.metadata" or "dat_info.json" file or a folder with theses files'''
    bl_idname = "na.import_datdtt_contents_file"
    bl_label = "Contents File or Folder"
    bl_options = {"UNDO"}
    filter_glob: StringProperty(default="*dat_info.json;*order.metadata", options={'HIDDEN'})

    type: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        filepath = self.filepath
        isDir = os.path.isdir(filepath)
        dirname = filepath if isDir else os.path.dirname(filepath)
        # Check if valid selection:
        # selection should exist
        if not os.path.exists(filepath):
            if not os.path.exists(dirname):
                self.report({"ERROR"}, "File doesn't exist!")
                return {"CANCELLED"}
            # if it doesn't, but it's a folder, try to find a file_order.metadata or dat_info.json file
            # blender adds the last selected filename to the path when importing a folder
            # so we need to remove it
            else:
                filepath = dirname
                isDir = True
        # if is file, check if filename is valid or if it's a folder
        if os.path.basename(filepath) not in ["file_order.metadata", "dat_info.json"] and \
                    not os.path.isdir(filepath):
            self.report({"ERROR"}, "Invalid file name! Please select either a 'file_order.metadata' or 'dat_info.json' file.")
            return {"CANCELLED"}
        
        contentsList: bpy.types.CollectionProperty
        if self.type == "dat":
            contentsList = context.scene.DatContents
            if dirname.endswith(".dtt"):
                self.report({"WARNING"}, "You selected a DTT folder, but the contents will be added to the DAT file")
        elif self.type == "dtt":
            contentsList = context.scene.DttContents
            if dirname[-4:] in DAT_EXTENSIONS:
                self.report({"WARNING"}, "You selected a DAT folder, but the contents will be added to the DTT file")
        else:
            raise Exception("Invalid type")

        # Clear current context
        contentsList.clear()

        # Parse the appropriate file and add files to contents
        root, ext = os.path.splitext(filepath)
        if isDir:
            if not importContentsFileFromFolder(filepath, contentsList):
                self.report({"ERROR"}, "No 'file_order.metadata' or 'dat_info.json' file found in directory!")
                return {"CANCELLED"}
        elif ext == ".json":
            readJsonDatInfo(filepath, contentsList)
        elif ext == ".metadata":
            readFileOrderMetadata(filepath, contentsList)
        
        return {"FINISHED"}

class FilePathProp(bpy.types.PropertyGroup):
    filepath: bpy.props.StringProperty()
    include: bpy.props.BoolProperty(default=True)

class ShowFullFilePath(bpy.types.Operator):
    '''Show this file's full path'''
    bl_idname = "na.show_full_filepath"
    bl_label = "Show Full Filepath"
    bl_options = {"UNDO"}

    filepath : bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        ShowMessageBox(self.filepath, os.path.basename(self.filepath))
        return {"FINISHED"}

classes = (
    ExportAllSteps,
    DAT_DTT_PT_Export,
    SelectFolder,
    ExportAll,
    GetBaseName,
    FilePathProp,
    AddDatDttContentsFile,
    RemoveDatDttFileOperator,
    ClearDatDttAllContentsOperator,
    ImportDatDttContentsFile,
    ShowFullFilePath
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.ExportAllSteps = bpy.props.PointerProperty(type=ExportAllSteps)
    bpy.types.Scene.ShowDatContents = bpy.props.BoolProperty (
        name = "Dat Contents",
        default = False,
    )
    bpy.types.Scene.DatContents = bpy.props.CollectionProperty(
        type = FilePathProp
    )
    bpy.types.Scene.DatExtension = bpy.props.StringProperty(
        name = "Dat Extension",
        default = "dat",
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
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.ExportAllSteps
    del bpy.types.Scene.ShowDatContents
    del bpy.types.Scene.DatContents
    del bpy.types.Scene.ShowDttContents
    del bpy.types.Scene.DttContents
    del bpy.types.Scene.ExportFileName
    del bpy.types.Scene.DatDttExportDir