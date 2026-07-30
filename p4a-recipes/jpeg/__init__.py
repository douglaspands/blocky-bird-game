# Receita local do jpeg para python-for-android — override do CMakeLists.txt
# antigo do libjpeg-turbo 2.0.1 (bundled pelo p4a v2024.01.21), que declara
# `cmake_minimum_required` abaixo de 3.5. O CMake do container
# kivy/buildozer e o 4.2.3, que removeu suporte a projetos < 3.5
# ("Compatibility with CMake < 3.5 has been removed from CMake"). A saida
# documentada pelo proprio erro do CMake e `-DCMAKE_POLICY_VERSION_MINIMUM=3.5`.
#
# Setar essa variavel via `docker run -e` NAO funciona: `Recipe.get_recipe_env()`
# (`Arch.get_env()` em pythonforandroid/archs.py) monta o dict de ambiente do
# zero — nao copia `os.environ` — entao qualquer env var do host/container e
# invisivel para o `sh.cmake(..., _env=env)` deste recipe. A flag precisa ir
# como argumento de linha de comando do cmake, daqui a copia local do recipe
# original (pythonforandroid/recipes/jpeg/__init__.py) com essa adicao.
#
# Tambem trocado `rm -f` por `rm -rf`: apos uma tentativa de build que falha
# no meio do `cmake configure`, `CMakeFiles/` fica como diretorio parcial no
# build dir, e `rm -f` (sem `-r`) nao remove diretorios — trava retries com
# "cannot remove 'CMakeFiles/': Is a directory".
# Ver specs/v2/design.md secao 24.1.

from os.path import join
from typing import ClassVar

import sh
from pythonforandroid.logger import shprint
from pythonforandroid.recipe import Recipe
from pythonforandroid.util import current_directory


class JpegRecipe(Recipe):
    name = "jpeg"
    version = "2.0.1"
    url = "https://github.com/libjpeg-turbo/libjpeg-turbo/archive/{version}.tar.gz"
    built_libraries: ClassVar[dict[str, str]] = {"libjpeg.a": ".", "libturbojpeg.a": "."}

    def build_arch(self, arch):
        build_dir = self.get_build_dir(arch.arch)

        with current_directory(build_dir):
            env = self.get_recipe_env(arch)
            toolchain_file = join(self.ctx.ndk_dir, "build/cmake/android.toolchain.cmake")

            shprint(sh.rm, "-rf", "CMakeCache.txt", "CMakeFiles/")
            shprint(
                sh.cmake,
                "-G",
                "Unix Makefiles",
                "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
                "-DCMAKE_SYSTEM_NAME=Android",
                "-DCMAKE_POSITION_INDEPENDENT_CODE=1",
                f"-DCMAKE_ANDROID_ARCH_ABI={arch.arch}",
                "-DCMAKE_ANDROID_NDK=" + self.ctx.ndk_dir,
                f"-DCMAKE_C_COMPILER={arch.get_clang_exe()}",
                f"-DCMAKE_CXX_COMPILER={arch.get_clang_exe(plus_plus=True)}",
                "-DCMAKE_BUILD_TYPE=Release",
                "-DCMAKE_INSTALL_PREFIX=./install",
                "-DCMAKE_TOOLCHAIN_FILE=" + toolchain_file,
                f"-DANDROID_ABI={arch.arch}",
                "-DANDROID_ARM_NEON=ON",
                "-DENABLE_NEON=ON",
                # Force disable shared, with the static ones is enough
                "-DENABLE_SHARED=0",
                "-DENABLE_STATIC=1",
                _env=env,
            )
            shprint(sh.make, _env=env)


recipe = JpegRecipe()
