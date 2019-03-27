Retrieve WorldClim climate and other information for lat-lon grid cells
=======================================================================

|travis| |codecov| |version| |github| |supported-versions| |supported-implementations|

This repository contains utility functions to retrieve information for given
latitudes and longitude.

Installation
------------
We strongly recommend to use conda_ for the installation. First, install the
necessary dependencies, namely netCDF4_, shapely_ and pandas_::

    conda install netcdf4 shapely pandas

To enable the download of the WorldClim data, you will also need rasterio_ and
xarray_ (you can skip this if you already downloaded the data) via::

    conda install rasterio xarray

Then install ``latlon_utils`` via::

    pip install latlon_utils

or from the source directory via::

    pip install .

Usage
-----
So far, the package has two functions: the `get_climate` and `get_country`
function. Use these like

Get the country for 50 degrees north and 10 degrees east::

    >>> from latlon_utils import get_country

    >>> get_country(50, 10)
    'Germany'

Get the climate for 50 degrees north and 10 degrees east::

    >>> from latlon_utils import get_climate

    # limit the number of columns printed by pandas
    >>> import pandas; pandas.options.display.max_columns = 5

    >>> get_climate(50, 10)
    tavg  jan     0.044739
          feb     0.974976
          mar     4.705505
          apr     8.232239
          mai    13.150024
          jun    16.012268
          jul    17.958984
          aug    17.828735
          sep    13.779480
          oct     8.787476
          nov     4.039001
          dec     1.430237
          djf     0.816650
          mam     8.695923
          jja    17.266663
          son     8.868652
          ann     8.911972
    prec  jan    48.000000
          feb    42.000000
          mar    44.000000
          apr    44.000000
          mai    56.000000
          jun    68.000000
          jul    65.000000
          aug    52.000000
          sep    47.000000
          oct    52.000000
          nov    52.000000
          dec    59.000000
          djf    49.666667
          mam    48.000000
          jja    61.666667
          son    50.333333
          ann    52.416667
    Name: (50, 10), dtype: float64


    >>> get_climate(50, 10)['tavg', 'djf']
    0.816650390625

    >>> get_climate([10, 11], [50, 51])
                tavg             ...       prec
                 jan        feb  ...        son       ann
    lat lon                        ...
    10  50   21.810730  22.687988  ...  10.666667  6.833333
    11  51   24.617249  24.678040  ...   7.666667  3.750000
    <BLANKLINE>
    [2 rows x 34 columns]

Data download
-------------
This package is built upon freely available datasets but does not contain any
data. This data is downloaded on request (see the next section). In particular,
the `get_climate` method uses the data from [WorldClim2.0]_, the `get_country`
function uses the `datasets/geo-countries`_ repository.

Download directory
******************
To download and process the necessary datasets, run::

    python -m latlon_utils.download

(see ``python -m latlon_utils.download --help`` for available options).

We download the GeoTIFF files from WorldClim_ and transform them to netCDF
datasets. The default directory to store the data is in
``$HOME/.local/share/latlon_utils``, where ``$HOME`` stands for the users home
directory. If you want to use a different directory, set the ``LATLONDATA``
variable, e.g.::

    export LATLONDATA=$HOME/my_data
    python download.py $LATLONDATA

The ``LATLONDATA`` environment variable is necessary to ensure that the python
package finds the data later again.

WorldClim resolutions
*********************
The default resolution that we use is ``10m``. However, you can also specify
other resolutions in the python functions or via the ``LATLONRES`` environment
variable. To use, for example the 5 minutes resolutions, simply run::

    export LATLONRES='5m'


References
----------
.. [WorldClim2.0] Fick, S.E. and R.J. Hijmans, 2017. Worldclim 2: New 1-km spatial resolution climate surfaces for global land areas. International Journal of Climatology. http://worldclim.org/

.. _WorldClim: http://worldclim.org/
.. _datasets/geo-countries: https://github.com/datasets/geo-countries
.. _xarray: http://xarray.pydata.org/en/stable/
.. _rasterio: https://rasterio.readthedocs.io/en/stable/
.. _netCDF4: https://github.com/Unidata/netcdf4-python
.. _pandas: https://pandas.pydata.org/
.. _conda: https://conda.io/projects/conda/en/latest/
.. _shapely: https://shapely.readthedocs.io/en/latest/


.. |travis| image:: https://travis-ci.org/Chilipp/latlon-utils.svg?branch=master
    :alt: Travis
    :target: https://travis-ci.org/Chilipp/latlon-utils

.. |codecov| image:: https://codecov.io/gh/Chilipp/latlon-utils/branch/master/graph/badge.svg
    :alt: Coverage
    :target: https://codecov.io/gh/Chilipp/latlon-utils

.. |version| image:: https://img.shields.io/pypi/v/latlon-utils.svg?style=flat
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/latlon-utils

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/latlon-utils.svg?style=flat
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/latlon-utils

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/latlon-utils.svg?style=flat
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/latlon-utils

.. |github| image:: https://img.shields.io/github/release/Chilipp/latlon-utils.svg
    :target: https://github.com/Chilipp/latlon-utils/releases/latest
    :alt: Latest github release
