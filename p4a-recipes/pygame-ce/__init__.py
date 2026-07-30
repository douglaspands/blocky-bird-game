# Receita local do pygame-ce para python-for-android (R17.1).
#
# A receita oficial ainda NAO foi mergeada no p4a upstream:
# https://github.com/kivy/python-for-android/pull/2971 (aberto desde 2024).
# Este arquivo e uma copia do __init__.py daquele PR, mantida aqui ate o
# merge acontecer (ou ate precisar de ajuste para uma versao mais nova do
# pygame-ce). Ver specs/v2/design.md secao 24.1 para o racional completo.
#
# Ajuste sobre a copia do PR: 'cython' foi adicionado a `depends` abaixo (nao
# estava na versao do PR upstream). Sem isso, `setup.py build_ext` falha com
# "You need cython" — outras receitas do p4a que compilam .pyx (numpy, av)
# declaram esse mesmo depends.
#
# Segundo ajuste: `sdl_image_includes` apontava para a raiz de
# `jni/SDL2_image`, mas a versao do sdl2_image recipe do p4a (2.8.0) move o
# header publico para `jni/SDL2_image/include/SDL_image.h` — layout diferente
# do `SDL2_ttf` (que mantem `SDL_ttf.h` na raiz). Sem o `/include`,
# `src_c/imageext.c` falhava com "'SDL_image.h' file not found".

from os.path import join

from pythonforandroid.recipe import CompiledComponentsPythonRecipe
from pythonforandroid.toolchain import current_directory


class Pygame2Recipe(CompiledComponentsPythonRecipe):
    """
    Recipe to build apps based on SDL2-based pygame.

    .. warning:: Some pygame functionality is still untested, and some
    dependencies like freetype, postmidi and libjpeg are currently
    not part of the build. It's usable, but not complete.
    """

    # Fixado na mesma versao que o desktop usa (pyproject.toml, validado na
    # task 26) para nao ter dois pygame-ce diferentes em voo. Se essa versao
    # nao compilar no p4a (risco descrito no design.md secao 24.1), a saida e
    # fixar aqui a ultima versao conhecida como funcional, mesmo que fique
    # atras do pyproject.toml.
    version = '2.5.7'
    url = 'https://github.com/pygame-community/pygame-ce/archive/{version}.tar.gz'

    site_packages_name = 'pygame-ce'
    name = 'pygame-ce'

    depends = ['sdl2', 'sdl2_image', 'sdl2_mixer', 'sdl2_ttf', 'setuptools', 'jpeg', 'png', 'cython']
    call_hostpython_via_targetpython = False  # Due to setuptools
    install_in_hostpython = False

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        with current_directory(self.get_build_dir(arch.arch)):
            setup_template = open(join("buildconfig", "Setup.Android.SDL2.in")).read()
            env = self.get_recipe_env(arch)
            env['ANDROID_ROOT'] = join(self.ctx.ndk.sysroot, 'usr')

            png = self.get_recipe('png', self.ctx)
            png_lib_dir = join(png.get_build_dir(arch.arch), '.libs')
            png_inc_dir = png.get_build_dir(arch)

            jpeg = self.get_recipe('jpeg', self.ctx)
            jpeg_inc_dir = jpeg_lib_dir = jpeg.get_build_dir(arch.arch)

            sdl_mixer_includes = ""
            sdl2_mixer_recipe = self.get_recipe('sdl2_mixer', self.ctx)
            for include_dir in sdl2_mixer_recipe.get_include_dirs(arch):
                sdl_mixer_includes += f"-I{include_dir} "

            setup_file = setup_template.format(
                sdl_includes=(
                    " -I" + join(self.ctx.bootstrap.build_dir, 'jni', 'SDL', 'include') +
                    " -L" + join(self.ctx.bootstrap.build_dir, "libs", str(arch)) +
                    " -L" + png_lib_dir + " -L" + jpeg_lib_dir + " -L" + arch.ndk_lib_dir_versioned),
                sdl_ttf_includes="-I" + join(self.ctx.bootstrap.build_dir, 'jni', 'SDL2_ttf'),
                sdl_image_includes="-I" + join(self.ctx.bootstrap.build_dir, 'jni', 'SDL2_image', 'include'),
                sdl_mixer_includes=sdl_mixer_includes,
                jpeg_includes="-I" + jpeg_inc_dir,
                png_includes="-I" + png_inc_dir,
                freetype_includes=""
            )
            open("Setup", "w").write(setup_file)

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['USE_SDL2'] = '1'
        env["PYGAME_CROSS_COMPILE"] = "TRUE"
        env["PYGAME_ANDROID"] = "TRUE"
        return env


recipe = Pygame2Recipe()
