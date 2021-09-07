import wradlib as wrl
import netCDF4
from datetime import datetime
import numpy as np

from .radolan_product_netcdf_config import radolan_product_netcdf_config


def create_empty_netcdf(fn, product_name=None, product_config_dict=None):
    """Create an empty NetCDF file for the desired RADOLAN product

    Parameters
    ----------
    fn : str
        Filename
    product_name : str , optional
        The two-character RADOLAN product name, e.g. 'RW', for which
        the parameters for the creation of the NetCDF file will be
        looked up in the dictionary `radolan_product_netcdf_config`.
    product_config_dict : dict, optional
        Dictionary holding the parameters required for building
        a NetCDF file with the correct dimensions, variables names
        and attributes. Use this if your product is not yet supported
        via passing only the `product_name` (which is the preferred way).
        The `product_name` always has to be supplied in addition to
        this variable.

    """

    if not product_name and not product_config_dict:
        raise ValueError(
            "Either product_name or product_config_dict " "have to be supplied."
        )
    elif not product_name and product_config_dict:
        raise ValueError(
            "A product_name has to be supplied when supplying " "a product_config_dict."
        )
    elif product_name and not product_config_dict:
        product_config_dict = radolan_product_netcdf_config[product_name]
    else:
        pass

    with netCDF4.Dataset(fn, "w") as nc_fh:
        n_lons = product_config_dict["metadata_fixed"]["n_lons"]
        n_lats = product_config_dict["metadata_fixed"]["n_lats"]

        # Get RADOLAN coordinates
        radolan_xy_grids = wrl.georef.get_radolan_grid(ncols=n_lons, nrows=n_lats)
        radolan_x = radolan_xy_grids[0, :, 0]
        radolan_y = radolan_xy_grids[:, 0, 1]
        radolan_lat_lon_grids = wrl.georef.get_radolan_grid(
            ncols=n_lons, nrows=n_lats, wgs84=True
        )
        radolan_lons = radolan_lat_lon_grids[:, :, 0]
        radolan_lats = radolan_lat_lon_grids[:, :, 1]

        # create dimensions
        nc_fh.createDimension("x", n_lons)
        nc_fh.createDimension("y", n_lats)
        nc_fh.createDimension("time", None)

        # create the variables we need in all files
        nc_fh.createVariable("x", "f8", ("x"))
        nc_fh.createVariable("y", "f8", ("y"))
        nc_fh.createVariable("latitudes", "f8", ("y", "x"))
        nc_fh.createVariable("longitudes", "f8", ("y", "x"))
        nc_fh.createVariable("time", "f8", ("time"))

        # create the individual specified variables with their attributes
        for variable_name, variable_config in product_config_dict["variables"].items():
            variable_parameters = variable_config["variable_parameters"].copy()
            nc_var = nc_fh.createVariable(
                varname=variable_name,
                datatype=variable_parameters.pop("datatype"),
                **variable_parameters
            )
            nc_var.setncatts(variable_config["attributes"])

        # create variables for the metadata that changes per time stamp
        for variable_name, variable_config in product_config_dict[
            "metadata_per_timestamp"
        ].items():
            variable_parameters = variable_config["variable_parameters"].copy()
            nc_var = nc_fh.createVariable(
                varname=variable_name,
                datatype=variable_parameters.pop("datatype"),
                **variable_parameters
            )
            nc_var.setncatts(variable_config["attributes"])

        nc_fh.set_auto_maskandscale(True)

        # variable attributes
        nc_fh["time"].long_name = "Time"
        nc_fh["time"].standard_name = "time"
        nc_fh["time"].units = "hours since 2000-01-01 00:50:00.0"
        nc_fh["time"].calendar = "standard"

        nc_fh["x"].long_name = "RADOLAN Grid x coordinate of projection"
        nc_fh["x"].standard_name = "projection_x_coordinate"
        nc_fh["x"].units = "km"

        nc_fh["y"].long_name = "RADOLAN Grid y coordinate of projection"
        nc_fh["y"].standard_name = "projection_y_coordinate"
        nc_fh["y"].units = "km"

        nc_fh["latitudes"].long_name = "Latitude"
        nc_fh["latitudes"].standard_name = "latitude"
        nc_fh["latitudes"].units = "degrees_north"

        nc_fh["longitudes"].long_name = "Longitude"
        nc_fh["longitudes"].standard_name = "longitude"
        nc_fh["longitudes"].units = "degrees_east"

        # global attributes
        nc_fh.title = "RADOLAN %s rainfall data" % product_name
        nc_fh.producttype = product_name
        # nc_fh.source = 'ftp://ftp-cdc.dwd.de/pub/CDC/grids_germany/hourly/radolan/'
        nc_fh.institution = "Deutscher Wetterdienst (DWD)"
        nc_fh.history = "Created at " + str(datetime.utcnow())
        nc_fh.Conventions = "CF-1.6"

        # Add actual coordinate data
        nc_fh["latitudes"][:, :] = radolan_lats
        nc_fh["longitudes"][:, :] = radolan_lons
        nc_fh["x"][:] = radolan_x
        nc_fh["y"][:] = radolan_y

        # Add projection definition
        nc_fh.createVariable("radolan_grid", "f8")
        nc_fh["radolan_grid"].long_name = "RADOLAN Grid"
        nc_fh["radolan_grid"].grid_mapping_name = "polar_stereographic"
        nc_fh["radolan_grid"].semi_major_axis = 6370040.0
        nc_fh["radolan_grid"].false_easting = 0.0
        nc_fh["radolan_grid"].false_northing = 0.0
        nc_fh["radolan_grid"].scale_factor_at_projection_origin = 0.9330127019
        nc_fh["radolan_grid"].straight_vertical_longitude_from_pole = 10.0
        nc_fh["radolan_grid"].latitude_of_projection_origin = 90.0


