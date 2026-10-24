import setuptools

from tools.__init__ import __version__

with open("README.md") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gen-odoo-readme",
    version=__version__,
    author="Jorge E. Obiols",
    description="Tool to create README.rst files for Odoo",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/quilsoft-org/gen-readme",
    author_email="jorge.obiols@gmail.com",
    license="AGPL-3.0",
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "gen-readme=tools.gen_readme:gen_readme",
        ],
    },
    include_package_data=True,
    package_data={"tools": ["*.template"]},
    install_requires=[
        "click==8.2.1",
        "jinja2>=3.1.6",
        "docutils==0.21.2",
        "Pygments==2.19.2",
    ],
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Documentation",
    ],
    keywords="odoo documentation readme rst",
)
