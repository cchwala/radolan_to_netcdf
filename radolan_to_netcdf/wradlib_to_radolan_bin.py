import datetime
import numpy as np


def metadata_to_header(metadata):
    """

    Parameters
    ----------
    metadata : dict
        Dict of metadata as returned by wradlib.io.read_radolan_composite

    Returns
    -------

    header : byte string
        Header byte string conforming to the definition of RADOALN binary files

    """

    if metadata["producttype"] != "RW":
        raise NotImplementedError("Currently only RADOALN-RW is supported")

    len_header_fixed_part = 82
    len_header_radar_locations = len("<" + ",".join(metadata["radarlocations"]) + "> ")

    len_header = len_header_fixed_part + len_header_radar_locations

    # Generate empty header with only whitespaces
    header_out = np.array(
        [
            "",
        ]
        * len_header,
        dtype="S1",
    )
    header_out[:] = " "

    # Fill header with metadata and tokens
    header_out[0:2] = list(metadata["producttype"])
    header_out[2:8] = list(datetime.datetime.strftime(metadata["datetime"], "%d%H%M"))
    header_out[8:13] = list(metadata["radarid"])
    header_out[13:17] = list(datetime.datetime.strftime(metadata["datetime"], "%m%y"))

    header_out[17:19] = list("BY")
    # Have to add one here to get correct length in header string.
    # Do not know why. Maybe because of the 'etx' char
    header_out[19:26] = list(str(metadata["datasize"] + len_header + 1))

    header_out[26:28] = list("VS")
    header_out[28:30] = list(
        {
            "100 km and 128 km (mixed)": " 0",
            "100 km": " 1",
            "128 km": " 2",
            "150 km": " 3",
        }.get(metadata["maxrange"])
    )

    header_out[30:32] = list("SW")
    header_out[32:41] = list(metadata["radolanversion"].rjust(9))

    header_out[41:43] = list("PR")
    header_out[43:48] = list(
        {
            0.01: " E-02",
            0.1: " E-01",
            1: " E-00",
        }.get(metadata["precision"])
    )

    header_out[48:51] = list("INT")
    header_out[51:55] = list(str(int(metadata["intervalseconds"] / 60)).rjust(4))

    header_out[55:57] = list("GP")
    header_out[57:66] = list(
        str(metadata["nrow"]).rjust(4) + "x" + str(metadata["ncol"]).rjust(4)
    )

    header_out[66:68] = list("MF")
    header_out[69:77] = list(str(int(metadata["moduleflag"])).zfill(8))

    header_out[77:79] = list("MS")
    header_out[79:82] = list(str(int(len_header_radar_locations)).rjust(3))

    header_out[82 : (82 + len_header_radar_locations)] = list(
        "<" + ",".join(metadata["radarlocations"]) + "> "
    )

    header_out = b"".join(header_out).decode()

    return header_out


def data_to_byte_array(data, metadata):
    """

    Parameters
    ----------
    data
    metadata

    Returns
    -------

    """

    if metadata["producttype"] != "RW":
        raise NotImplementedError("Currently only RADOALN-RW is supported")

    arr = (data / metadata["precision"]).flatten().astype(np.uint16)

    secondary = np.zeros_like(arr, dtype=np.uint16)
    secondary[metadata["secondary"]] = 0x1000

    nodatamask = np.zeros_like(arr, dtype=np.uint16)
    nodatamask[metadata["nodatamask"]] = 0b0010100111000100

    cluttermask = np.zeros_like(arr, dtype=np.uint16)
    cluttermask[metadata["cluttermask"]] = 0x8000

    arr = arr | secondary | nodatamask | cluttermask

    return arr.tobytes()


def write_to_radolan_bin_file(fn, data, metadata):
    """

    Parameters
    ----------
    fn
    data
    metadata

    Returns
    -------

    """

    data_as_byte_str = data_to_byte_array(data, metadata)
    header_as_byte_str = metadata_to_header(metadata)

    with open(fn, mode="wb") as f:
        f.write(header_as_byte_str.encode())
        f.write(b"\x03")
        f.write(data_as_byte_str)
