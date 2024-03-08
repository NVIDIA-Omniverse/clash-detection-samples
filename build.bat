@echo off
setlocal enabledelayedexpansion

pushd %~dp0

:: build repo
call "repo.bat" build %*
