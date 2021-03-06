from matplotlib import pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.colors import BoundaryNorm
from matplotlib.cm import ScalarMappable
import numpy as np
import pandas as pd
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon
from shapely.prepared import prep
import fiona
from descartes import PolygonPatch
import matplotlib.colors as mcolors


class PlotSeattleChoropleth(object):
    '''
    Works... but messy.
    '''

    def __init__(self, shapefile_name, section_name):
        self.shapefile_name = shapefile_name
        self.section_name = section_name
        self._set_basemap()
        self._set_mapdata()

    def _set_colormap(self):
        c = mcolors.ColorConverter().to_rgb
        return self._make_colormap([c('greenyellow'), c('yellow'), 0.33,
                                    c('yellow'), c('orange'), 0.66,
                                    c('orange'), c('red')])

    def _make_colormap(self, seq):
        seq = [(None,) * 3, 0.0] + list(seq) + [1.0, (None,) * 3]
        cdict = {'red': [], 'green': [], 'blue': []}
        for i, item in enumerate(seq):
            if isinstance(item, float):
                r1, g1, b1 = seq[i - 1]
                r2, g2, b2 = seq[i + 1]
                cdict['red'].append([item, r1, r2])
                cdict['green'].append([item, g1, g2])
                cdict['blue'].append([item, b1, b2])
        return mcolors.LinearSegmentedColormap('CustomMap', cdict)

    def fit_data(self, data_df, beat_col='zone_beat', values_col='values'):
        self.df_map = self.df_map.merge(data_df, left_on='name',
                                        right_on=beat_col)
        self.df_map = self.df_map.drop(beat_col, axis=1)
        self.values_col = values_col

    def plot_map(self, title_name, cmap=None, figwidth=14,
                 bins=[0., 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.],
                 bin_labels=None, save_path=None):
        if cmap is None:
            cmap = self._set_colormap()
        self.df_map['bins'] = self.df_map[self.values_col].apply(self._get_bins, args=(bins,))
        if bin_labels is None:
            bin_labels = ["{0}%".format(100 * x) for x in bins]
        fig = plt.figure(figsize=(figwidth, figwidth * self.h / self.w))
        ax = fig.add_subplot(111, axisbg = 'w', frame_on = False)
        func = lambda x: PolygonPatch(x, ec='#111111', lw=.8, alpha=1.,
                                      zorder=4)
        self.df_map['patches'] = self.df_map['poly'].map(func)
        pc = PatchCollection(self.df_map['patches'], match_original=True)
        #cmap_rng = (self.df_map['bins'].values - min(bins)) / float(max(bins))
        #cmap_rng = (self.df_map['bins'].values - self.df_map['bins'].values.min())/ \
        #           (self.df_map['bins'].values.max() - float(self.df_map['bins'].values.min()))
        #cmap_list = [cmap(val) for val in cmap_rng]
        cmap_list = [cmap(val) for val in self.df_map[self.values_col].values]
        pc.set_facecolor(cmap_list)
        ax.add_collection(pc)
        self.map.drawmapscale(self.coords[0] + 0.08,
                              self.coords[1] + -0.01,
                              self.coords[0],
                              self.coords[1],
                              10.,
                              fontsize=16,
                              barstyle='fancy',
                              labelstyle='simple',
                              fillcolor1='w',
                              fillcolor2='#555555',
                              fontcolor='#555555',
                              zorder=5,
                              ax=ax)
        cbar = self._create_colorbar(cmap, ncolors=len(bin_labels) + 1,
                                     labels=bin_labels, shrink=0.5)
        cbar.ax.tick_params(labelsize=16)
        if title_name is not None:
            fig.suptitle(title_name, fontdict={'size':24, 'fontweight':'bold'},
                         y=0.92)
        if save_path is not None:
            plt.savefig(save_path, dpi=100, frameon=False, bbox_inches='tight', pad_inches=0.5)


    def _set_basemap(self):
        shp = fiona.open('{0}.shp'.format(self.shapefile_name))
        self.coords = shp.bounds
        shp.close()
        self.w, self.h = self.coords[2] - self.coords[0], self.coords[3] - self.coords[1]
        extra = 0.01
        self.map = Basemap(projection = 'tmerc', ellps = 'WGS84',
                           lon_0 = np.mean([self.coords[0], self.coords[2]]),
                           lat_0 = np.mean([self.coords[1], self.coords[3]]),
                           llcrnrlon = self.coords[0] - extra * self.w,
                           llcrnrlat = self.coords[1] - (extra * self.h), 
                           urcrnrlon = self.coords[2] + extra * self.w,
                           urcrnrlat = self.coords[3] + (extra * self.h),
                           resolution = 'i',
                           suppress_ticks = True)
        _out = self.map.readshapefile(self.shapefile_name, name='seattle',
                                          drawbounds=False, color='none',
                                          zorder=2)

    def _set_mapdata(self):
        self.df_map = pd.DataFrame({
            'poly': [Polygon(points) for points in self.map.seattle],
            'name': [hood[self.section_name] for hood in self.map.seattle_info]
        })

        self.hood_polygons = prep(MultiPolygon(list(self.df_map['poly'].values)))

    def _get_bins(self, value, bins):
        #for i in xrange(len(bins) - 1):
        #    if value > bins[i] and value <= bins[i + 1]:
        #        return i
        #return -1
        fraction = 1. / (len(bins) - 1)
        for i in xrange(1, len(bins)):
            if value > bins[i - 1] and value <= bins[i]:
                return (i - 1) * fraction
        return 0

    def _create_colorbar(self, cmap, ncolors, labels, **kwargs):    
        norm = BoundaryNorm(range(0, ncolors), cmap.N)
        mappable = ScalarMappable(cmap=cmap, norm=norm)
        mappable.set_array([])
        mappable.set_clim(-0.5, ncolors+0.5)
        colorbar = plt.colorbar(mappable, **kwargs)
        colorbar.set_ticks(np.linspace(0, ncolors, ncolors+1)+0.5)
        colorbar.set_ticklabels(range(0, ncolors))
        colorbar.set_ticklabels(labels)
        return colorbar