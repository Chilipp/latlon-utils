import argparse
import os
import os.path as osp
from urllib import request
import xarray as xr
import numpy as np
import zipfile
import glob
import re
import datetime as dt
import tempfile
from latlon_utils import (
    get_data_dir, worldclim_variables, worldclim_resolutions, __version__)


wc_base_url = 'http://biogeo.ucdavis.edu/data/worldclim/v2.0/tif/base/'

SILENT = False

unit_patt = re.compile(r'\(.+\)')


def download_wc_variable(name, outdir=None, res='5m', lat=None, lon=None):
    """Download a WorldClim variable and transform it to a netcdf file

    Parameters
    ----------
    name: str
        The variable name. One of

        tmin
            minimum temperature (°C)
        tmax
            maximum temperature (°C)
        tavg
            maximum temperature (°C)
        prec
            precipitation (mm)
        srad
            solar radiation (kJ m-2 day-1)
        wind
            wind speed (m s-1)
        vapr
            water vapor pressure (kPa)
    outdir: str
        The target directory. If None, the default data directory for the
        latlon_utils (see the :func:`latlon_utils.get_data_dir` function) is
        used
    res: str
        The resolution string. One out of ``'10m', '5m', '2.5m'`` and ``'30s'``
    lat: indexer
        An indexer to use for the latitudes to extract a subset of the data
        Can be anything valid for the :meth:`xarray.DataArray.sel` method.
    lon: indexer
        An indexer to use for the latitudes to extract a subset of the data.
        Can be anything valid for the :meth:`xarray.DataArray.sel` method.

    Returns
    -------
    str
        The path to the downloaded netCDF file
    """
    if outdir is None:
        outdir = get_data_dir()

    if not osp.exists(outdir):
        os.makedirs(outdir)
    base = 'wc2.0_%s_%s.zip' % (res, name)
    outfile = osp.join(outdir, name + '_' + res + '.nc')

    with tempfile.TemporaryDirectory(prefix='worldclim_') as download_dir:
        download_target = osp.join(download_dir, base)

        url = wc_base_url + base

        if not SILENT:
            print('Downloading ' + url)
        request.urlretrieve(url, download_target)

        if not SILENT:
            print('Extracting ' + download_target)
        with zipfile.ZipFile(download_target) as f:
            f.extractall(download_dir)

        tiffs = sorted(glob.glob(osp.join(download_dir,
                                          'wc2.0_%s_%s_??.tif' % (res, name))))
        da = xr.concat(list(map(xr.open_rasterio, tiffs)),
                       dim=xr.Variable(('month', ), np.arange(1, 13)))
        da.encoding = dict(zlib=True, complevel=4, least_significant_digit=4)
        da.name = name

        if not SILENT:
            print("Saving as netcdf file to " + outfile)
        sel = {'band': 1}
        if lat is not None:
            sel['y'] = lat
        if lon is not None:
            sel['x'] = lon
        da.attrs['long_name'] = unit_patt.sub(
            '', worldclim_variables[name]).strip()
        da.attrs['units'] = unit_patt.search(
            worldclim_variables[name]).group()[1:-1]
        da.attrs['history'] = (
            '%s: Downloaded %s data with latlon-utils (%s) from %s' % (
                dt.datetime.now().isoformat(), name, __version__, url))
        da.attrs['reference'] = (
            'Fick, S.E. and R.J. Hijmans, 2017. Worldclim 2: New 1-km spatial '
            'resolution climate surfaces for global land areas. International '
            'Journal of Climatology.')
        da.sel(**sel).rename({'x': 'lon', 'y': 'lat'}).to_netcdf(outfile)
    return outfile


def download_geo_countries(outdir=None):
    """Download the datasets/geo-countries dataset

    Parameters
    ----------
    outdir: str
        The target directory. If None, the default data directory for the
        latlon_utils (see the :func:`latlon_utils.get_data_dir` function) is
        used

    Returns
    -------
    str
        The path to the downloaded file"""
    if outdir is None:
        outdir = get_data_dir()

    if not osp.exists(outdir):
        os.makedirs(outdir)
    download_target = osp.join(outdir, 'countries.geojson')

    url = ("https://raw.githubusercontent.com/datasets/geo-countries/master/"
           "data/countries.geojson")

    if not SILENT:
        print('Downloading %s to %s' % (url, download_target))
    request.urlretrieve(url, download_target)
    return download_target


def download_natural_earth_countries(outdir=None):
    """Download the natural earth 10m admin 0 countries

    Parameters
    ----------
    outdir: str
        The target directory. If None, the default data directory for the
        latlon_utils (see the :func:`latlon_utils.get_data_dir` function) is
        used

    Returns
    -------
    str
        The path to the downloaded shapefile"""
    if outdir is None:
        outdir = get_data_dir()

    if not osp.exists(outdir):
        os.makedirs(outdir)
    download_target = osp.join(outdir, 'ne_10m_admin_0_countries.zip')

    url = ('https://www.naturalearthdata.com/http//www.naturalearthdata.com/'
           'download/10m/cultural/ne_10m_admin_0_countries.zip')

    if not SILENT:
        print('Downloading %s to %s' % (url, download_target))
    request.urlretrieve(url, download_target)
    with zipfile.ZipFile(download_target) as f:
        f.extractall(outdir)
    os.remove(download_target)
    return osp.splitext(download_target)[0] + '.shp'


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'outdir',
        help=("The target directory where to download the data. "
              "Default: %(default)s"), nargs='?',
        default=get_data_dir())
    parser.add_argument(
        '-res', '--worldclim-resolution', default='10m',
        choices=worldclim_resolutions,
        help="The resolution for the WorldClim data. Default: %(default)s")
    parser.add_argument(
        '-v', '--worldclim-variables', nargs='+', default=['tavg', 'prec'],
        help="WorldClim variables to download. Default: %(default)s",
        choices=['all'] + list(worldclim_variables))
    parser.add_argument('-lat', nargs=2, type=float,
                        help='Minimum and maximum latitude')
    parser.add_argument('-lon', nargs=2, type=float,
                        help='Minimum and maximum longitude')
    parser.add_argument('-no-wc', '--no-worldclim', action='store_true',
                        help="Skip the download of WorldClim data")
    return parser


def main(args=None):
    parser = get_parser()
    args = parser.parse_args(args)

    # update global variables
    lon = args.lon and slice(*sorted(args.lon))
    lat = args.lat and slice(*sorted(args.lat)[::-1])
    outdir = args.outdir

    # download WorldClim data
    if not args.no_worldclim:
        if 'all' in args.worldclim_variables:
            variables = list(worldclim_variables)
        else:
            variables = args.worldclim_variables
        for v in variables:
            download_wc_variable(v, outdir, lat=lat, lon=lon,
                                 res=args.worldclim_resolution)

    # download countries.geojson
    download_geo_countries(outdir)

    # download natural earth
    download_natural_earth_countries()


def test_command_line():
    with tempfile.TemporaryDirectory(prefix='worldclim_') as test_dir:
        main((test_dir + ' -v tavg -lat 20 30 -lon 20 30 -res 10m').split())
        assert osp.exists(osp.join(test_dir, 'tavg_10m.nc'))
        assert osp.exists(osp.join(test_dir, 'countries.geojson'))


if __name__ == '__main__':
    main()
