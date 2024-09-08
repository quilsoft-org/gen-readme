import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urljoin

import click
from docutils.core import publish_file
from jinja2 import Template

from .manifest import is_module, read_manifest

FRAGMENTS_DIR = "readme"

FRAGMENTS = (
    "DESCRIPTION",
    "INSTALL",
    "CONFIGURE",
    "USAGE",
    "ROADMAP",
    "DEVELOP",
    "CONTRIBUTORS",
    "CREDITS",
    "HISTORY",
)

DEVELOPMENT_STATUS_BADGES = {
    "mature": (
        "https://img.shields.io/badge/maturity-Mature-brightgreen.png",
        "https://odoo-community.org/page/development-status",
        "Mature",
    ),
    "production/stable": (
        "https://img.shields.io/badge/maturity-Production%2FStable-green.png",
        "https://odoo-community.org/page/development-status",
        "Production/Stable",
    ),
    "beta": (
        "https://img.shields.io/badge/maturity-Beta-yellow.png",
        "https://odoo-community.org/page/development-status",
        "Beta",
    ),
    "alpha": (
        "https://img.shields.io/badge/maturity-Alpha-red.png",
        "https://odoo-community.org/page/development-status",
        "Alpha",
    ),
}

LICENSE_BADGES = {
    "AGPL-3": (
        "https://img.shields.io/badge/licence-AGPL--3-blue.png",
        "http://www.gnu.org/licenses/agpl-3.0-standalone.html",
        "License: AGPL-3",
    ),
    "LGPL-3": (
        "https://img.shields.io/badge/licence-LGPL--3-blue.png",
        "http://www.gnu.org/licenses/lgpl-3.0-standalone.html",
        "License: LGPL-3",
    ),
    "GPL-3": (
        "https://img.shields.io/badge/licence-GPL--3-blue.png",
        "http://www.gnu.org/licenses/gpl-3.0-standalone.html",
        "License: GPL-3",
    ),
    "OPL-1": (
        "https://img.shields.io/badge/licence-OPL--1-blue.png",
        "https://www.tldrlegal.com/license/open-public-license-v1-0-opl-1-0",
        "License: OPL-1",
    ),
    "OEEL-1": (
        "https://img.shields.io/badge/licence-OEEL--1-blue.png",
        "https://www.tldrlegal.com/license/open-public-license-v1-0-opl-1-0",
        "License: OPL-1",
    ),
}

PRE_COMMIT_BADGES = {
    "pre-commmit": (
        "https://img.shields.io/badge/pre_commit-passed-green",
        "https://pre-commit.com/",
        "Pre-Commit",
    ),
}
errors = []

# this comes from pypa/readme_renderer
RST2HTML_SETTINGS = {
    # Prevent local files from being included into the rendered output.
    # This is a security concern because people can insert files
    # that are part of the system, such as /etc/passwd.
    "file_insertion_enabled": False,
    # Halt rendering and throw an exception if there was any errors or
    # warnings from docutils.
    "halt_level": 2,
    # Output math blocks as LaTeX that can be interpreted by MathJax for
    # a prettier display of Math formulas.
    "math_output": "MathJax",
    # Disable raw html as enabling it is a security risk, we do not want
    # people to be able to include any old HTML in the final output.
    "raw_enabled": False,
    # Use typographic quotes, and transform --, ---, and ... into their
    # typographic counterparts.
    "smart_quotes": True,
    # Use the short form of syntax highlighting so that the generated
    # Pygments CSS can be used to style the output.
    "syntax_highlight": "short",
    "output_encoding": "utf-8",
    "xml_declaration": False,
}


