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

"""
 This script initializes the plugin, making it known to QGIS.
"""

from .fieldexplorer_nl import FieldExplorerNl

def classFactory(iface):
  return FieldExplorerNl(iface)
