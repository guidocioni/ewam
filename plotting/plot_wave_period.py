from multiprocessing import Pool
from functools import partial
from utils import *
import sys
from metpy.calc import wind_components

debug = False
if not debug:
    import matplotlib
    matplotlib.use('Agg')

import matplotlib.pyplot as plt

# The one employed for the figure name when exported 
variable_name = 'wave_period'

print_message('Starting script to plot '+variable_name)

# Get the projection as system argument from the call so that we can 
# span multiple instances of this script outside
if not sys.argv[1:]:
    print_message(
        'Projection not defined, falling back to default (euratl)')
    projection = 'euratl'
else:
    projection = sys.argv[1]


def main():
    """In the main function we basically read the files and prepare the variables to be plotted.
    This is not included in utils.py as it can change from case to case."""
    dset = read_dataset(variables=['TM10', 'MWD'],
                        projection=projection)

    dset['mwd'].attrs['units'] = 'degrees'
    speed = xr.full_like(dset['mwd'], fill_value=10)
    speed.attrs['units'] = 'm/s'
    u, v = wind_components(speed, dset['mwd'])

    u = xr.DataArray(u.magnitude,
                   coords=dset['mwd'].coords,
                   attrs={'standard_name': 'x component direction',
                          'units': ''},
                   name='u')
    v = xr.DataArray(v.magnitude,
                   coords=dset['mwd'].coords,
                   attrs={'standard_name': 'y component direction',
                          'units': ''},
                   name='v')

    levels_period = np.arange(2, 14, 1)
    dset['u'] = u
    dset['v'] = v

    cmap = get_colormap("winds")
    cmap = truncate_colormap(cmap, 0.1, 1.0)

    _ = plt.figure(figsize=(figsize_x, figsize_y))

    ax  = plt.gca()
    m, x, y = get_projection(dset, projection, labels=True)
    m.fillcontinents(color='lightgray',lake_color='whitesmoke', zorder=0)

    dset = dset.drop(['lon', 'lat']).load()

    # All the arguments that need to be passed to the plotting function
    args=dict(x=x, y=y, ax=ax,
             levels_period=levels_period,
             cmap=cmap)


    print_message('Pre-processing finished, launching plotting scripts')
    if debug:
        plot_files(dset.isel(time=slice(0, 2)), **args)
    else:
        # Parallelize the plotting by dividing into chunks and processes
        dss = chunks_dataset(dset, chunks_size)
        plot_files_param = partial(plot_files, **args)
        p = Pool(processes)
        p.map(plot_files_param, dss)


def plot_files(dss, **args):
    first = True
    for time_sel in dss.time:
        data = dss.sel(time=time_sel)
        time, run, cum_hour = get_time_run_cum(data)
        # Build the name of the output image
        filename = subfolder_images[projection] + '/' + variable_name + '_%s.png' % cum_hour

        cs = args['ax'].contourf(args['x'], args['y'], data['mwp'],
                         extend='both', cmap=args['cmap'],
                         levels=args['levels_period'])


        # We need to reduce the number of points before plotting the vectors,
        # these values work pretty well
        if projection == 'euratl':
            density = 10
            scale = 600
        elif projection =='it':
            density = 5
            scale = 500
        elif projection =='adr':
            density = 3
            scale = 500
        elif projection =='moc':
            density = 8
            scale = 500
        elif projection =='lig':
            density = 2
            scale = 400
        elif projection =='tir':
            density = 3
            scale = 400
        elif projection =='jon':
            density = 4
            scale = 400
        elif projection =='mor':
            density = 6
            scale = 500

        cv = args['ax'].quiver(args['x'][::density, ::density],
                               args['y'][::density, ::density],
                               data['u'][::density, ::density],
                               data['v'][::density, ::density],
                               alpha=0.5, color='gray', scale=scale)


        an_fc = annotation_forecast(args['ax'], time)
        an_var = annotation(args['ax'], 'Wave period and direction',
            loc='lower left', fontsize=6)
        an_run = annotation_run(args['ax'], run)
        logo = add_logo_on_map(ax=args['ax'],
                                zoom=0.1, pos=(0.95, 0.08))

        if first:
            plt.colorbar(cs, orientation='horizontal', label='Wave period [s]',
                pad=0.03, fraction=0.03)
        
        if debug:
            plt.show(block=True)
        else:
            plt.savefig(filename, **options_savefig)        
        
        remove_collections([cs, an_fc, an_var, an_run, cv, logo])

        first = False 


if __name__ == "__main__":
    import time
    start_time=time.time()
    main()
    elapsed_time=time.time()-start_time
    print_message("script took " + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))

