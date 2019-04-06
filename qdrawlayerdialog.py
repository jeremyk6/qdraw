# -*- coding: utf-8 -*-

# QDraw: plugin that makes drawing easier
# Author: Jérémy Kalsron
#         jeremy.kalsron@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtWidgets import QDialog, QComboBox, QLineEdit, QVBoxLayout, \
    QCheckBox, QDialogButtonBox, QLabel
from qgis.core import QgsProject


class QDrawLayerDialog(QDialog):
    def __init__(self, iface, gtype):
        QDialog.__init__(self)

        self.setWindowTitle(self.tr('Drawing'))

        self.name = QLineEdit()

        if gtype == 'point' or gtype == 'XYpoint':
            gtype = 'Point'
        elif gtype == 'line':
            gtype = 'LineString'
        else:
            gtype = 'Polygon'

        # change here by QgsMapLayerComboBox()
        self.layerBox = QComboBox()
        self.layers = []
        for layer in QgsProject.instance().mapLayers().values():
            if layer.providerType() == "memory":
                # ligne suivante à remplacer par if layer.geometryType() == :
                if gtype in layer.dataProvider().dataSourceUri()[:26]: #  must be of the same type of the draw
                    if 'field='+self.tr('Drawings')+':string(255,0)' in layer.dataProvider().dataSourceUri()[-28:]: # must have its first field named Drawings, string type
                        self.layers.append(layer)
                        self.layerBox.addItem(layer.name())

        self.addLayer = QCheckBox(self.tr('Add to an existing layer'))
        self.addLayer.toggled.connect(self.addLayerChecked)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        vbox = QVBoxLayout()
        vbox.addWidget(QLabel(self.tr("Give a name to the feature:")))
        vbox.addWidget(self.name)
        vbox.addWidget(self.addLayer)
        vbox.addWidget(self.layerBox)
        if len(self.layers) == 0:
            self.addLayer.setEnabled(False)
            self.layerBox.setEnabled(False)
        vbox.addWidget(buttons)
        self.setLayout(vbox)

        self.layerBox.setEnabled(False)
        self.name.setFocus()

    def tr(self, message):
        return QCoreApplication.translate('Qdraw', message)

    def addLayerChecked(self):
        if self.addLayer.checkState() == Qt.Checked:
            self.layerBox.setEnabled(True)
        else:
            self.layerBox.setEnabled(False)

    def getName(self, iface, gtype):
        dialog = QDrawLayerDialog(iface, gtype)
        result = dialog.exec_()
        return (
            dialog.name.text(),
            dialog.addLayer.checkState() == Qt.Checked,
            dialog.layerBox.currentIndex(),
            dialog.layers,
            result == QDialog.Accepted)
