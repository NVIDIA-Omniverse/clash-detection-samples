# Clash Detection Samples

This repository contains Python based clash detection samples.

It leverages NVIDIA Omniverse Kit and the Clash Detection SDK, which get downloaded upon building the project.

# Prerequisites and Environment Setup

To kickstart your development journey, your system should adhere to the following specifications:

- **Operating System**: Windows 10/11 or Linux (Ubuntu 20.04/22.04 recommended)
- **GPU**: NVIDIA RTX capable GPU (Turing or newer recommended)
- **Driver**: Latest NVIDIA driver compatible with your GPU
- **Internet Access**: Required for downloading the Omniverse Kit SDK, extensions, and tools.
- **Software Dependencies**:
  - Required : Git
  - Recommended : Docker
  - Recommended : VSCode (or your preferred IDE)

# Repository Structure

| Directory Item    | Purpose                                                         |
| ----------------- | --------------------------------------------------------------- |
| deps/             | Project dependencies.                                           |
| PACKAGE-LICENSES/ | Additional licensing information for package dependencies.      |
| source/           | Source code.                                                    |
| tools/            | Tooling settings and repository specific tools.                 |
| .gitignore        | Git configuration.                                              |
| CONTRIBUTING.md   | Guidelines and instructions for potential contributors.         |
| LICENSE           | License for the repo.                                           |
| README.md         | Project information.                                            |
| SECURITY.md       | Security policies and procedures for the project.               |
| VERSION.md        | Project version.                                                |
| build.bat         | Windows script which instructs repo tools to build the project. |
| build.sh          | Linux script which instructs repo tools to build the project.   |
| prebuild.toml     | Pre-build configuration of repo tools.                          |
| repo.bat          | Windows repo tool entry point.                                  |
| repo.sh           | Linux repo tool entry point.                                    |
| repo.toml         | Top level configuration of repo tools.                          |

# How to Clone the Repository

Cloning a GitHub repository to your local disk is a straightforward process that allows you to work on projects and keep track of changes. Below is a step-by-step guide on how to clone a GitHub repository, applicable to any operating system (Windows, Linux, macOS) that supports Git.

Before you begin, ensure you have the following:
Git Installed: If Git is not already installed on your system, you can download and install it from [Git's official site](https://git-scm.com/downloads).

1. Open your terminal or command prompt.
1. If this is your first time using Git, you need to configure your user name and email.
   ```
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```
1. Navigate to the directory where you want to clone the repository.
1. Clone the repository.
   ```
   git clone https://github.com/NVIDIA-Omniverse/clash-detection-samples.git
   ```
   Once the cloning process is complete, you should see a new directory with the same name as the repository in your specified location.
1. [Optional] To ensure everything is set up correctly, you can check the status of your repository:
   ```
   git status
   ```

# How to Build

- Click [here](source/extensions/omni.samples.clashdetection/docs/README.md) for more information about provided sample code and how to build.
- Click [here](https://docs.omniverse.nvidia.com/extensions/latest/ext_clash-detection/clash-detection-core.html) to access online Clash Detection Core Python Developer Documentation from the SDK.

# Clash Detection SDK Documentation

We strongly recommend you to watch the [Getting Started video](https://docs.omniverse.nvidia.com/extensions/latest/ext_clash-detection.html#clashdetection) before working with Clash Detection.

Explore documentation and video tutorial for the Clash Detection SDK online:

- [Clash Detection SDK Changelog](https://docs.omniverse.nvidia.com/extensions/latest/ext_clash-detection/clash-detection-changelog.html)
- [Introduction, Video Tutorial & Installation](https://docs.omniverse.nvidia.com/extensions/latest/ext_clash-detection.html#clashdetection)
- [How to Work with the UI](https://docs.omniverse.nvidia.com/extensions/latest/ext_clash-detection/clash-detection-ui.html)
- [How to Work with the Clash Detection Viewport API](https://docs.omniverse.nvidia.com/extensions/latest/ext_clash-detection/clash-detection-viewport.html)
- [How to Work with the Clash Detection Bake API](https://docs.omniverse.nvidia.com/extensions/latest/ext_clash-detection/clash-detection-bake.html)
- [Clash Detection Core Python Developer Documentation](https://docs.omniverse.nvidia.com/extensions/latest/ext_clash-detection/clash-detection-core.html)

This documentation is also available locally, as a part of the Clash Detection SDK, in `docs\index.html`.

Once this project is built, you can access the documentation via [\_build\target-deps\clash_detection_sdk\docs\index.html](_build\target-deps\clash_detection_sdk\docs\index.html)

# Additional Resources

- [Omniverse Kit SDK Manual](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/index.html)

# License

Development using the Omniverse Kit SDK is subject to the licensing terms detailed [here](https://docs.omniverse.nvidia.com/dev-guide/latest/common/NVIDIA_Omniverse_License_Agreement.html).

# Data Collection & Use

## Overview

NVIDIA Omniverse Kit Clash Detection Samples collects anonymous usage data to help improve software performance and aid in diagnostic purposes.

Rest assured, no personal information such as user email, name or any other PII field is collected.

## Purpose

Omniverse Kit Samples starts collecting data when you begin interaction with our provided software.

It includes:

1. Installation and configuration details such as version of operating system, applications installed : Allows us to recognize usage trends & patterns
1. Hardware Details such as CPU, GPU, monitor information : Allows us to optimize settings in order to provide best performance
1. Product session and feature usage : Allows us to understand user journey and product interaction to further enhance workflows

Error and crash logs : Allows us to improve performance & stability for troubleshooting and diagnostic purposes of our software

## Instructions to turn-off telemetry

If you wish to opt-out of physx and/or clashdetection only telemetry data collection, set the following persistent settings to `false` in the .kit app file (persistent settings are retained so deleting them is not enough)

```
[settings]
telemetry.enableAnonymousData = false
```

This setting can also be overridden by defining and setting the `OMNI_TELEMETRY_DISABLE_ANONYMOUS_DATA` environment variable to '1' for the kit process. The docs around it can be found [here](http://omniverse-docs.s3-website-us-east-1.amazonaws.com/carbonite/170.0-pre/docs/structuredlog/OmniTelemetry.html#anonymous-data-mode). This env. var is intended to be used when launching a container whose app enables the `/telemetry/enableAnonymousData` setting in its config files. It's the suggested way to opt out of anonymous telemetry for a containerized app.

# Contributing

We provide this project as-is and are currently not accepting outside contributions.
