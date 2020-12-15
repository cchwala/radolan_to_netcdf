import pkg_resources
import glob
import os


def get_test_data_path():
    return pkg_resources.resource_filename('radolan_to_netcdf',
                                           'tests/test_data')

def get_test_data_for_product(product_name):
    fn_patterns = {
        'RW': 'radolan_rw/raa01-rw_10000-181122*---bin.gz',
        'YW': 'radolan_yw/raa01-yw2017.002_10000*bin.gz',
        'RY': 'radolan_ry/raa01-ry_10000-2001011*-dwd---bin.gz'
    }

    return glob.glob(os.path.join(get_test_data_path(),
                                  fn_patterns[product_name]))
