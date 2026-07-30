[app]
title = Blocky Bird
package.name = blockybird
package.domain = com.douglaspands

source.dir = .
source.include_exts = py,png
source.exclude_dirs = tests,specs,.venv,dist,build,.git,.github,__pycache__,p4a-recipes,android,scripts,.pytest_cache

version = 0.2.0
requirements = python3,pygame-ce,android

orientation = all
fullscreen = 1

# receita local do pygame-ce: a oficial nao esta mergeada no p4a upstream
# (ver p4a-recipes/pygame-ce/__init__.py e design.md secao 24.1)
p4a.local_recipes = ./p4a-recipes
p4a.bootstrap = sdl2

# FIXADO em v2024.01.21 (hostpython3 3.11.5): o p4a master/release mais recente
# (>= commit e1bd2497, "Update to Python 3.14, remove distutils") builda o
# hostpython3 usado para rodar os setup.py dos recipes como Python 3.14 — e o
# setup.py do pygame-ce (em toda versao, checado ate a 2.5.7) ainda chama
# `distutils.ccompiler.spawn(...)` como funcao de modulo, removida da
# reestruturacao do setuptools._distutils no Python 3.12+. Falha real
# reproduzida: "AttributeError: module 'distutils.ccompiler' has no attribute
# 'spawn'". v2024.01.21 e a ultima release antes dessa mudanca. Ver
# specs/v2/design.md secao 24.1 para o relato completo desta investigacao.
p4a.branch = v2024.01.21

# Android TV: sem tela de toque obrigatoria + categoria leanback launcher (R17.3)
android.extra_manifest_xml = ./android/tv_extra_manifest.xml
android.manifest.intent_filters = ./android/tv_intent_filter.xml
android.extra_manifest_application_arguments = android:banner="@drawable/banner"
android.add_resources = assets/android_banner.png:drawable/banner.png

android.api = 34
android.minapi = 21
android.ndk_api = 21
android.archs = armeabi-v7a, arm64-v8a, x86_64
android.allow_backup = True

[buildozer]
log_level = 2
