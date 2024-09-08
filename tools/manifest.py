# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)

import ast
import os

MANIFEST_NAMES = ("__manifest__.py", "__openerp__.py", "__terp__.py")


class NoManifestFound(Exception):
    pass


def get_manifest_path(addons, module):
    for manifest_name in MANIFEST_NAMES:
        manifest_path = f"{addons}/{module}/{manifest_name}"
        if os.path.isfile(manifest_path):
            return manifest_path


def is_module(file):
    """verifica si un archivo pertenece a un modulo, se le pasan todos los archivos
    desde la raiz del repositorio, si el path al archivo es de la forma xxx/__init__.py
    o yyy/__manifest__.py entonces xxx o yyy son modulos.
    Tener en cuenta que se pueden repetir."""

    if "__init__.py" in file or "__manifest__.py" in file:
        return file.split("/")[0]
    else:
        return False


def read_manifest(addons, module):
    manifest_path = get_manifest_path(addons, module)
    if not manifest_path:
        raise NoManifestFound("no Odoo manifest found in {module}")
    with open(manifest_path) as mf:
        manifest = mf.read()
    return ast.literal_eval(manifest)


def find_addons(addons_dir, installable_only=True, this_modules=False):
    """yield (addon_name, addon_dir, manifest)"""
    for addon_name in os.listdir(addons_dir):
        addon_dir = os.path.join(addons_dir, addon_name)
        try:
            manifest = read_manifest(addon_dir)
        except NoManifestFound:
            continue
        if installable_only and not manifest.get("installable", True):
            continue
        yield addon_name, addon_dir, manifest
