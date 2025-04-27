from setuptools import setup
from Cython.Build import cythonize
import numpy

setup(
    ext_modules=cythonize("Mask_Module.pyx"),
    include_dirs=[numpy.get_include()]
)

# python setup.py build_ext --inplace