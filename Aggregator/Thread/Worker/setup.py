from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("Unmask_Module.pyx")
)

# python setup.py build_ext --inplace