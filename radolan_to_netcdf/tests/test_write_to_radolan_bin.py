import unittest
import wradlib as wrl
import numpy as np

from radolan_to_netcdf import radolan_to_netcdf
from radolan_to_netcdf import wradlib_to_radolan_bin
from radolan_to_netcdf.tests.tools import get_test_data_for_product

class TestWradlibMetadataToHeader(unittest.TestCase):
    for fn_radolan_file in get_test_data_for_product('RW'):
        data, metadata = radolan_to_netcdf.read_in_one_bin_file(
            fn_radolan_file)

        with wrl.io.radolan.get_radolan_filehandle(fn_radolan_file) as f:
            reference = wrl.io.radolan.read_radolan_header(f)

        actual = wradlib_to_radolan_bin.metadata_to_header(metadata)

        assert actual == reference
