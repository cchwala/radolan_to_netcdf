import unittest
import os
import pkg_resources
import glob
import netCDF4
import numpy as np
from numpy.testing import assert_almost_equal
from radolan_to_netcdf import radolan_to_netcdf


def get_test_data_path():
    return pkg_resources.resource_filename('radolan_to_netcdf',
                                           'tests/test_data')

def get_test_data_for_product(product_name):
    fn_patterns = {
        'RW': 'radolan_rw/raa01-rw_10000-181122*---bin.gz',
        'YW': 'radolan_yw/raa01-yw2017.002_10000*bin.gz'
    }

    return glob.glob(os.path.join(get_test_data_path(),
                                  fn_patterns[product_name]))

def parse_and_validate_test_data(product_name):
    fn = 'test.nc'
    radolan_to_netcdf.create_empty_netcdf(fn, product_name=product_name)

    data_list, metadata_list = [], []

    for fn_radolan_file in get_test_data_for_product(product_name):
        data, metadata = radolan_to_netcdf.read_in_one_bin_file(
            fn_radolan_file)
        data_list.append(data)
        metadata_list.append(metadata)

    radolan_to_netcdf.create_empty_netcdf(fn=fn, product_name=product_name)

    radolan_to_netcdf.append_to_netcdf(
        fn=fn,
        data_list=data_list,
        metadata_list=metadata_list)

    with netCDF4.Dataset(fn, mode='r') as ds:
        actual = ds['rainfall_amount'][:].filled(np.nan).sum(axis=0)
        reference = np.stack(data_list, axis=2).sum(axis=2)
        assert_almost_equal(actual, reference)

    os.remove(fn)


def test_RW():
    parse_and_validate_test_data(product_name='RW')


def test_YW():
    parse_and_validate_test_data(product_name='YW')


def test_flagged_pixels():
    fn_radolan_files = get_test_data_for_product(product_name='RW')
    fn_bin = fn_radolan_files[0]
    data, metadata = radolan_to_netcdf.read_in_one_bin_file(fn_bin)
    # Write file to NetCDF
    fn = 'test.nc'
    radolan_to_netcdf.create_empty_netcdf(fn, product_name='RW')
    radolan_to_netcdf.append_to_netcdf(fn, [data, ], [metadata, ])

    for flag_name in ['secondary', 'nodatamask', 'cluttermask']:

        # Read back and check flagged pixels
        with netCDF4.Dataset(fn, mode='r') as ds:
            # Get data as matrix from NetCDF and derive the non-zero indices
            # because this is how they are stored in RADOLAN bin files and
            # wradlib returns them that way
            actual = np.nonzero(ds[flag_name][0, :, :].flatten())[0]
            reference = metadata[flag_name]

            np.testing.assert_almost_equal(actual, reference)

    os.remove(fn)
