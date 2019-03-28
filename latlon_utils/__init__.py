"""Utility functions to retrieve lat-lon specific informations"""
import os
import os.path as osp
import json
from itertools import starmap, product
import numpy as np
import pandas as pd


__version__ = '0.0.4'

__author__ = 'Philipp S. Sommer'


#: Variables in the WorldClim v2.0 dataset
worldclim_variables = {
    'tmin': 'minimum temperature (degC)',
    'tmax': 'maximum temperature (degC)',
    'tavg': 'maximum temperature (degC)',
    'prec': 'precipitation (mm)',
    'srad': 'solar radiation (kJ m-2 day-1)',
    'wind': 'wind speed (m s-1)',
    'vapr': 'water vapor pressure (kPa)',
    }

#: The available resolutions for the WorldClim data
worldclim_resolutions = ['10m', '5m', '2.5m', '30s']


def get_data_dir():
    """Get the data directory where the downloads are stored.

    You can either set this with the ``LATLONDATA`` environment variable or we
    use ``$HOME/.local/share/latlon_utils``.

    Returns
    -------
    str
        The directory for the data. If it is not yet existing, it will be
        created

    See Also
    --------
    get_data_file: To retrieve the path to a file in this directory"""
    ret = os.getenv('LATLONDATA', osp.join(osp.expanduser("~"), '.local',
                                           'share', 'latlon_utils'))
    if not osp.exists(ret):
        os.makedirs(ret)
    return ret


def get_wc_resolution(res):
    """Get the resolution used for the WorldClim data

    Parameters
    ----------
    res: {'10m', '5m', '2.5m', '30s'}
        If None, the ``LATLONRES`` environment variable is used. If this is not
        set, we set the default resolution to '10m'"""
    return res or os.getenv("LATLONRES", '10m')


def get_data_file(fname, download=True):
    """Get the path of a data file in the data directory

    Parameters
    ----------
    fname: str
        The file name in the data directory (see :func:`get_data_dir`)
    download: bool
        If True and the file is missing, it will be downloaded"""
    ret = osp.join(get_data_dir(), fname)
    if not osp.exists(ret):
        if fname == 'countries.geojson':
            from latlon_utils.download import download_geo_countries
            download_geo_countries()
        elif fname in starmap(
                '{}_{}.nc'.format,
                product(worldclim_variables, worldclim_resolutions)):
            from latlon_utils.download import download_wc_variable
            var, res = osp.splitext(fname)[0].split('_')
            download_wc_variable(var, res=res)
        elif fname == 'ne_10m_admin_0_countries.shp':
            from latlon_utils.download import download_natural_earth_countries
            download_natural_earth_countries()
        else:
            raise ValueError(
                "Could not find %s in %s!" % (fname, get_data_dir()))
    return ret


def get_country(lat, lon):
    """Get the country at the specific latitude and longitude

    Parameters
    ----------
    lat: float or np.ndarray of floats
        The latitude between -90 and 90
    lon: float or np.ndarray of floats
        The longitude between -180 and 360

    Returns
    -------
    str or list of str
        The Country name(s) or ``'unknown'`` if no country could be found at
        the given lat-lon combination

    Examples
    --------
    Get the country for 50 degrees north and 10 degrees east::

        >>> from latlon_utils import get_country

        >>> get_country(50, 10)
        'Germany'
    """
    from shapely.geometry import shape, Point
    from shapely.prepared import prep

    assert np.shape(lat) == np.shape(lon)

    with open(get_data_file('countries.geojson')) as f:
        data = json.load(f)

    countries = {}
    for feature in data["features"]:
        geom = feature["geometry"]
        country = feature["properties"]["ADMIN"]
        countries[country] = prep(shape(geom))

    def get_country(lat, lon):
        point = Point(lon, lat)
        for country, geom in countries.items():
            if geom.contains(point):
                return country

        return "unknown"

    if not np.ndim(lat):
        return get_country(lat, lon)
    else:
        return list(starmap(get_country, zip(lat, lon)))


def test_get_country():
    assert get_country(50, 10) == 'Germany'


def get_country_gpd(lat, lon):
    """Get the country using geopandas

    Parameters
    ----------
    lat: float or np.ndarray of floats
        The latitude between -90 and 90
    lon: float or np.ndarray of floats
        The longitude between -180 and 360

    Returns
    -------
    str or np.ndarray of strings
        The country name (or names if `lat` and `lon` are arrays)"""
    import geopandas as gpd
    from shapely.geometry import Point
    nat_earth = get_data_file('ne_10m_admin_0_countries.shp')
    ne_df = gpd.read_file(nat_earth)

    squeeze = np.ndim(lat) == 0

    points = pd.DataFrame(np.vstack([lon, lat]).T, columns=['lon', 'lat'])
    points['geometry'] = list(map(tuple, points.values.tolist()))
    points['geometry'] = points['geometry'].apply(Point)

    points_gpd = gpd.GeoDataFrame(points, geometry='geometry')
    points_gpd.crs = ne_df.crs

    ret = gpd.sjoin(points_gpd, ne_df, how='left', op='within').ADMIN.values
    return ret[0] if squeeze else ret


