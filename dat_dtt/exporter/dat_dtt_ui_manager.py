import os
import time

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper
from ...utils.ioUtils import read_uint32

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
        default = True,
        description = "Set object origins to world origin"
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
        
        datTypes = [
            {
                "name": "dat",
                "showVarName": "ShowDatContents",
                "showVar": context.scene.ShowDatContents,
                "contentsVar": context.scene.DatContents
            },
            {
                "name": "dtt",
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
            subRow.operator(AddDatDttContentsFile.bl_idname, text="", icon="FILE_NEW").type = datType["name"]
            subRow.operator(ImportDatDttContentsFile.bl_idname, text="", icon="FILE_FOLDER").type = datType["name"]
            if len(datType["contentsVar"]) > 0:
                subRow.operator(ClearDatDttAllContentsOperator.bl_idname, text="", icon="X").type = datType["name"]

            if datType["showVar"]:
                box = box.box()
                row = box.row()
                if len(datType["contentsVar"]) > 0:
                    columns = int(context.region.width / bpy.context.preferences.system.ui_scale // 150)
                    columns = box.column_flow(columns=columns, align=False)
                    for file in datType["contentsVar"]:
                        row = columns.box().row()
                        row.operator(ShowFullFilePath.bl_idname, emboss=False, text=os.path.basename(file.filepath)).filepath = file.filepath
                        remove_op = row.operator("na.remove_datdtt_file", icon="X", text="")
                        remove_op.filepath = file.filepath
                        remove_op.type = datType["name"]
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
        if self.target == "dat":
            context.scene.DatDir = directory
            if directory.endswith(".dtt"):
                self.report({'WARNING'}, "DTT directory selected, this field is for the DAT directory")
            elif not context.scene.DttDir and directory.endswith(".dat"):
                context.scene.DttDir = directory[:-4] + ".dtt"
            if not context.scene.ExportFileName:
                bpy.ops.na.get_base_name()
        elif self.target == "dtt":
            context.scene.DttDir = directory
            if directory.endswith(".dat"):
                self.report({'WARNING'}, "DAT directory selected, this field is for the DTT directory")
            elif not context.scene.DatDir and directory.endswith(".dtt"):
                context.scene.DatDir = directory[:-4] + ".dat"
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
    '''Import the contents of a "file_order.metadata" or "extracted_files.txt" file'''
    bl_idname = "na.import_datdtt_contents_file"
    bl_label = "Import Contents File"
    bl_options = {"UNDO"}
    filter_glob: StringProperty(default="*.metadata;*.txt", options={'HIDDEN'})

    type: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        if os.path.basename(self.filepath) not in ["file_order.metadata", "extracted_files.txt"] and \
                    not os.path.isdir(self.filepath):
            self.report({"ERROR"}, "Invalid file name! Please select either a 'file_order.metadata' or 'extracted_files.txt' file.")
            return {"FINISHED"}
        
        contentsList: bpy.types.CollectionProperty
        if self.type == "dat":
            contentsList = context.scene.DatContents
        elif self.type == "dtt":
            contentsList = context.scene.DttContents
        else:
            raise Exception("Invalid type")

        # Clear current context
        contentsList.clear()

        def readTxtFile(filepath):
            with open(filepath, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        added_file = contentsList.add()
                        added_file.filepath = os.path.join(os.path.dirname(self.filepath), line)
        def readFileOrderMetadata(filepath):
            if filepath.endswith("hash_order.metadata"):
                self.report({"ERROR"}, "hash_order.metadata is not supported! Please use 'file_order.metadata' instead.")
                
            with open(filepath, "rb") as f:
                num_files = read_uint32(f)
                name_length = read_uint32(f)
                files = []
                for i in range(num_files):
                    files.append(f.read(name_length).decode("utf-8").strip("\x00"))
                for file in files:
                    added_file = contentsList.add()
                    added_file.filepath = os.path.join(self.filepath, file)

        # Parse the appropriate file and add files to contents
        root, ext = os.path.splitext(self.filepath)
        if os.path.isdir(self.filepath):
            # search for metadata or txt file
            for file in os.listdir(self.filepath):
                if file == "extracted_files.txt":
                    readTxtFile(os.path.join(self.filepath, file))
                elif file == "file_order.metadata":
                    readFileOrderMetadata(os.path.join(self.filepath, file))
                    break
            else:
                self.report({"ERROR"}, "No 'file_order.metadata' or 'extracted_files.txt' file found in directory!")
                return {"FINISHED"}
        elif ext == ".txt":
            readTxtFile(self.filepath)
        elif ext == ".metadata":
            readFileOrderMetadata(self.filepath)
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