def gen_one_addon_index(readme_filename):
    """Genera el readme en html"""
    addon_dir = os.path.dirname(readme_filename)
    index_dir = os.path.join(addon_dir, "static", "description")
    index_filename = os.path.join(index_dir, "index.html")
    if os.path.exists(index_filename):
        with open(index_filename) as f:
            if "gen-readme" not in f.read():
                # index was created manually
                return
    if not os.path.isdir(index_dir):
        os.makedirs(index_dir)
    publish_file(
        source_path=readme_filename,
        destination_path=index_filename,
        writer_name="html5",
        settings_overrides=RST2HTML_SETTINGS,
    )
    with open(index_filename, "rb") as f:
        index = f.read()
    # remove the docutils version from generated html, to avoid
    # useless changes in the readme
    index = re.sub(
        rb"(<meta.*generator.*Docutils)\s*[\d.]+", rb"\1", index, re.MULTILINE
    )
    # # remove the http-equiv line
    # index = re.sub(
    #     rb'<meta\s+http-equiv="Content-Type"\s+content="text/html;\s*charset=utf-8"\s*/?>',
    #     b"",
    #     index,
    #     flags=re.MULTILINE | re.IGNORECASE,
    # )

    with open(index_filename, "wb") as f:
        f.write(index)
    return index_filename


def check_rst(readme_filename):
    with tempfile.NamedTemporaryFile() as f:
        publish_file(
            source_path=readme_filename,
            destination=f,
            writer_name="html4css1",
            settings_overrides=RST2HTML_SETTINGS,
        )


def generate_fragment(kwargs, file, module):
    fragment_lines = file.readlines()
    if not fragment_lines:
        return False

    # Replace relative path by absolute path for figures
    image_path_re = re.compile(r".*\s*\.\..* (figure|image)::\s+(?P<path>.*?)\s*$")
    module_url = (
        "https://raw.githubusercontent.com/"
        f"{kwargs.get('org_name','quilsoft-org')}/"
        f"{kwargs.get('repo_name','my-repo')}/"
        f"{kwargs.get('branch','main')}/"
        f"{module}/"
    )
    for index, fragment_line in enumerate(fragment_lines):
        mo = image_path_re.match(fragment_line)
        if not mo:
            continue
        path = mo.group("path")

        if path.startswith("http"):
            # It is already an absolute path
            continue
        else:
            # remove '../' if exists that make the fragment working
            # on github interface, in the 'readme' subfolder
            relative_path = path.replace("../", "")
            fragment_lines[index] = fragment_line.replace(
                path, urljoin(module_url, relative_path)
            )
    fragment = "".join(fragment_lines)

    # ensure that there is a new empty line at the end of the fragment
    if fragment[-1] != "\n":
        fragment += "\n"
    return fragment


def check_contributors(addons, module):
    dir = f"{addons}/{module}/readme/CONTRIBUTORS.rst"
    pattern = r"^\*\s+[a-zA-Z\s]+\s<[\w\.-]+@[\w\.-]+>$"
    with open(dir, encoding="utf-8") as file:
        content = file.readlines()

        for line in content:
            if re.match(pattern, line.strip()):
                return True
    return False


def check_description(kwargs, module):
    addons = kwargs.get("addons")
    dir = f"{addons}/{module}/readme/DESCRIPTION.rst"
    with open(dir, encoding="utf-8") as file:
        content = file.read()
    words = len(content.split())
    return words >= kwargs.get("min_description_words")


def check_readme_fragments(kwargs, module):
    """Verifica si el contenido del readme es válido"""
    addons = kwargs.get("addons")
    # Chequear que tenga el contributores
    if not check_contributors(addons, module):
        errors.append(
            "The section {module_name}/readme/CONTRIBUTORS.rst has no "
            "identification please add one i.e. "
            "'* Jorge Obiols <jorge.obiols@gmail.com>'."
        )

    # Chequear que haya una descripción razonable
    if not check_description(kwargs, module):
        errors.append(
            f"Please write a good description for the {module} module in the "
            f"section {module}/readme/DESCRIPTION.rst\n"
            f"The description must have at least "
            f"{kwargs.get('min_description_words')} words to be acceptable."
        )