def test_get_country_gpd():
    assert get_country_gpd(50, 10) == 'Germany'


def get_climate(lat, lon, variables=['tavg', 'prec'], res=None):
    """Get the country at the specific latitude and longitude

    Parameters
    ----------
    lat: float or np.ndarray of floats
        The latitude between -90 and 90
    lon: float or np.ndarray of floats
        The longitude between -180 and 360
    variables: list of str
        The variables to include. By default average temperature (tavg) and
        precipitation (prec). Avaiable datasets in the WorldClim v2.0 dataset
        are

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
    res: str
        The resolution to use. If None, it defaults to the
        ``LATLONRES`` environment variable or ``'10m'``

    Returns
    -------
    pandas.DataFrame or pandas.Series
        Climate information for the given cells. The index is a
        :class:`pandas.MultiIndex` with the first level being `lat` and the
        second `lon`, the columns are a :class:`pandas.MultiIndex` with the
        first variable being one of ``'tavg'`` and ``'prec'`` and the second
        are the monthly, seasonal and annual means. To access, for example, the
        temperature in july, you can write ``df['tavg', 'jul']``

        If `lat` is not an array, a pandas.Series is returned.

    Examples
    --------
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
    """
    import netCDF4 as nc
    assert np.shape(lat) == np.shape(lon)

    def find_closest(arr, vals):
        idx = np.searchsorted(arr, vals)
        diff = arr[idx] - vals
        diffprev = vals - arr[idx - 1]
        idx[idx == arr.size] = arr.size - 1
        idx[(idx > 0) & (idx < arr.size) & (diff > diffprev)] -= 1
        return idx

    squeeze = False
    if np.ndim(lat) == 0:
        lat = [lat]
        lon = [lon]
        squeeze = True

    lat = np.asarray(lat)
    lon = np.asarray(lon)
    lon = np.where(lon > 180, lon - 360, lon)

    months = ['jan', 'feb', 'mar', 'apr', 'mai', 'jun', 'jul', 'aug', 'sep',
              'oct', 'nov', 'dec']

    cols = months + ['djf', 'mam', 'jja', 'son', 'ann']

    ret = pd.DataFrame(
        index=pd.MultiIndex.from_tuples(list(zip(lat, lon)),
                                        names=['lat', 'lon']),
        columns=pd.MultiIndex.from_product([variables, cols]),
        dtype=float)

    res = get_wc_resolution(res)

    data_files = [get_data_file(v + '_' + res + '.nc') for v in variables]

    for v, fname in zip(variables, data_files):
        with nc.Dataset(fname) as nco:
            nco.set_auto_mask(False)
            idx_lon = find_closest(nco.variables['lon'][:], lon)
            idx_lat = nco.variables['lat'].shape[0] - 1 - find_closest(
                nco.variables['lat'][::-1], lat)
            for i, (j, k) in enumerate(zip(idx_lat, idx_lon)):
                ret.loc[slice(i, i+1), (v, months)] = nco.variables[v][:, j, k]

    # compute seasonal averages
    for var in variables:
        ret[var, 'djf'] = ret[var][['jan', 'feb', 'dec']].mean(axis=1)
        ret[var, 'mam'] = ret[var][['mar', 'apr', 'mai']].mean(axis=1)
        ret[var, 'jja'] = ret[var][['jun', 'jul', 'aug']].mean(axis=1)
        ret[var, 'son'] = ret[var][['sep', 'oct', 'nov']].mean(axis=1)
        ret[var, 'ann'] = ret[var][months].mean(axis=1)
    if squeeze:
        return ret.T.iloc[:, 0]
    return ret


def test_get_climate():
    """Test the :func:`get_climate` function"""
    import netCDF4 as nc
    from numpy.testing import assert_allclose
    lat, lon = 50, 10
    with nc.Dataset(get_data_file('tavg_10m.nc')) as nco:
        idx_lat = pd.Index(nco.variables['lat'][:]).get_loc(
            lat, method='nearest')
        idx_lon = pd.Index(nco.variables['lon'][:]).get_loc(
            lon, method='nearest')
        tmonth = nco.variables['tavg'][:, idx_lat, idx_lon]
    with nc.Dataset(get_data_file('prec_10m.nc')) as nco:
        pmonth = nco.variables['prec'][:, idx_lat, idx_lon]

    ref = np.r_[tmonth, tmonth[[0, 1, -1]].mean(), tmonth[2:5].mean(),
                tmonth[5:8].mean(), tmonth[8:11].mean(), tmonth.mean(),
                pmonth, pmonth[[0, 1, -1]].mean(), pmonth[2:5].mean(),
                pmonth[5:8].mean(), pmonth[8:11].mean(), pmonth.mean()]

    assert_allclose(get_climate(lat, lon), ref)
