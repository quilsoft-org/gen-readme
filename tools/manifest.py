# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)

import ast
import os
from pathlib import Path

MANIFEST_NAMES = ("__manifest__.py", "__openerp__.py", "__terp__.py")


class NoManifestFound(Exception):
    pass


def get_manifest_path(addons, module):
    for manifest_name in MANIFEST_NAMES:
        manifest_path = f"{addons}/{module}/{manifest_name}"
        if os.path.isfile(manifest_path):
            return manifest_path


def is_module(filepath, addons="."):
    """Return the Odoo module that owns ``filepath``, relative to ``addons``.

    A module is a directory that directly contains an Odoo manifest. Walk up
    the file's parents until one with a manifest is found, so files at any
    depth (views, readme fragments, data...) map to their module, plain
    Python packages without a manifest are ignored, and nested addon
    directories resolve correctly. Returns ``False`` when the file does not
    belong to any module.

    Paths are normalized with ``os.path.abspath`` instead of ``Path.resolve``
    so that symlinked modules are not skipped.
    """
    addons_root = Path(os.path.abspath(addons))
    path = Path(filepath)
    if not path.is_absolute():
        path = addons_root / path
    try:
        rel = Path(os.path.abspath(path)).relative_to(addons_root)
    except ValueError:
        # file is outside the addons directory: not a module of this tree
        return False

    for parent in rel.parents:
        if parent == Path("."):
            break
        if get_manifest_path(str(addons_root), str(parent)):
            return str(parent)
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
            manifest = read_manifest(addons_dir, addon_name)
        except NoManifestFound:
            continue
        if installable_only and not manifest.get("installable", True):
            continue
        yield addon_name, addon_dir, manifest
