# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import omni.client
import os
from pxr import Usd, UsdUtils, Sdf
from omni.physxclashdetectioncore.clash_query import ClashQuery
from omni.physxclashdetectioncore.clash_data import ClashData
from omni.physxclashdetectioncore.clash_info import ClashInfo
from omni.physxclashdetectioncore.clash_detect import ClashDetection
from omni.physxclashdetectioncore.clash_data_serializer_sqlite import ClashDataSerializerSqlite
from omni.physxclashdetectioncore.clash_detect_settings import SettingId
from omni.physxclashdetectioncore.clash_detect_export import export_to_html, export_to_json, ExportColumnDef
from omni.physxclashdetectioncore.utils import OptimizedProgressUpdate
from omni.physxclashdetectionbake import ClashDetectionBake


class ClashDetectionProcessor:
    """
    This class is designed to perform clash detection on 3D models using the USD (Universal Scene Description) framework.
    It supports exporting clash detection results to HTML and JSON formats for further analysis.
    """
    def __init__(
        self,
        stage_path_name: str,
        object_a_path: str = '',
        object_b_path: str = '',
        tolerance: float = 0.0,
        dynamic: bool = False,
        start_time: float = 0.0,
        end_time: float = 0.0,
        logging: bool = False,
        clash_bake: bool = False,
        clash_bake_meshes_layer_path: str = '',
        clash_bake_meshes_material_path: str = '',
        html_path_name: str = '',
        json_path_name: str = '',
        query_name: str = '',
        comment: str = '',
        search_for_duplicates: bool = False,
    ):
        """
        Parameters:
        stage_path_name: str - full path to a stage to be processed.
        object_a_path: str not Sdf.Path - absolute stage path or a USD collection to define searchset A.
        object_b_path: str not Sdf.Path - absolute stage path or a USD collection to define searchset B.
        tolerance: float - tolerance distance for overlap queries. Use zero for hard clashes, non-zero for soft (clearance) clashes.
        dynamic: bool - True for dynamic clash detection, False for static.
        start_time: float - start time in seconds. Only works when dynamic clash detection is enabled.
        end_time: float - end time in seconds. Only works when dynamic clash detection is enabled.
        logging: bool - If True, logs info & perf results to console.
        clash_bake: bool - True to bake the clash detection results into a new pair of layers.
        clash_bake_meshes_layer_path: str - full path to the layer where the baked meshes will be stored.
        clash_bake_meshes_material_path: str - full path to the material to be applied to the baked meshes.
        html_path_name: str - full path to HTML file if also export to HTML is needed. No clash images will be exported.
        json_path_name: str - full path to JSON file if also export to JSON is needed. No clash images will be exported.
        query_name: str - custom name for the clash detection query which will be generated based on parameters above.
        comment: str - custom comment for the clash detection query which will be generated based on parameters above.
        search_for_duplicates: True to search for static identical meshes with identical transformations (fully overlapping each other). Overrules dynamic setting.
        """
        self._stage_path_name = stage_path_name
        self._html_path_name = html_path_name
        self._json_path_name = json_path_name
        self._clash_bake = clash_bake
        self._clash_bake_meshes_layer_path = clash_bake_meshes_layer_path
        self._clash_bake_meshes_material_path = clash_bake_meshes_material_path
        self._query = ClashQuery(
            query_name=query_name,
            object_a_path=object_a_path,
            object_b_path=object_b_path,
            clash_detect_settings={
                SettingId.SETTING_LOGGING.name: logging,
                SettingId.SETTING_TOLERANCE.name: tolerance,
                SettingId.SETTING_DYNAMIC.name: dynamic,
                SettingId.SETTING_DYNAMIC_START_TIME.name: start_time,
                SettingId.SETTING_DYNAMIC_END_TIME.name: end_time,
                SettingId.SETTING_DUP_MESHES.name: search_for_duplicates,
            },
            comment=comment
        )
        self._new_clash_data_layer_path_name = ''  # path to the new clash data layer if new one was created

    def _export(self, clash_data: ClashData, num_overlaps_chk: int) -> bool:
        """
        Realizes the clash data export to HTML and JSON.
        Returns: True on success, False otherwise.
        """
        column_defs = [
            ExportColumnDef(0, "Clash ID"),
            ExportColumnDef(1, "Min Distance", True),
            ExportColumnDef(2, "Tolerance", True),
            ExportColumnDef(3, "Overlap Tris", True),
            ExportColumnDef(4, "Clash Start"),
            ExportColumnDef(5, "Clash End"),
            ExportColumnDef(6, "Records", True),
            ExportColumnDef(7, "Object A"),
            ExportColumnDef(8, "Object B"),
            ExportColumnDef(9, "Comment"),
        ]

        overlaps = clash_data.find_all_overlaps_by_query_id(self._query.identifier, False)
        if len(overlaps) != num_overlaps_chk:
            print("Serialization issue detected.")
        rows = [
            [
                o.overlap_id,
                f"{o.min_distance:.3f}",
                f"{o.tolerance:.3f}",
                str(o.overlap_tris),
                f"{o.start_time:.3f}",
                f"{o.end_time:.3f}",
                str(o.num_records),
                o.object_a_path,
                o.object_b_path,
                o.comment,
            ]
            for o in overlaps.values()
        ]

        if self._html_path_name:
            print(f"Exporting to HTML file '{self._html_path_name}'...")
            html_bytes = export_to_html("Clash Detection Results", self._stage_path_name, column_defs, rows)
            if not html_bytes or len(html_bytes) == 0:
                print("HTML export failed.")
                return False
            if omni.client.write_file(self._html_path_name, html_bytes) != omni.client.Result.OK:
                print(f"Failed writing HTML file to '{self._html_path_name}'.")
                return False
            html_bytes = None

        if self._json_path_name:
            print(f"Exporting to JSON file '{self._json_path_name}'...")
            json_bytes = export_to_json(column_defs, rows)
            if not json_bytes or len(json_bytes) == 0:
                print("JSON export failed.")
                return False
            if omni.client.write_file(self._json_path_name, json_bytes) != omni.client.Result.OK:
                print(f"Failed writing JSON file to '{self._json_path_name}'.")
                return False
            json_bytes = None

        return True

    def _detect_overlaps(self, stage: Usd.Stage, clash_detect: ClashDetection, clash_data: ClashData) -> int:
        """
        Runs clash detection engine, fetches results and serializes them.
        Returns number of overlaps found.
        """
        print("Running clash detection engine...", end="")
        progress_update = OptimizedProgressUpdate()
        num_steps = clash_detect.create_pipeline()
        for i in range(num_steps):
            step_data = clash_detect.get_pipeline_step_data(i)
            if step_data.finished:
                break
            if progress_update.update(step_data.progress):
                print(".", end="")
            clash_detect.run_pipeline_step(i)
        print("Finished.")

        num_overlaps = clash_detect.get_nb_overlaps()
        print(f"Fetching {num_overlaps} overlaps...", end="")
        for p in clash_detect.fetch_and_save_overlaps(stage, clash_data, self._query):
            print(".", end="")
        print("Finished.")

        return num_overlaps

    def _clean_overlaps_and_query(self) -> bool:
        """
        Cleans up the overlaps and queries from the clash data, ensuring a fresh state for new clash detection runs.
        Returns: True if the cleanup was successful, False otherwise.
        """
        stage_path_name = self._stage_path_name
        if not stage_path_name:
            print("Stage name to process was not provided.")
            return False
        print(f"Opening stage '{stage_path_name}'...")
        stage = Usd.Stage.Open(stage_path_name)
        if not stage:
            print(f"Failed to open stage '{stage_path_name}'")
            return False
        UsdUtils.StageCache.Get().Insert(stage)

        clash_data = ClashData(ClashDataSerializerSqlite())
        clash_data.open(UsdUtils.StageCache.Get().GetId(stage).ToLongInt(), True)

        affected_records = clash_data.remove_all_overlaps_by_query_id(self._query.identifier, False)
        print(f"{affected_records} clash {'record' if affected_records == 1 else 'records'} removed.")
        affected_records = clash_data.remove_query_by_id(self._query.identifier)
        print(f"{affected_records} clash {'query' if affected_records == 1 else 'queries'} removed.")
        self._query._identifier = 0

        clash_data.save()
        Usd.Stage.Save(stage)
        clash_data.saved()
        clash_data.close()
        clash_data.destroy()
        UsdUtils.StageCache.Get().Erase(stage)

        return True

    def _generate_dynamic_clash_bake(self, stage : Usd.Stage, clash_data : ClashData):
        """Executes a simple baking of clash results for current query"""
        if self._clash_bake_meshes_layer_path == '' or self._clash_bake_meshes_material_path == '':
            raise Exception("Clash Bake Generation needs paths for meshes and materials layers")
        
        # Collect all overlaps for given query WITH frame info in order to generate dynamic bake
        overlaps = clash_data.find_all_overlaps_by_query_id(clash_query_id=self._query.identifier, 
                                                            fetch_also_frame_info=True)
        
        clash_infos = [clash_info for clash_info in overlaps.values()]

        # Collect all a/b paths
        paths = [(str(ci.object_a_path), str(ci.object_b_path)) for ci in clash_infos]

        # Prepare bake infos
        bake_infos = ClashDetectionBake.prepare_clash_bake_infos(stage=stage, clash_infos=clash_infos)
        # Open or create two dedicates layers for clash baking, one for materials and one for meshes
        root_layer = stage.GetRootLayer()
        layer_meshes: Sdf.Layer = Sdf.Layer.CreateNew(self._clash_bake_meshes_layer_path)  # type: ignore
        layer_materials: Sdf.Layer = Sdf.Layer.CreateNew(self._clash_bake_meshes_material_path)  # type: ignore

        # Remove previously baked meshes (useful when opening an existing layer with pre-baked clash meshes)
        ClashDetectionBake.remove_baked_meshes(stage=stage, paths=paths)

        # NOTE: The layers must have same time codes per second as the original stage
        layer_meshes.timeCodesPerSecond = root_layer.timeCodesPerSecond  # type: ignore
        layer_materials.timeCodesPerSecond = root_layer.timeCodesPerSecond  # type: ignore

        # Insert layers into stage
        session_layer = stage.GetSessionLayer()
        session_layer.subLayerPaths.append(layer_meshes.identifier)
        session_layer.subLayerPaths.append(layer_materials.identifier)

        # Copy Support files (material shaders mainly) to same folder where layers live
        support_paths = ClashDetectionBake.get_support_files_paths()
        dest_folder = os.path.dirname(str(layer_materials.identifier))
        for src in support_paths:
            dest = os.path.join(dest_folder, os.path.basename(src))
            omni.client.copy(src, dest, omni.client.CopyBehavior.OVERWRITE)

        old_edit_target = stage.GetEditTarget()
        try:
            # Generate materials before they're referenced by meshes.
            # Generating them on a separate layer is not mandatory.
            stage.SetEditTarget(layer_materials)
            print("Baking materials")
            materials = ClashDetectionBake.bake_clash_materials(stage)

            # Bake clash meshes
            # This can be taking some time so if needed just split the bake_infos in batches to give some time to user
            # interfaces updates in order to display progress.
            # Generating them on a separate layer is not mandatory.
            stage.SetEditTarget(layer_meshes)
            print("Baking Meshes")
            ClashDetectionBake.bake_clash_meshes(stage=stage, bake_infos=bake_infos, materials=materials)

            # Finalize mesh baking (runs optimization / merge operations)
            # Also this operation can be taking some time so if needed split paths in batches and interleave with user
            # interface updates in order to display progress.
            print("Finalizing Meshes")
            ClashDetectionBake.finalize_clash_meshes(stage=stage, paths=paths)
        finally:
            # Make sure to restore original edit target in any case
            # And remove clash dedicated layers from session layer
            stage.SetEditTarget(old_edit_target)
            session_layer.subLayerPaths.remove(layer_meshes.identifier)
            session_layer.subLayerPaths.remove(layer_materials.identifier)

        print("Clash baking finished")

        # Save the layers
        layer_materials.Save()  # type: ignore
        layer_meshes.Save()  # type: ignore

        del layer_materials
        del layer_meshes

    def run(self) -> bool:
        """
        Performs the clash detection.
        Returns True if run was successful, False otherwise.
        """
        stage_path_name = self._stage_path_name
        if not stage_path_name:
            print("Stage name to process was not provided.")
            return False
        print(f"Opening stage '{stage_path_name}'...")
        stage = Usd.Stage.Open(stage_path_name)
        if not stage:
            print(f"Failed to open stage '{stage_path_name}'")
            return False
        UsdUtils.StageCache.Get().Insert(stage)

        clash_data = ClashData(ClashDataSerializerSqlite())
        clash_data.open(UsdUtils.StageCache.Get().GetId(stage).ToLongInt(), True)

        print("Creating new query...")
        new_query_id = clash_data.insert_query(self._query, True, True)
        if not new_query_id or new_query_id < 1:
            print("Failed to save clash detection query...")
            return False

        new_clash_data_layer = False
        if clash_data._target_layer and clash_data._target_layer.anonymous:
            new_clash_data_layer = True

        print("Setting up clash detection engine...")
        clash_detect = ClashDetection()
        if not clash_detect.set_settings(self._query.clash_detect_settings, stage):
            print("Failed to set clash detection settings.")
            return False
        if not clash_detect.set_scope(
            stage,
            self._query.object_a_path,
            self._query.object_b_path,
            self._query.clash_detect_settings.get(SettingId.SETTING_DUP_MESHES.name, False)
        ):
            print("Failed to set clash detection scope.")
            return False

        num_overlaps = self._detect_overlaps(stage, clash_detect, clash_data)
        if self._clash_bake:
            print(f"Generating Clash Bake Layers for '{stage_path_name}'...")
            self._generate_dynamic_clash_bake(stage, clash_data)

        print(f"Saving stage '{stage_path_name}'...")
        if not clash_data.save():
            print("Failed to save clash detection results.")
        # now make sure, that the layer is referenced by relative path, not absolute
        root_layer = stage.GetRootLayer()
        for path in root_layer.subLayerPaths:
            if path == clash_data._target_layer.identifier:
                root_layer.subLayerPaths.remove(path)
                rel_path = os.path.relpath(clash_data._target_layer.identifier, os.path.dirname(root_layer.identifier))
                root_layer.subLayerPaths.append(rel_path)
                break
        Usd.Stage.Save(stage)
        clash_data.saved()

        if new_clash_data_layer:
            self._new_clash_data_layer_path_name = clash_data._target_layer.identifier

        if self._json_path_name or self._html_path_name:
            self._export(clash_data, num_overlaps)

        print(f"Closing stage '{stage_path_name}'...")
        UsdUtils.StageCache.Get().Erase(stage)
        clash_data.close()
        clash_data.destroy()

        return True

    def clean_up(self) -> bool:
        """
        Cleans up the overlaps and queries from the clash data, ensuring a fresh state for new clash detection runs.
        This is a direct undo operation for the run() method.
        Returns: True if the cleanup was successful, False otherwise.
        """
        r = True
        if self._json_path_name:
            if omni.client.delete(self._json_path_name) == omni.client.Result.OK:
                print(f"Exported file '{self._json_path_name}' deleted.")
            else:
                r = False
        if self._html_path_name:
            if omni.client.delete(self._html_path_name) == omni.client.Result.OK:
                print(f"Exported file '{self._html_path_name}' deleted.")
            else:
                r = False
        if self._new_clash_data_layer_path_name:
            if omni.client.delete(self._new_clash_data_layer_path_name) == omni.client.Result.OK:
                print(f"Created layer '{self._new_clash_data_layer_path_name}' deleted.")
            else:
                r = False
            self._new_clash_data_layer_path_name = ''
        else:
            if not self._clean_overlaps_and_query():
                r = False
        return r
