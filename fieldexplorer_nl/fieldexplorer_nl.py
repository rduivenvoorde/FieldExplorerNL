# -*- coding: utf-8 -*-
# -----------------------------------------------------------
# Copyright (C) 2020 Richard Duivenvoorde richard@zuidt.nl
# -----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# ---------------------------------------------------------------------

from qgis.PyQt.QtGui import (
    QIcon,
)
from qgis.PyQt.QtWidgets import (
    QAction,
    QMessageBox,
)
from qgis.core import (
    Qgis,
    QgsMapLayer,
    QgsMessageLog,
    QgsRectangle,
)

import os
import inspect
import csv


class FieldExplorerNl(object):

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = iface.mapCanvas()

    def initGui(self):
        # Create action that will start plugin
        current_directory = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.action = QAction(QIcon(os.path.join(current_directory, "icons", "phenokey.png")), "Create CSV", self.iface.mainWindow())
        self.action_info = QAction(QIcon(os.path.join(current_directory, "icons", "phenokey.png")), "FieldExplorer Info", self.iface.mainWindow())

        # connect the action to the work/run method
        self.action.triggered.connect(self.run)
        help_txt = """Info
This plugin ....
"""
        self.action_info.triggered.connect(lambda: self.show_message(help_txt))

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu("FieldExplorer NL", self.action)
        self.iface.addPluginToVectorMenu("FieldExplorer NL", self.action_info)


    def unload(self):
        # Remove the plugin menu item and toolbar button
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginVectorMenu("FieldExplorer NL", self.action)
        self.iface.removePluginVectorMenu("FieldExplorer NL", self.action_info)

    def run(self):
        self.write_csv()

    def show_message(self, information):
        QMessageBox.information(self.iface.mainWindow(), \
                                "FieldExplorer NL", information)

    def write_csv(self):
        layer = self.iface.activeLayer()

        if layer.type() != QgsMapLayer.VectorLayer:
            self.show_message('The active layer "{}" is NOT a vector layer containing plot data.\nPlease make a polygon layer active in the layermanager.'
                              .format(layer.name()))
            return

        reply = QMessageBox.question(self.iface.mainWindow(), 'FieldExplorer NL',
                                     'Save current active layer "{}" to FieldExplorer CSV?'
                                     .format(layer.name()),
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.Yes)
        if reply == QMessageBox.No:
            return

        layer_path = layer.dataProvider().dataSourceUri()
        (directory, file_name) = os.path.split(layer_path)
        file_name = file_name.split('|')[0]
        self.log('Starting to write "{}" ({} in {}) to FieldExplorer NL CSV'
                 .format(layer.name(), file_name, directory))

        (directory, file_name) = os.path.split(layer_path)
        file_name = file_name.split('|')[0]
        csv_name = os.path.splitext(file_name)[0] + '.csv'
        csv_file = os.path.join(directory, csv_name)

        # check if dir is writable
        if not os.access(directory, os.W_OK):  # W_OK is for writing, R_OK for reading
            self.show_message('The data directory "{}"\nis not writable, will not be able to write a csv there.'
                              .format(directory))
            return

        # check if layer's crs = epsg:4326
        if 'EPSG:4326' != layer.crs().authid():
            self.show_message('The layer should have EPSG:4326 as crs, but is: "{}".\nPlease provide a layer in EPSG:4326 (lat lon coordinates).'
                              .format(layer.crs().authid()))
            return

        # or coordinates within  2,50.0 : 8.0,55 (NL))
        layer_extent = layer.extent()
        nl_extent = QgsRectangle(2, 50.0, 8.0, 55)
        if not nl_extent.contains(layer_extent):
            self.show_message('The data/layer extent: "{}" is not within The Netherlands.\nPlease provide data within {}.'
                              .format(layer_extent, nl_extent))
            return

        # check if polygons touch (should NOT)



        features = layer.getFeatures()
        attributes = layer.fields().names()
        if not ('Plot-ID' in attributes and 'Comments' in attributes):
            self.show_message('The data should contain both an "Plot-ID" and a "Comments" attribute.\nAvailable attributes: {}'
                              .format(attributes))
            return

        with open(csv_file, 'w', newline='') as f:
            # QUOTE_NONNUMERIC, QUOTE_MINIMAL
            csv_writer = csv.writer(f, delimiter=',', quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)
            # header
            csv_writer.writerow(('Plot-ID', 'A(LAT)', 'A(LONG)', 'B(LAT)', 'B(LONG)',
                                 'C(LAT)', 'C(LONG)', 'D(LAT)', 'D(LONG)', 'Comments'))
            for feature in features:
                geom = feature.geometry()
                # force singletype (so both multi and single will work)
                if not geom.convertToSingleType():
                    self.show_message('Cannot convert feature {} to a single polygon.'
                                      .format(feature.attributes()))
                    return

                # force clockwise direction!
                geom.forceRHR()

                coordinates = []
                for vertex in geom.vertices():
                    coordinates.append(vertex)

                # check if just 5
                if len(coordinates) > 5:
                    self.show_message(
                        'The feature {} contains too many vertices,\nthere should be just 4, but has: {}'
                        .format(feature.attributes(), len(coordinates)-1))
                    return

                row = []
                row.append(feature['Plot-ID'])
                for coord in coordinates[:-1]:
                    row.append(coord.y())
                    row.append(coord.x())
                if 'Comments' in attributes:
                    row.append(feature['Comments'])
                csv_writer.writerow(row)
        # OK, done!
        self.iface.messageBar().pushMessage('Done!',
                                       'Succesfully wrote FieldExplorer CSV file to:\n{}'.format(csv_file),
                                       level=Qgis.Info, duration=15)

    def log(self, log_text):
        QgsMessageLog.logMessage('{}'.format(log_text), 'FieldExplorer NL', Qgis.Info)


