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

from builtins import str
from qgis.PyQt.QtWidgets import QWidget, QPushButton, QSlider, QDesktopWidget,\
    QLabel, QColorDialog, QVBoxLayout
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt, QCoreApplication, pyqtSignal


class QdrawSettings(QWidget):
    """Window used to change settings (transparency/color)"""
    settingsChanged = pyqtSignal()

    def __init__(self):
        QWidget.__init__(self)

        self.setWindowTitle(self.tr('Qdraw - Settings'))
        self.setFixedSize(320, 100)
        self.center()

        # default color
        self.color = QColor(60, 151, 255, 255)

        self.sld_opacity = QSlider(Qt.Horizontal, self)
        self.sld_opacity.setRange(0, 255)
        self.sld_opacity.setValue(255)
        self.sld_opacity.tracking = True
        self.sld_opacity.valueChanged.connect(self.handler_opacitySliderValue)
        self.lbl_opacity = QLabel(self.tr('Opacity') + ': 100%', self)

        self.dlg_color = QColorDialog(self)
        btn_chColor = QPushButton(self.tr('Change the drawing color'), self)
        btn_chColor.clicked.connect(self.handler_chColor)

        vbox = QVBoxLayout()
        vbox.addWidget(self.lbl_opacity)
        vbox.addWidget(self.sld_opacity)
        vbox.addWidget(btn_chColor)
        self.setLayout(vbox)

    def tr(self, message):
        return QCoreApplication.translate('Qdraw', message)

    def handler_opacitySliderValue(self, val):
        self.color.setAlpha(val)
        self.lbl_opacity.setText(
            self.tr('Opacity')+': '+str(int((float(val) / 255) * 100))+'%')
        self.settingsChanged.emit()

    def handler_chColor(self):
        color = self.dlg_color.getColor(self.color)
        if color.isValid():
            color.setAlpha(self.color.alpha())
            self.color = color
            self.settingsChanged.emit()
            self.close()

    def getColor(self):
        return self.color

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

    def closeEvent(self, e):
        self.clear()
        e.accept()

    def clear(self):
        return
