import os
import re
import tempfile
from urllib.parse import urljoin

import click
import yaml
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
    "output_enconding": "utf-8",
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
        writer_name="html4css1",
        settings_overrides=RST2HTML_SETTINGS,
    )
    with open(index_filename, "rb") as f:
        index = f.read()
    # remove the docutils version from generated html, to avoid
    # useless changes in the readme
    index = re.sub(
        rb"(<meta.*generator.*Docutils)\s*[\d.]+", rb"\1", index, re.MULTILINE
    )
    # remove the http-equiv line
    index = re.sub(
        rb'<meta\s+http-equiv="Content-Type"\s+content="text/html;\s*charset=utf-8"\s*/?>',
        b"",
        index,
        flags=re.MULTILINE | re.IGNORECASE,
    )

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


def generate_fragment(answers, file):
    fragment_lines = file.readlines()
    if not fragment_lines:
        return False

    # Replace relative path by absolute path for figures
    image_path_re = re.compile(r".*\s*\.\..* (figure|image)::\s+(?P<path>.*?)\s*$")
    module_url = (
        "https://raw.githubusercontent.com/"
        f"{answers.get('org_name','quilsoft-org')}/"
        f"{answers.get('repo_name','my-repo')}/"
        f"{answers.get('branch','main')}/"
        f"{answers.get('addon_name','addon')}/"
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


def check_readme_fragments(addon_dir):
    """Verifica si el contenido del readme es válido"""
    print("verificando readme")
    parts_to_check = [
        {
            "section": "CONTRIBUTORS.rst",
            "msg": 'The section %s/readme/%s has no identification please add one i.e. "* Jorge Obiols <jorge.obiols@gmail.com>".',
        },
        {
            "section": "DESCRIPTION.rst",
            "msg": "The section %s/readme/%s has very little content.",
        },
    ]
    errors = []
    module_name = os.path.basename(addon_dir)

    for item in parts_to_check:
        dir = os.path.join(addon_dir + "/readme", item.get("section"))

        try:
            with open(dir, encoding="utf-8") as file:
                content = file.read().strip()
                if len(content) <= 10:
                    errors.append(item["msg"] % (module_name, item["section"]))

        except FileNotFoundError:
            errors.append(f"File {module_name}/readme/{item['section']} does not exist")
        except Exception as e:
            errors.append(
                f"Unknown exception str({e}) reading {module_name}/readme/{item['section']}"
            )

    for error in errors:
        print(error)

    return True if not errors else False


def gen_one_addon_readme(answers, module):
    """Genera el README.rst para el addon addon_name"""
    fragments = {}
    readme_characters = 0
    for fragment_name in FRAGMENTS:
        fragment_filename = os.path.join(module, FRAGMENTS_DIR, fragment_name + ".rst")

        if os.path.exists(fragment_filename):
            # si el fragmento existe lo leemos
            with open(fragment_filename, encoding="utf8") as file:
                fragment = generate_fragment(answers, file)
                # para medir que tan grande es el readme, y poner o no el TOC
                readme_characters += 0 if not fragment else len(fragment)
                if fragment:
                    fragments[fragment_name] = fragment
        else:
            # si el fragmento no existe lo creamos vacio
            with open(fragment_filename, "a") as f:
                pass
    manifest = read_manifest(module)
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
        print("The manifest does not have author, please add Quilsoft as the author.")
        exit(1)

    name = manifest.get("name")
    if not name:
        print("The manifest has no name, please add a proper name")
        exit(1)

    # generate
    template_filename = os.path.join(
        os.path.dirname(__file__), "gen_addon_readme.template"
    )
    readme_filename = os.path.join(module, "README.rst")
    website = manifest.get("website")

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
                    "org_name": answers.get("org_name", "quilsoft-org"),
                    "development_status": development_status,
                    "web": website,
                    "toc": readme_characters > 1000,
                }
            )
        )
        rf.write("\n")
    return readme_filename


@click.command()
@click.argument(
    "files",
    type=click.Path(exists=False),
    nargs=-1,
)
@click.option(
    "--addons",
    type=click.Path(dir_okay=True, file_okay=False, exists=False),
    help="Directory containing several addons, the README will be "
    "generated for all installable addons found there...",
    default=".",
)
def gen_readme(files, addons):
    """main function esta es la entrada"""

    print("Se arranca el gen-readme v1.3.33")

    def get_answers(answ):
        with open(answ) as file:
            return yaml.safe_load(file)

    if not files:
        # Si no fue llamado por pre-commit tomamos los files del path que le paso
        if addons:
            files = os.listdir(addons)
        else:
            print("There are no parameters given")
            exit(1)

    print("archivos a procesar =", files)

    modules = []
    # De esos archivos me quedo con los que son modulos
    for file in files:
        # Leer el archivo de respuetas
        if file == ".copier-answers.yml":
            answers = get_answers(f"{addons}/{file}")

        # Quedarse con los archivos que son modulos
        if module := is_module(addons, file):
            modules.append(module)

    print("addons", addons)
    print("modulos a testear ", modules)
    print("answers ", answers)
    exit(1)

    for module in modules:
        # si no existe el readme (directorio) lo creamos
        if not os.path.exists(os.path.join(module, FRAGMENTS_DIR)):
            os.mkdir(os.path.join(module, FRAGMENTS_DIR))

        # Generamos o Regenamos el readme
        readme_filename = gen_one_addon_readme(answers, module)

        # Verifica que en el readme haya datos validos
        check_readme_fragments(module)

        # Generamos el html
        gen_one_addon_index(readme_filename)
