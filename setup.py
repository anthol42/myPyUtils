from setuptools import setup
import os

if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "No description found"

# Load version
with open("pyutils/__version__.py", "r") as f:
    version = f.read().split("=")[1].strip().strip("\"")

setup(
    name="myPyUtils",
    version=version,
    author="Anthony Lavertu",
    author_email="alavertu2@gmail.com",
    include_package_data=True,
    description="useful utilities for python and datascience",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anthol42/myPyUtils/tree/main",
    project_urls={
        "Issues": "https://github.com/anthol42/myPyUtils/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering :: Artificial Intelligence"
    ],
    keywords=[
        "MyPyUtils", "utils", "utilities", "python", "helpers", "tools", "datascience"
    ],
    python_requires=">=3.9",
    install_requires=[
        "PyYAML>=6.0.0",
    ],
)