def gen_rst_readme(kwargs, module):
    """Genera el README.rst"""
    addons = kwargs.get("addons")
    fragments = {}
    readme_characters = 0
    for fragment_name in FRAGMENTS:
        fragment_filename = f"{addons}/{module}/{FRAGMENTS_DIR}/{fragment_name}.rst"

        if os.path.exists(fragment_filename):
            # si el fragmento existe lo leemos
            with open(fragment_filename, encoding="utf8") as file:
                fragment = generate_fragment(kwargs, file, module)
                # para medir que tan grande es el readme, y poner o no el TOC
                readme_characters += 0 if not fragment else len(fragment)
                if fragment:
                    fragments[fragment_name] = fragment
        else:
            # si el fragmento no existe lo creamos vacio
            with open(fragment_filename, "a") as f:
                pass

    manifest = read_manifest(addons, module)
    badges = []
    badges.append(PRE_COMMIT_BADGES["pre-commmit"])

    development_status = manifest.get("development_status", "Beta").lower()
    if development_status in DEVELOPMENT_STATUS_BADGES:
        badges.append(DEVELOPMENT_STATUS_BADGES[development_status])

    license = manifest.get("license", "AGPL-3")

    if license in LICENSE_BADGES:
        badges.append(LICENSE_BADGES[license])

    author = manifest.get("author")
    if not author or author != "Quilsoft":
        errors.append(
            f"The manifest of module {module} does not have author, please add "
            "Quilsoft as the author."
        )

    name = manifest.get("name")
    if not name:
        errors.append(
            f"The manifest of module {module} has no name, please add a proper name."
        )

    # generate
    template_filename = f"{os.path.dirname(__file__)}/gen_addon_readme.template"
    readme_filename = f"{addons}/{module}/README.rst"

    with open(template_filename, encoding="utf8") as tf:
        template = Template(tf.read())

    # Abrimos el template y le escribimos las variables.
    with open(readme_filename, "w", encoding="utf8") as rf:
        rf.write(
            template.render(
                {
                    "addon_name": name,
                    "author": author,
                    "badges": badges,
                    "fragments": fragments,
                    "manifest": manifest,
                    "org_name": kwargs.get("org_name"),
                    "development_status": development_status,
                    "web": kwargs.get("website"),
                    "toc": readme_characters > 1000,
                }
            )
        )
        rf.write("\n")
    return readme_filename


def check_icon(kwargs, module):
    addons = kwargs.get("addons")
    if not os.path.exists(f"{addons}/{module}/static/description/icon.png"):
        errors.append(
            "The module {module} has no icon\n"
            "Please provide an icon.png file in the "
            "{module}/static/description/icon.png path"
        )


@click.command()
@click.argument(
    "files",
    type=click.Path(exists=False),
    nargs=-1,
)
@click.option(
    "--addons",
    type=click.Path(
        dir_okay=True,
        file_okay=False,
        exists=False,
    ),
    help="Directory containing several addons, the README will be "
    "generated for all installable addons found there...",
    default=".",
)
@click.option(
    "--min-description-words",
    type=click.INT,
    help="Minimum number of words that the DESCRIPTION section must contain. Default: 40",
    default=40,
)
@click.option(
    "--website",
    type=click.STRING,
    help="Partner website; the logo at the end of the README is taken from this website",
    default="https://quilsoft.com",
)
@click.option(
    "--org-name",
    type=click.STRING,
    help="Github Organization from the partner. Default: quilsoft-org",
    default="quilsoft-org",
)
def gen_readme(files, **kwargs):
    """main function for gen_readme"""
    addons = kwargs.get("addons")
    if not files:
        # Si no fue llamado por pre-commit tomamos los files del path que le paso
        if addons:
            files = {
                str(file.relative_to(Path(addons)))
                for file in Path(addons).rglob("*")
                if file.is_file()
            }
        else:
            print("There are no parameters given")
            exit(1)

    modules = set()
    # De esos archivos me quedo con los que son modulos
    for file in files:

        # Filtrar los directorios que son modulos
        module = is_module(file)
        if module:
            modules.add(module)

    for module in modules:
        # si no existe el readme (directorio) lo creamos
        if not os.path.exists(f"{addons}/{module}/{FRAGMENTS_DIR}"):
            os.mkdir(f"{addons}/{module}/{FRAGMENTS_DIR}")

        # Generamos o Regenamos el README.rst
        readme_filename = gen_rst_readme(kwargs, module)

        # Verifica que en el readme haya datos validos
        check_readme_fragments(kwargs, module)

        # Verifica que tenga un icono
        check_icon(kwargs, module)

        # Si tengo errores reporto y termino
        if errors:
            for error in errors:
                print(error)
            exit(1)

        # Generamos el html
        gen_one_addon_index(readme_filename)
