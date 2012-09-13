# -*- coding: utf-8 -*-
# This file is part of pygal
#
# A python svg graph plotting library
# Copyright © 2012 Kozea
#
# This library is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with pygal. If not, see <http://www.gnu.org/licenses/>.
"""
Base for pygal charts

"""

from __future__ import division
from pygal.view import Margin, Box
from pygal.serie import Value
from pygal.util import (
    get_text_box, get_texts_box, cut, rad, humanize, truncate)
from pygal.svg import Svg
from pygal.util import cached_property
from math import sin, cos, sqrt


class BaseGraph(object):
    """Graphs commons"""

    __value__ = Value

    def __init__(self, config, series):
        """Init the graph"""
        self.config = config
        self.series = series
        self.horizontal = getattr(self, 'horizontal', False)
        self.svg = Svg(self)
        self._x_labels = None
        self._y_labels = None
        self.nodes = {}
        self.margin = Margin(*([20] * 4))
        self._box = Box()
        self.view = None

    def __getattr__(self, attr):
        """Search in config, then in self"""
        if attr in dir(self.config):
            return object.__getattribute__(self.config, attr)
        return object.__getattribute__(self, attr)

    @property
    def _format(self):
        """Return the value formatter for this graph"""
        return humanize if self.human_readable else str

    def _compute(self):
        """Initial computations to draw the graph"""

    def _plot(self):
        """Actual plotting of the graph"""

    def _compute_margin(self):
        """Compute graph margins from set texts"""
        if self.show_legend:
            h, w = get_texts_box(
                map(lambda x: truncate(x, self.truncate_legend or 15),
                    cut(self.series, 'title')),
                self.legend_font_size)
            if self.legend_at_bottom:
                h_max = max(h, self.legend_box_size)
                self.margin.bottom += 10 + h_max * round(
                    sqrt(len(self.series)) - 1) * 1.5 + h_max
            else:
                self.margin.right += 10 + w + self.legend_box_size

        if self.title:
            h, w = get_text_box(self.title, self.title_font_size)
            self.margin.top += 10 + h

        if self._x_labels:
            h, w = get_texts_box(
                cut(self._x_labels), self.label_font_size)
            self._x_labels_height = 10 + max(
                w * sin(rad(self.x_label_rotation)), h)
            self.margin.bottom += self._x_labels_height
            if self.x_label_rotation:
                self.margin.right = max(
                    w * cos(rad(self.x_label_rotation)),
                    self.margin.right)
        else:
            self._x_labels_height = 0
        if self._y_labels:
            h, w = get_texts_box(
                cut(self._y_labels), self.label_font_size)
            self.margin.left += 10 + max(
                w * cos(rad(self.y_label_rotation)), h)

    @cached_property
    def _legends(self):
        """Getter for series title"""
        return [serie.title for serie in self.series]

    @cached_property
    def _values(self):
        """Getter for series values (flattened)"""
        return [val
                for serie in self.series
                for val in serie.values
                if val is not None]

    @cached_property
    def _len(self):
        """Getter for the maximum series size"""
        return max([len(serie.values) for serie in self.series])

    @cached_property
    def _min(self):
        """Getter for the minimum series value"""
        return (self.range and self.range[0]) or min(self._values)

    @cached_property
    def _max(self):
        """Getter for the maximum series value"""
        return (self.range and self.range[1]) or max(self._values)

    def _draw(self):
        """Draw all the things"""
        self._prepare_data()
        self._compute()
        self._compute_margin()
        self._decorate()
        self._plot()

    def _has_data(self):
        """Check if there is any data"""
        if len(self.series) == 0:
            return False
        if sum(map(len, map(lambda s: s.values, self.series))) == 0:
            return False
        return True

    def _prepare_data(self):
        """Remove aberrant values"""
        if self.logarithmic:
            for serie in self.series:
                for metadata in serie.metadata:
                    if metadata.value <= 0:
                        metadata.value = None

    def _uniformize_data(self):
        """Make all series to max len"""
        for serie in self.series:
            if len(serie.values) < self._len:
                diff = self._len - len(serie.values)
                serie.metadata += diff * [self.__value__(0)]

            for metadata in serie.metadata:
                if metadata.value is None:
                    metadata.value = 0

    def _render(self):
        """Make the graph internally"""
        if self._has_data():
            self._draw()
            self.svg.pre_render(False)
        else:
            self.svg.pre_render(True)

    def render(self, is_unicode):
        """Render the graph, and return the svg string"""
        self._render()
        return self.svg.render(
            is_unicode=is_unicode, pretty_print=self.pretty_print)

    def render_tree(self):
        """Render the graph, and return lxml tree"""
        self._render()
        return self.svg.root