def read_in_one_bin_file(f):
    data, metadata = wrl.io.read_radolan_composite(f, missing=np.nan)
    return data, metadata


def append_to_netcdf(fn, data_list, metadata_list):
    """Append RADOLAN data and metadata to existing NetCDF

    WIP!

    Does currently only work for RADOLAN RW data

    """
    if type(data_list) != list:
        data_list = [
            data_list,
        ]
    if type(metadata_list) != list:
        metadata_list = [
            metadata_list,
        ]
    with netCDF4.Dataset(fn, "a") as nc_fh:
        current_length = len(nc_fh["time"][:])
        for i, (data, metadata) in enumerate(zip(data_list, metadata_list)):
            i_new = i + current_length
            nc_fh["time"][i_new] = netCDF4.date2num(
                metadata["datetime"],
                units=nc_fh["time"].units,
                calendar=nc_fh["time"].calendar,
            )

            product_name = metadata["producttype"]
            product_config_dict = radolan_product_netcdf_config[product_name]

            if product_name != nc_fh.producttype:
                raise ValueError(
                    "RADOLAN product of data is `%s` and "
                    "is `%s` in existing NetCDF" % (product_name, nc_fh.producttype)
                )

            variable_names = list(product_config_dict["variables"].keys())
            if len(variable_names) != 1:
                raise NotImplementedError(
                    "Writting the actual RADOLAN data "
                    "to NetCDF is only supported for "
                    "one `variable`."
                )

            variable_name = variable_names[0]
            variable_config = product_config_dict["variables"][variable_name]

            if "fill_value" in variable_config["variable_parameters"]:
                fill_value = variable_config["variable_parameters"]["fill_value"]
                offset = variable_config["attributes"]["add_offset"]
                scale_factor = variable_config["attributes"]["scale_factor"]

                fill_value_float = fill_value * scale_factor + offset

                temp_data = data.copy()
                temp_data[np.isnan(temp_data)] = fill_value_float
            else:
                temp_data = data
            nc_fh[variable_name][i_new, :, :] = temp_data

            # TODO: Remove this hardcoding of writing `secondary` and `nodatamask`
            secondary = np.zeros_like(data, dtype="bool").flatten()
            secondary[metadata["secondary"]] = True
            nc_fh["secondary"][i_new, :, :] = secondary.reshape(data.shape)

            nodatamask = np.zeros_like(data, dtype="bool").flatten()
            nodatamask[metadata["nodatamask"]] = True
            nc_fh["nodatamask"][i_new, :, :] = nodatamask.reshape(data.shape)

            cluttermask = np.zeros_like(data, dtype="bool").flatten()
            cluttermask[metadata["cluttermask"]] = True
            nc_fh["cluttermask"][i_new, :, :] = cluttermask.reshape(data.shape)

            # TODO make this more flexible and also test for it !!!
            nc_fh["maxrange"][i_new] = int(metadata["maxrange"].split(" ")[0])
            nc_fh["radarlocations"][i_new] = " ".join(metadata["radarlocations"])
