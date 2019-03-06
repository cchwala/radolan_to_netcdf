import unittest
from numpy.testing import assert_almost_equal
from radolan_to_netcdf import radolan_to_netcdf


class TestRadolanRW(unittest.TestCase):
    def test_write_new_netcdf(self):
        fn = 'test.nc'
        radolan_to_netcdf.create_empty_netcdf(fn, product_name='RW')

        data_list, metadata_list = [], []
        for fn_radolan_file in glob.glob(
            'data/radolan_rw/raa01-rw_10000-181122*---bin.gz'):
            data, metadata = radolan_to_netcdf.read_in_one_bin_file(
                fn_radolan_file)
            data_list.append(data)
            metadata_list.append(metadata)

        fn = '/Users/chwala-c/Desktop/test.nc'
        create_empty_netcdf(fn=fn, product_name='RW')

        radolan_to_netcdf.append_to_netcdf(
            fn=fn,
            data_list=data_list,
            metadata_list=metadata_list)

        with netCDF4.Dataset(fn, mode='r') as ds:
            actual = ds['rainfall_amount'][:].filled(np.nan).sum(axis=0)
            reference = np.stack(data_list, axis=2).sum(axis=2)
            assert_almost_equal(actual, reference)


