import unittest
import wradlib as wrl
import numpy as np

from radolan_to_netcdf import radolan_to_netcdf
from radolan_to_netcdf import wradlib_to_radolan_bin
from radolan_to_netcdf.tests.tools import get_test_data_for_product

class TestWradlibMetadataToHeader(unittest.TestCase):
    def test_RW(self):
        for fn_radolan_file in get_test_data_for_product('RW'):
            data, metadata = radolan_to_netcdf.read_in_one_bin_file(
                fn_radolan_file)

            with wrl.io.radolan.get_radolan_filehandle(fn_radolan_file) as f:
                reference = wrl.io.radolan.read_radolan_header(f)

            actual = wradlib_to_radolan_bin.metadata_to_header(metadata)

            assert actual == reference

    def test_not_RW_error(self):
        with self.assertRaises(NotImplementedError) as context:
            fn_radolan_files = get_test_data_for_product('YW')
            data, metadata = radolan_to_netcdf.read_in_one_bin_file(
                fn_radolan_files[0])
            wradlib_to_radolan_bin.metadata_to_header(metadata)

        self.assertTrue(
            'Currently only RADOALN-RW is supported' in str(context.exception)
        )


class TestWradlibDataToByteArray(unittest.TestCase):
    def test_RW(self):
        for fn_radolan_file in get_test_data_for_product('RW'):
            data, metadata = radolan_to_netcdf.read_in_one_bin_file(
                fn_radolan_file)

            with wrl.io.radolan.get_radolan_filehandle(fn_radolan_file) as f:
                header = wrl.io.radolan.read_radolan_header(f)
                attrs = wrl.io.radolan.parse_dwd_composite_header(header)
                reference = wrl.io.read_radolan_binary_array(f, attrs['datasize'])

            actual = wradlib_to_radolan_bin.data_to_byte_array(data, metadata)

            assert actual == reference

    def test_not_RW_error(self):
        with self.assertRaises(NotImplementedError) as context:
            fn_radolan_files = get_test_data_for_product('YW')
            data, metadata = radolan_to_netcdf.read_in_one_bin_file(
                fn_radolan_files[0])
            wradlib_to_radolan_bin.data_to_byte_array(data, metadata)

        self.assertTrue(
            'Currently only RADOALN-RW is supported' in str(context.exception)
        )


class TestWradlibToRadolanBinaryRoundtrip(unittest.TestCase):
    def test_RW(self):
        for fn_radolan_file in get_test_data_for_product('RW'):
            data_reference, metadata_reference = radolan_to_netcdf.read_in_one_bin_file(
                fn_radolan_file)

            wradlib_to_radolan_bin.write_to_radolan_bin_file(
                fn='test_radolan.bin',
                data=data_reference,
                metadata=metadata_reference,
            )

            data_actual, metadata_actual = radolan_to_netcdf.read_in_one_bin_file(
                'test_radolan.bin')

            np.testing.assert_almost_equal(data_actual, data_reference)

            assert list(metadata_actual.keys()) == list(metadata_reference.keys())

            for key in metadata_reference.keys():
                try:
                    np.testing.assert_almost_equal(
                        metadata_actual[key], metadata_reference[key]
                    )
                except TypeError:
                    assert metadata_actual[key] == metadata_reference[key]
