import os.path as osp
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ''

    def run_tests(self):
        import shlex
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='latlon-utils',
      version='0.0.4',
      description=('Retrieve WorldClim climate and other information for '
                   'lat-lon grid cells'),
      long_description=readme(),
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
      ],
      keywords='worldclim geo-countries latitude longitude',
      url='https://github.com/Chilipp/latlon-utils',
      author='Philipp Sommer',
      author_email='philipp.sommer@unil.ch',
      license="GPLv3",
      packages=find_packages(exclude=['docs', 'tests*', 'examples']),
      install_requires=[
          'netCDF4',
          'shapely',
          'pandas',
      ],
      package_data={'latlon-utils': [
          osp.join('latlon_utils', 'data', '*'),
          ]},
      include_package_data=True,
      tests_require=['pytest', 'rasterio', 'xarray', 'pytest-cov'],
      cmdclass={'test': PyTest},
      zip_safe=False)
