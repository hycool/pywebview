from setuptools import setup, find_packages

setup(
    name='qt_cef',
    version='0.0.1',
    license='MIT',
    author='Burgeon Software',
    url='https://github.com/hycool/pywebview',
    author_email='huai.y@burgeon.cn',
    description='A tool kit which make creating desktop application simple',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=['PyQt5==5.11.2', 'cefpython3==57.1', 'gpu-info==2.0.1'],
)
