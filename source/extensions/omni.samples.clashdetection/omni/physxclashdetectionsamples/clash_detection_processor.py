# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
from pxr import Usd, UsdUtils
from omni.physxclashdetectioncore.clash_query import ClashQuery
from omni.physxclashdetectioncore.clash_data import ClashData
from omni.physxclashdetectioncore.clash_detect import ClashDetection
from omni.physxclashdetectioncore.clash_data_serializer_sqlite import ClashDataSerializerSqlite
from omni.physxclashdetectioncore.clash_detect_settings import SettingId
from omni.physxclashdetectioncore.clash_detect_export import export_to_html, export_to_json, ExportColumnDef
from omni.physxclashdetectioncore.utils import OptimizedProgressUpdate


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
        html_path_name: str = '',
        json_path_name: str = '',
        query_name: str = '',
        comment: str = '',
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
        html_path_name: str - full path to HTML file if also export to HTML is needed. No clash images will be exported.
        json_path_name: str - full path to JSON file if also export to JSON is needed. No clash images will be exported.
        query_name: str - custom name for the clash detection query which will be generated based on parameters above.
        comment: str - custom comment for the clash detection query which will be generated based on parameters above.
        """
        self._stage_path_name = stage_path_name
        self._html_path_name = html_path_name
        self._json_path_name = json_path_name
        self._query = ClashQuery(
            query_name=query_name,
            object_a_path=object_a_path,
            object_b_path=object_b_path,
            clash_detect_settings={
                SettingId.SETTING_LOGGING.name: logging is True,
                SettingId.SETTING_TOLERANCE.name: float(tolerance),
                SettingId.SETTING_DYNAMIC.name: dynamic,
                SettingId.SETTING_DYNAMIC_START_TIME.name: float(start_time),
                SettingId.SETTING_DYNAMIC_END_TIME.name: float(end_time),
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
            ExportColumnDef(0, 'Clash ID'),
            ExportColumnDef(1, 'Tolerance'),
            ExportColumnDef(2, 'Overlapping Tris', True),
            ExportColumnDef(3, 'Clash Start'),
            ExportColumnDef(4, 'Clash End'),
            ExportColumnDef(5, 'Clashing Frames', True),
            ExportColumnDef(6, 'Object A'),
            ExportColumnDef(7, 'Object B'),
        ]

        overlaps = clash_data.find_all_overlaps_by_query_id(self._query.identifier, False)
        if len(overlaps) != num_overlaps_chk:
            print("Serialization issue detected.")
        rows = [
            [
                o.overlap_id,
                f"{o.tolerance:.3f}",
                str(o.overlap_tris),
                f"{o.start_time:.3f}",
                f"{o.end_time:.3f}",
                str(o.num_records),
                o.object_a_path,
                o.object_b_path
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
        print("Running clash detection engine...")
        progress_update = OptimizedProgressUpdate()
        num_steps = clash_detect.create_pipeline()
        for i in range(num_steps):
            step_data = clash_detect.get_pipeline_step_data(i)
            if step_data.finished:
                break
            clash_detect.run_pipeline_step(i)
            if progress_update.update(step_data.progress):
                print(f"\r{progress_update.progress_value}%", end="")
        print("\rDone!")

        num_overlaps = clash_detect.get_nb_overlaps()
        print(f"Fetching {num_overlaps} overlaps...")
        for p in clash_detect.fetch_and_save_overlaps(stage, clash_data, self._query):
            print(f"\r{p}%", end="")
        print("\rDone!")

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
        if not clash_detect.set_scope(stage, self._query.object_a_path, self._query.object_b_path):
            print("Failed to set clash detection scope.")
            return False
        if not clash_detect.set_settings(self._query.clash_detect_settings, stage):
            print("Failed to set clash detection settings.")
            return False

        num_overlaps = self._detect_overlaps(stage, clash_detect, clash_data)

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
