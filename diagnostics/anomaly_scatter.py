# place your module imports here:
import logging

# operating system manipulations (e.g. path constructions)
import os

# to manipulate iris cubes
import iris
import matplotlib.pyplot as plt

# for pandas
import pandas as pd
import seaborn as sns

# import internal esmvaltool modules here
from esmvaltool.diag_scripts.shared import group_metadata, run_diagnostic

logger = logging.getLogger(os.path.basename(__file__))


def _plot_scatter(cfg, data_df):
    logger.info('Making the plot')
    local_path = cfg['plot_dir']

    # do some plotting
    fig, ax1 = plt.subplots(1, 1, layout="constrained", figsize=(10, 6))

    sns.scatterplot(data=data_df, x='pr', y='tas', ax=ax1)

    labels = []
    i = 1
    for k, v in data_df.iterrows():
        # labels
        l = f'{i} - {k}'
        labels.append(l)
        ax1.annotate(
            i,
            (v['pr'], v['tas']),
            xytext=(2.5, -2.5), textcoords='offset points',
            fontsize=8
        )
        i = i+1

    ax1.text(
        1.05, 1.0, '\n'.join(labels),
        transform=ax1.transAxes,
        ha='left',
        va='top'
    )

    ax1.set_title('tas and pr anomaly')
    png_name = 'scatter_plot.png'

    fig.savefig(os.path.join(local_path, png_name))
    plt.close(fig)


def process_data(cfg):
    """
    Arguments:
        cfg - nested dictionary of metadata

    Returns:
        string; runs the user diagnostic

    """
    # we want to read the data from the cfg files, and put values into a 
    # dataframe, arranged by model name / variable

    # first group the data by dataset
    my_files_dict = group_metadata(cfg['input_data'].values(), 'dataset')

    data = {}

    logger.info('Processing data')
    for key, value in my_files_dict.items():
        # process the data
        data[key] = {}

        for var in value:
            # load the data
            cube = iris.load_cube(var['filename'])
            
            # extract period of interest and mean
            cube = cube.extract(iris.Constraint(season_year=lambda y: cfg['period_start'] <= y <= cfg['period_end']))
            cube = cube.collapsed('time', iris.analysis.MEAN)
            
            # store the data
            if var['short_name'] == 'pr':
                # convert precip to mm/day
                d_val = cube.data.item() * 86400
            else:
                d_val = cube.data.item()
            data[key][var['short_name']] = d_val
            
    data_df = pd.DataFrame(data).transpose()
    
    # now make the plot
    _plot_scatter(cfg, data_df)


if __name__ == '__main__':
    # always use run_diagnostic() to get the config (the preprocessor
    # nested dictionary holding all the needed information)
    with run_diagnostic() as config:
        process_data(config)