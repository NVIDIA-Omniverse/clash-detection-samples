# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import asyncio
import pathlib
import carb
import carb.settings
import omni.ext
import omni.kit
import omni.kit.ui
import omni.ui as ui
from omni.physxclashdetectionuicommon.windowmenuitem import MenuItem
from .clash_detection_sample_window import ClashDetectionSamplesWindow
from omni.kit.widget.prompt import Prompt


class ClashDetectionSamplesExtension(omni.ext.IExt):
    MENU_ITEM_NAME = "Clash Detection Samples"
    SETTING_CLASH_DETECTION_SAMPLES_WINDOW = "/physics/clashDetectionSamples/showSamplesWindow"
    OMNIVERSE_EULA_ACCEPTED = "persistent/physics/clashDetectionSamples/omniEulaAccepted"

    def __init__(self):
        super().__init__()
        self._menu = None
        self._settings_subs = None
        self._settings = None
        self._clash_samples_window = None

    def on_startup(self, ext_id):
        self._ext_path = omni.kit.app.get_app().get_extension_manager().get_extension_path(ext_id)
        self._test_data_path = str(pathlib.Path(self._ext_path).joinpath("testdata"))
        self._settings = carb.settings.get_settings()
        self._settings_subs = (
            omni.kit.app.SettingChangeSubscription(
                self.SETTING_CLASH_DETECTION_SAMPLES_WINDOW,
                self._show_clash_samples_window_setting_changed
            ),
        )

        def main_menu_click():
            val = carb.settings.get_settings().get_as_bool(self.SETTING_CLASH_DETECTION_SAMPLES_WINDOW)
            carb.settings.get_settings().set_bool(self.SETTING_CLASH_DETECTION_SAMPLES_WINDOW, not val)

        self._menu = MenuItem(
            f"Physics/{self.MENU_ITEM_NAME}",
            "Window",
            main_menu_click,
            lambda: self._clash_samples_window.visible if self._clash_samples_window else False
        )

        ui.Workspace.set_show_window_fn(ClashDetectionSamplesWindow.WINDOW_NAME, self.show_window)

        async def sync_clash_samples_window_state_async():
            for _ in range(2):
                await omni.kit.app.get_app().next_update_async()
            if self._settings.get_as_bool(self.SETTING_CLASH_DETECTION_SAMPLES_WINDOW):
                self._settings.set_bool(self.SETTING_CLASH_DETECTION_SAMPLES_WINDOW, True)
        asyncio.ensure_future(sync_clash_samples_window_state_async())

        async def show_eula_acceptance_window_async():
            for _ in range(5):
                await omni.kit.app.get_app().next_update_async()
            self._show_eula()
        asyncio.ensure_future(show_eula_acceptance_window_async())

    def _show_eula(self):
        """ EULA acceptance """
        if not self._settings.get_as_bool(self.OMNIVERSE_EULA_ACCEPTED):
            eula_url = "https://docs.omniverse.nvidia.com/install-guide/latest/common/NVIDIA_Omniverse_License_Agreement.html"
            Prompt(
                "End User License Agreement",
                ("By using the software and materials provided, you agree to the terms of use:\n\n"
                 f"{eula_url}\n\n"
                 "Do you accept the EULA (End User License Agreement)?"),
                ok_button_text="Yes",
                cancel_button_text="No",
                ok_button_fn=lambda: self._settings.set_bool(self.OMNIVERSE_EULA_ACCEPTED, True),
                cancel_button_fn=omni.kit.app.get_app().post_quit,
                on_closed_fn=omni.kit.app.get_app().post_quit,
                modal=True,
                width=720,
                callback_addons=[
                    lambda: omni.ui.Button(
                        "Copy EULA URL to Clipboard",
                        width=712,
                        clicked_fn=lambda: omni.kit.clipboard.copy(eula_url)
                    )
                ],
            ).show()

    def _show_clash_samples_window_setting_changed(self, item, event_type):
        if event_type == carb.settings.ChangeEventType.CHANGED:
            enabled = self._settings.get_as_bool(self.SETTING_CLASH_DETECTION_SAMPLES_WINDOW)
            if not enabled:
                if self._clash_samples_window:
                    self._clash_samples_window.destroy()
                    self._clash_samples_window = None
            else:
                self.create_window()

    def show_window(self, show: bool):
        if show:
            self.create_window()
        elif self._clash_samples_window:
            self._clash_samples_window.visible = False

    def create_window(self):
        if self._clash_samples_window is None:
            self._clash_samples_window = ClashDetectionSamplesWindow(self._test_data_path)
        # self._clash_samples_window.build_window()
        if self._clash_samples_window:
            self._clash_samples_window.set_visibility_changed_fn(self._window_visibility_changed_fn)
            self._clash_samples_window.deferred_dock_in("Content", ui.DockPolicy.CURRENT_WINDOW_IS_ACTIVE)

    def _window_visibility_changed_fn(self, visible):
        # handle the case when user closes the window by the top right cross
        if not visible:
            window_enabled = self._settings.get_as_bool(self.SETTING_CLASH_DETECTION_SAMPLES_WINDOW)
            if window_enabled:
                self._settings.set_bool(self.SETTING_CLASH_DETECTION_SAMPLES_WINDOW, False)
        if self._menu:
            self._menu.refresh()

    def on_shutdown(self):
        ui.Workspace.set_show_window_fn(ClashDetectionSamplesWindow.WINDOW_NAME, None)
        self._settings.set_bool(self.SETTING_CLASH_DETECTION_SAMPLES_WINDOW, False)
        if self._menu:
            self._menu.remove()
            self._menu = None
        if self._clash_samples_window is not None:
            self._clash_samples_window.destroy()
            self._clash_samples_window = None
        self._settings_subs = None
        self._settings = None
