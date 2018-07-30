import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="qt5_cef",
    version="0.0.2",
    author="hy",
    author_email="hycool.happy@163.com",
    description="A simple tool kit for create desktop application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hycool/pywebview",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    install_requires=['PyQt5==5.11.2', 'cefpython3==57.1']
)
