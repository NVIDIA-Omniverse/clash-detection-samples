# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import os
import tempfile
import pathlib
import asyncio
import omni.ui as ui

from .clash_detection_processor import ClashDetectionProcessor


class ClashDetectionSamplesWindow(ui.Window):
    WINDOW_NAME = "Clash Detection Samples"

    def __init__(self, test_data_path: str) -> None:
        super().__init__(self.WINDOW_NAME, width=700, height=300, visible=True)

        self._test_data_path = test_data_path
        self._stage_path_name = str(pathlib.Path(self._test_data_path).joinpath("time_sampled.usda"))
        self._temp_dir_path = tempfile.TemporaryDirectory().name

        self.frame.set_build_fn(self.build_window)

    def destroy_window(self):
        self.undock()
        self.visible = False
        super().destroy()

    def _run_clash_processor_on_sample_stage_static(self):
        html_path_name = str(pathlib.Path(self._temp_dir_path).joinpath("static_sample_export.html"))
        json_path_name = str(pathlib.Path(self._temp_dir_path).joinpath("static_sample_export.json"))

        cdp = ClashDetectionProcessor(
            stage_path_name=self._stage_path_name,
            object_a_path="/Root/Xform_Primitives/Cube",
            object_b_path="/Root/Xform_Primitives/Plane",
            logging=False,
            html_path_name=html_path_name,
            json_path_name=json_path_name,
            query_name="Example Static Query",
            comment="A static clash query designed to identify clash between gray block and the ground plane."
        )
        cdp.run()

        if hasattr(os, 'startfile'):
            os.startfile(self._temp_dir_path)

    def _run_clash_processor_on_sample_stage_dynamic(self):
        html_path_name = str(pathlib.Path(self._temp_dir_path).joinpath("dynamic_sample_export.html"))
        json_path_name = str(pathlib.Path(self._temp_dir_path).joinpath("dynamic_sample_export.json"))

        cdp = ClashDetectionProcessor(
            stage_path_name=self._stage_path_name,
            object_a_path="/Root/STATION_TIME_SAMPLED",
            object_b_path="/Root/Xform_Primitives",
            tolerance=5,
            dynamic=True,
            start_time=3,
            end_time=20,
            logging=False,
            html_path_name=html_path_name,
            json_path_name=json_path_name,
            query_name="Example Dynamic Query",
            comment="A dynamic clash query designed to identify instances where the yellow platform's animation collides with the gray block, starting from the 3-second mark and concluding at 20 seconds."
        )
        cdp.run()

        if hasattr(os, "startfile"):
            os.startfile(self._temp_dir_path)

    def _run_clash_processor_on_sample_stage_dups(self):
        html_path_name = str(pathlib.Path(self._temp_dir_path).joinpath("dups_sample_export.html"))
        json_path_name = str(pathlib.Path(self._temp_dir_path).joinpath("dups_sample_export.json"))

        cdp = ClashDetectionProcessor(
            stage_path_name=self._stage_path_name,
            html_path_name=html_path_name,
            json_path_name=json_path_name,
            query_name="Example Search for Duplicates Query",
            comment="A static clash query designed to identify identical meshes with identical transformations fully overlapping each other.",
            search_for_duplicates=True
        )
        cdp.run()

        if hasattr(os, 'startfile'):
            os.startfile(self._temp_dir_path)

    def _open_sample_stage(self):
        async def open_sample_stage():
            import omni.usd
            usd_context = omni.usd.get_context()
            (result, err) = await usd_context.open_stage_async(self._stage_path_name)
        asyncio.ensure_future(open_sample_stage())

    def build_window(self):
        with self.frame:
            with ui.VStack():
                with ui.CollapsableFrame("Available Clash Detection Samples - Observe the console output, as there is no UI in use.", height=0):
                    with ui.VStack():
                        with ui.HStack(height=0):
                            ui.Spacer(width=5)
                            ui.Button("Run", width=100, clicked_fn=self._run_clash_processor_on_sample_stage_dups)
                            ui.Spacer(width=10)
                            ui.Label("Execute Clash Processor configured to create and run a static query on the sample scene to identify identical meshes with identical transformations fully overlapping each other. Export results.")
                        with ui.HStack(height=0):
                            ui.Spacer(width=5)
                            ui.Button("Run", width=100, clicked_fn=self._run_clash_processor_on_sample_stage_static)
                            ui.Spacer(width=10)
                            ui.Label("Execute Clash Processor configured to create and run a static query on the sample scene to identify a clash between gray block and the ground plane. Export results.")
                        with ui.HStack(height=0):
                            ui.Spacer(width=5)
                            ui.Button("Run", width=100, clicked_fn=self._run_clash_processor_on_sample_stage_dynamic)
                            ui.Spacer(width=10)
                            ui.Label("Execute Clash Processor configured to create and run a dynamic query on the sample scene to identify instances where the yellow platform's animation collides with the gray block. Export results.")
                with ui.CollapsableFrame("Available Clash Detection Sample Stages:", height=0):
                    with ui.HStack(height=0):
                        ui.Spacer(width=5)
                        ui.Button("Open", width=100, clicked_fn=self._open_sample_stage)
                        ui.Spacer(width=10)
                        ui.Label("Open the sample dynamic stage in the Omniverse.")
