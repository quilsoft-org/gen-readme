
README GENERATOR AND VALIDATOR FOR ODOO
=======================================

This plugin is based on oca-gen-addon-readme from the repository [OCA/maintainer-tools.git](https://github.com/OCA/maintainer-tools). The original version is licensed under AGPL-3.

You can find the terms of the license in the LICENSE file available in this repository.

This small utility generates high-quality README.rst files along with a web page, which is displayed when reviewing the module's information. The webpage is located in the static/index.html directory.

The README generation starts by creating a readme directory in the module, containing a number of .rst files called *Fractions* where the developer can describe the module's functionalities in detail.


    tony_stark_module
    ├── views
    ├── readme
    |   ├── CONFIGURE.rst
    |   ├── CONTRIBUTORS.rst
    |   ├── CREDITS.rst
    |   ├── DESCRIPTION.rst
    |   ├── HISTORY.rst
    |   ├── INSTALL.rst
    |   ├── READMAP.rst
    |   └── USAGE.rst
    ├── reports
    ├── static
    └── views

What gen_readme does:
---------------------

1. If the readme directory does not exist in the module, gen-readme will create the directory in situ, with all the fragments plus an empty README.
1. Make sure that the CONTRIBUTORS.rst section includes the developer(s) who created or modified the module, as there may be multiple authors.
1. Ensure that the word count in the DESCRIPTION section is at a reasonable level. This can be adjusted using a parameter.
1. Check that the module's manifest contains the author key, which usually refers to the intellectual property owner, typically the partner.
1. Additionally, at the request of Raiver Figueroa, ensure that the module has an icon.

pre-commit hook
---------------

You can use this module as a pre-commit plugin this way

    - repo: https://github.com/quilsoft-org/gen-readme.git
        rev: 1.3.45
        hooks:
        - id: gen-readme
          args:
            - --min-description-words 20
            - --website https://quilsoft.com
            - --org_name quilsoft-org
            - --author Quilsoft

Local Installation
------------------

You can install the plugin locally and run it against a set of modules. To do this, you need to install it with:

    sudo pipx install gen-odoo-readme

See proyect details in [pypi.org/gen-odoo/readme](https://pypi.org/project/gen-odoo-readme/)

Use the gen-readme --help command for detailed usage instructions:

    Usage: gen-readme [OPTIONS] [FILES]...

    main function for gen_readme

    Options:
    --addons DIRECTORY              Directory containing several addons, the
                                    README will be generated for all installable
                                    addons found there...
    --min-description-words INTEGER
                                    Minimum number of words that the DESCRIPTION
                                    section must contain./n Default 40
    --website TEXT                  Partner website; the logo at the end of the
                                    README is taken from this website
    --org-name TEXT                 Github Organization from the
                                    partner./nDefault quilsoft-org
    --help                          Show this message and exit

When working locally, you must provide the --addons-dir DIRECTORY option to make it work
