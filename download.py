import argparse
import os
import os.path as osp
from urllib import request
import xarray as xr
import numpy as np
import zipfile
import glob

# make the target folder
outdir = osp.join(osp.dirname(__file__), 'latlon_utils', 'data')

lon = None
lat = None

base_url = 'http://biogeo.ucdavis.edu/data/worldclim/v2.0/tif/base/'


def download_wc_variable(name):
    if not osp.exists(outdir):
        os.makedirs(outdir)
    base = 'wc2.0_5m_%s.zip' % name
    outfile = osp.join(outdir, name + '.nc')
    download_target = osp.join(outdir, base)

    print('Downloading ' + base_url + base)
    request.urlretrieve(base_url + base, download_target)

    print('Extracting ' + download_target)
    with zipfile.ZipFile(download_target) as f:
        f.extractall(outdir)

    tiffs = sorted(glob.glob(osp.join(outdir, 'wc2.0_5m_%s_??.tif' % name)))
    da = xr.concat(list(map(xr.open_rasterio, tiffs)),
                   dim=xr.Variable(('month', ), np.arange(1, 13)))
    da.encoding = dict(zlib=True, complevel=4, least_significant_digit=4)
    da.name = name

    print("Saving as netcdf file to " + outfile)
    sel = {'band': 1}
    if lat is not None:
        sel['y'] = lat
    if lon is not None:
        sel['x'] = lon
    da.sel(**sel).rename({'x': 'lon', 'y': 'lat'}).to_netcdf(outfile)
    for f in tiffs + [download_target]:
        os.remove(f)


def download_geo_countries():
    if not osp.exists(outdir):
        os.makedirs(outdir)
    download_target = osp.join(outdir, 'countries.geojson')

    url = ("https://raw.githubusercontent.com/datasets/geo-countries/master/"
           "data/countries.geojson")

    print('Downloading %s to %s' % (url, download_target))
    request.urlretrieve(url, download_target)


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'outdir',
        help=("The target directory where to download the data. "
              "Default: %(default)s"), nargs='?',
        default=outdir)
    parser.add_argument('-lat', nargs=2, type=float,
                        help='Minimum and maximum latitude')
    parser.add_argument('-lon', nargs=2, type=float,
                        help='Minimum and maximum longitude')
    return parser


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()

    # update global variables
    lon = args.lon and slice(sorted(args.lon))
    lat = args.lat and slice(sorted(args.lat)[::-1])
    outdir = args.outdir

    # download WorldClim data
    download_wc_variable('tavg')
    download_wc_variable('prec')

    # download countries.geojson
    download_geo_countries()
