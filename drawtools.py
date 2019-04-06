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

# Mainly comes from selectTools.py from Cadre de Permanence by Mederic Ribreux

from __future__ import print_function
from builtins import str
from builtins import range

from qgis.gui import QgsMapTool, QgsRubberBand, QgsMapToolEmitPoint, \
    QgsProjectionSelectionDialog
from qgis.core import QgsWkbTypes, QgsPointXY

from qgis.PyQt.QtCore import Qt, QCoreApplication, pyqtSignal, QPoint
from qgis.PyQt.QtWidgets import QDialog, QLineEdit, QDialogButtonBox, \
    QGridLayout, QLabel, QGroupBox, QVBoxLayout, QComboBox, QPushButton, \
    QInputDialog
from qgis.PyQt.QtGui import QDoubleValidator, QIntValidator, QKeySequence

from math import sqrt, pi, cos, sin


class DrawRect(QgsMapTool):
    '''Classe de sélection avec un Rectangle'''

    selectionDone = pyqtSignal()
    move = pyqtSignal()

    def __init__(self, iface, couleur):
        self.canvas = iface.mapCanvas()
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.iface = iface
        self.rb = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rb.setColor(couleur)
        self.reset()
        return None

    def reset(self):
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.rb.reset(True)	 # true, its a polygon

    def canvasPressEvent(self, e):
        if not e.button() == Qt.LeftButton:
            return
        self.startPoint = self.toMapCoordinates(e.pos())
        self.endPoint = self.startPoint
        self.isEmittingPoint = True

    def canvasReleaseEvent(self, e):
        self.isEmittingPoint = False
        if not e.button() == Qt.LeftButton:
            return None
        if self.rb.numberOfVertices() > 3:
            self.selectionDone.emit()
        else:
            width, height, ok = RectangleDialog().getSize()
            if width > 0 and height > 0 and ok:
                self.rb.addPoint(
                    QgsPointXY(
                        self.startPoint.x() + width,
                        self.startPoint.y() - height))
                self.showRect(
                    self.startPoint,
                    QgsPointXY(
                        self.startPoint.x() + width,
                        self.startPoint.y() - height))
                self.selectionDone.emit()

    def canvasMoveEvent(self, e):
        if not self.isEmittingPoint:
            return
        self.move.emit()
        self.endPoint = self.toMapCoordinates(e.pos())
        self.showRect(self.startPoint, self.endPoint)

    def showRect(self, startPoint, endPoint):
        self.rb.reset(QgsWkbTypes.PolygonGeometry)  # true, it's a polygon
        if startPoint.x() == endPoint.x() or startPoint.y() == endPoint.y():
            return

        point1 = QgsPointXY(startPoint.x(), startPoint.y())
        point2 = QgsPointXY(startPoint.x(), endPoint.y())
        point3 = QgsPointXY(endPoint.x(), endPoint.y())
        point4 = QgsPointXY(endPoint.x(), startPoint.y())

        self.rb.addPoint(point1, False)
        self.rb.addPoint(point2, False)
        self.rb.addPoint(point3, False)
        self.rb.addPoint(point4, True)  # true to update canvas
        self.rb.show()

    def deactivate(self):
        self.rb.reset(True)
        QgsMapTool.deactivate(self)


class RectangleDialog(QDialog):
    crs = None

    def __init__(self):
        QDialog.__init__(self)

        self.setWindowTitle(tr('Rectangle size'))

        self.width = QLineEdit()
        self.height = QLineEdit()

        width_val = QDoubleValidator()
        height_val = QDoubleValidator()

        self.width.setValidator(width_val)
        self.height.setValidator(height_val)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        grid = QGridLayout()
        grid.addWidget(QLabel(tr('Give a size in m:')), 0, 0)
        grid.addWidget(QLabel(tr('Width:')), 1, 0)
        grid.addWidget(QLabel(tr('Height:')), 1, 1)
        grid.addWidget(self.width, 2, 0)
        grid.addWidget(self.height, 2, 1)
        grid.addWidget(buttons, 3, 0, 1, 2)

        self.setLayout(grid)

    def getSize(self):
        dialog = RectangleDialog()
        result = dialog.exec_()

        width = 0
        height = 0
        if dialog.width.text().strip() and dialog.height.text().strip():
            width = float(dialog.width.text())
            height = float(dialog.height.text())
        return (width, height, result == QDialog.Accepted)


class DrawPolygon(QgsMapTool):
    '''Outil de sélection par polygone, tiré de selectPlusFr'''

    selectionDone = pyqtSignal()
    move = pyqtSignal()

    def __init__(self, iface, couleur):
        canvas = iface.mapCanvas()
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.iface = iface
        self.status = 0
        self.rb = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rb.setColor(couleur)
        return None

    def keyPressEvent(self, e):
        if e.matches(QKeySequence.Undo):
            if self.rb.numberOfVertices() > 1:
                self.rb.removeLastPoint()

    def canvasPressEvent(self, e):
        if e.button() == Qt.LeftButton:
            if self.status == 0:
                self.rb.reset(QgsWkbTypes.PolygonGeometry)
                self.status = 1
            self.rb.addPoint(self.toMapCoordinates(e.pos()))
        else:
            if self.rb.numberOfVertices() > 2:
                self.status = 0
                self.selectionDone.emit()
            else:
                self.reset()
        return None

    def canvasMoveEvent(self, e):
        if self.rb.numberOfVertices() > 0 and self.status == 1:
            self.rb.removeLastPoint(0)
            self.rb.addPoint(self.toMapCoordinates(e.pos()))
        self.move.emit()
        return None

    def reset(self):
        self.status = 0
        self.rb.reset(True)

    def deactivate(self):
        self.rb.reset(True)
        QgsMapTool.deactivate(self)


class DrawCircle(QgsMapTool):
    '''Outil de sélection par cercle, tiré de selectPlusFr'''

    selectionDone = pyqtSignal()
    move = pyqtSignal()

    def __init__(self, iface, color, segments):
        canvas = iface.mapCanvas()
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.iface = iface
        self.status = 0
        self.segments = segments
        self.rb = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rb.setColor(color)
        return None

    def canvasPressEvent(self, e):
        if not e.button() == Qt.LeftButton:
            return
        self.status = 1
        self.center = self.toMapCoordinates(e.pos())
        rbcircle(self.rb, self.center, self.center, self.segments)
        return

    def canvasMoveEvent(self, e):
        if not self.status == 1:
            return
        # construct a circle with N segments
        cp = self.toMapCoordinates(e.pos())
        rbcircle(self.rb, self.center, cp, self.segments)
        self.rb.show()
        self.move.emit()

    def canvasReleaseEvent(self, e):
        '''La sélection est faîte'''
        if not e.button() == Qt.LeftButton:
            return None
        self.status = 0
        if self.rb.numberOfVertices() > 3:
            self.selectionDone.emit()
        else:
            radius, ok = QInputDialog.getDouble(
                self.iface.mainWindow(), tr('Radius'),
                tr('Give a radius in m:'), min=0)
            if radius > 0 and ok:
                cp = self.toMapCoordinates(e.pos())
                cp.setX(cp.x() + radius)
                rbcircle(self.rb, self.toMapCoordinates(
                    e.pos()), cp, self.segments)
                self.rb.show()
                self.selectionDone.emit()
        return None

    def reset(self):
        self.status = 0
        self.rb.reset(True)

    def deactivate(self):
        self.rb.reset(True)
        QgsMapTool.deactivate(self)


def rbcircle(rb, center, edgePoint, N):
    '''Fonction qui affiche une rubberband sous forme de cercle'''
    r = sqrt(center.sqrDist(edgePoint))
    rb.reset(QgsWkbTypes.PolygonGeometry)
    for itheta in range(N + 1):
        theta = itheta * (2.0 * pi / N)
        rb.addPoint(QgsPointXY(center.x() + r * cos(theta),
                               center.y() + r * sin(theta)))
    return


class DrawLine(QgsMapTool):
    selectionDone = pyqtSignal()
    move = pyqtSignal()

    def __init__(self, iface, couleur):
        canvas = iface.mapCanvas()
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.iface = iface
        self.status = 0
        self.rb = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.rb.setColor(couleur)
        return None

    def keyPressEvent(self, e):
        if e.matches(QKeySequence.Undo):
            if self.rb.numberOfVertices() > 1:
                self.rb.removeLastPoint()

    def canvasPressEvent(self, e):
        if e.button() == Qt.LeftButton:
            if self.status == 0:
                self.rb.reset(QgsWkbTypes.LineGeometry)
                self.status = 1
            self.rb.addPoint(self.toMapCoordinates(e.pos()))
        else:
            if self.rb.numberOfVertices() > 2:
                self.status = 0
                self.selectionDone.emit()
            else:
                self.reset()
        return None

    def canvasMoveEvent(self, e):
        if self.rb.numberOfVertices() > 0 and self.status == 1:
            self.rb.removeLastPoint(0)
            self.rb.addPoint(self.toMapCoordinates(e.pos()))
        self.move.emit()
        return None

    def reset(self):
        self.status = 0
        self.rb.reset(QgsWkbTypes.LineGeometry)

    def deactivate(self):
        self.rb.reset(QgsWkbTypes.LineGeometry)
        QgsMapTool.deactivate(self)


class DrawPoint(QgsMapTool):
    selectionDone = pyqtSignal()

    def __init__(self, iface, couleur):
        canvas = iface.mapCanvas()
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.iface = iface
        self.rb = QgsRubberBand(self.canvas, QgsWkbTypes.PointGeometry)
        self.rb.setColor(couleur)
        self.rb.setWidth(3)

    def canvasReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.rb.addPoint(self.toMapCoordinates(e.pos()))
            self.selectionDone.emit()

    def reset(self):
        self.rb.reset(QgsWkbTypes.PointGeometry)

    def deactivate(self):
        self.rb.reset(QgsWkbTypes.PointGeometry)
        QgsMapTool.deactivate(self)


class SelectPoint(QgsMapTool):
    select = pyqtSignal()
    selectionDone = pyqtSignal()

    def __init__(self, iface, couleur):
        canvas = iface.mapCanvas()
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.iface = iface
        self.rb = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rb.setColor(couleur)
        self.rbSelect = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        return None

    def canvasReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.rbSelect.reset(QgsWkbTypes.PolygonGeometry)
            cp = self.toMapCoordinates(
                QPoint(e.pos().x() - 5, e.pos().y() - 5))
            self.rbSelect.addPoint(cp)
            cp = self.toMapCoordinates(
                QPoint(e.pos().x() + 5, e.pos().y() - 5))
            self.rbSelect.addPoint(cp)
            cp = self.toMapCoordinates(
                QPoint(e.pos().x() + 5, e.pos().y() + 5))
            self.rbSelect.addPoint(cp)
            cp = self.toMapCoordinates(
                QPoint(e.pos().x() - 5, e.pos().y() + 5))
            self.rbSelect.addPoint(cp)
            self.select.emit()
        else:
            self.selectionDone.emit()
        return None

    def reset(self):
        self.rb.reset(QgsWkbTypes.PolygonGeometry)
        self.rbSelect.reset(QgsWkbTypes.PolygonGeometry)

    def deactivate(self):
        self.rb.reset(QgsWkbTypes.PolygonGeometry)
        self.rbSelect.reset(QgsWkbTypes.PolygonGeometry)
        QgsMapTool.deactivate(self)


def tr(message):
    return QCoreApplication.translate('Qdraw', message)


class DMSDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)

        self.setWindowTitle(tr('DMS Point Tool'))

        self.lat_D = QLineEdit()
        self.lat_M = QLineEdit()
        self.lat_S = QLineEdit()
        self.lat_DM = QLineEdit()
        self.lon_D = QLineEdit()
        self.lon_M = QLineEdit()
        self.lon_S = QLineEdit()
        self.lon_DM = QLineEdit()

        self.lat_M.textEdited.connect(self.lat_MS_edited)
        self.lat_S.textEdited.connect(self.lat_MS_edited)
        self.lat_DM.textEdited.connect(self.lat_DM_edited)
        self.lon_M.textEdited.connect(self.lon_MS_edited)
        self.lon_S.textEdited.connect(self.lon_MS_edited)
        self.lon_DM.textEdited.connect(self.lon_DM_edited)

        int_val = QIntValidator()
        int_val.setBottom(0)

        float_val = QDoubleValidator()
        float_val.setBottom(0)

        self.lat_D.setValidator(int_val)
        self.lat_M.setValidator(int_val)
        self.lat_S.setValidator(float_val)
        self.lat_DM.setValidator(float_val)

        self.lon_D.setValidator(int_val)
        self.lon_M.setValidator(int_val)
        self.lon_S.setValidator(float_val)
        self.lon_DM.setValidator(float_val)

        self.lat_NS = QComboBox()
        self.lat_NS.addItem("N")
        self.lat_NS.addItem("S")

        self.lon_EW = QComboBox()
        self.lon_EW.addItem("E")
        self.lon_EW.addItem("W")

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        lat_grp = QGroupBox(tr("Latitude"), self)
        lat_grp.setStyleSheet(
            "QGroupBox { font-weight: bold; color: #3c3c3c; } ")
        lat_grid = QGridLayout()
        lat_grid.addWidget(QLabel(tr("Degrees")), 0, 0)
        lat_grid.addWidget(QLabel(tr("Minutes")), 0, 1)
        lat_grid.addWidget(QLabel(tr("Seconds")), 0, 2)
        lat_grid.addWidget(QLabel(tr("Direction")), 0, 3)
        lat_grid.addWidget(self.lat_D, 1, 0)
        lat_grid.addWidget(self.lat_M, 1, 1)
        lat_grid.addWidget(self.lat_S, 1, 2)
        lat_grid.addWidget(self.lat_NS, 1, 3)
        lat_grid.addWidget(QLabel(tr("Decimal minutes")), 2, 1)
        lat_grid.addWidget(self.lat_DM, 3, 1, 1, 2)
        lat_grp.setLayout(lat_grid)

        lon_grp = QGroupBox(tr("Longitude"), self)
        lon_grp.setStyleSheet(
            "QGroupBox { font-weight: bold; color: #3c3c3c; } ")
        lon_grid = QGridLayout()
        lon_grid.addWidget(QLabel(tr("Degrees")), 0, 0)
        lon_grid.addWidget(QLabel(tr("Minutes")), 0, 1)
        lon_grid.addWidget(QLabel(tr("Seconds")), 0, 2)
        lon_grid.addWidget(QLabel(tr("Direction")), 0, 3)
        lon_grid.addWidget(self.lon_D, 1, 0)
        lon_grid.addWidget(self.lon_M, 1, 1)
        lon_grid.addWidget(self.lon_S, 1, 2)
        lon_grid.addWidget(self.lon_EW, 1, 3)
        lon_grid.addWidget(QLabel(tr("Decimal minutes")), 2, 1)
        lon_grid.addWidget(self.lon_DM, 3, 1, 1, 2)
        lon_grp.setLayout(lon_grid)

        vbox = QVBoxLayout()
        vbox.addWidget(lat_grp)
        vbox.addWidget(lon_grp)
        vbox.addWidget(buttons)

        self.setLayout(vbox)

    def getPoint(self):
        dialog = DMSDialog()
        result = dialog.exec_()

        latitude = 0
        longitude = 0
        if dialog.lat_D.text().strip() \
                and dialog.lat_M.text().strip() \
                and dialog.lat_S.text().strip() \
                and dialog.lon_D.text().strip() \
                and dialog.lon_M.text().strip() \
                and dialog.lon_S.text().strip():
            latitude = int(dialog.lat_D.text()) \
                + float(dialog.lat_M.text()) / 60 \
                + float(dialog.lat_S.text()) / 3600
            if dialog.lat_NS.currentIndex() == 1:
                latitude *= -1
            longitude = int(dialog.lon_D.text()) \
                + float(dialog.lon_M.text()) / 60 \
                + float(dialog.lon_S.text()) / 3600
            if dialog.lon_EW.currentIndex() == 1:
                longitude *= -1
        return (QgsPointXY(longitude, latitude), result == QDialog.Accepted)

    def lat_MS_edited(self):
        if self.lat_M.text().strip():
            M = int(self.lat_M.text())
        else:
            M = 0
        if self.lat_S.text().strip():
            S = float(self.lat_S.text())
        else:
            S = 0
        if M == 0 and S == 0:
            self.lat_DM.clear()
        else:
            self.lat_DM.setText(str(M + (S / 60)))

    def lat_DM_edited(self):
        if self.lat_DM.text().strip():
            DM = float(self.lat_DM.text())
            self.lat_M.setText(str(int(DM)))
            self.lat_S.setText(str((DM - int(DM)) * 60))
        else:
            self.lat_M.clear()
            self.lat_S.clear()

    def lon_MS_edited(self):
        if self.lon_M.text().strip():
            M = int(self.lon_M.text())
        else:
            M = 0
        if self.lon_S.text().strip():
            S = float(self.lon_S.text())
        else:
            S = 0
        if M == 0 and S == 0:
            self.lon_DM.clear()
        else:
            self.lon_DM.setText(str(M + (S / 60)))

    def lon_DM_edited(self):
        if self.lon_DM.text().strip():
            DM = float(self.lon_DM.text())
            self.lon_M.setText(str(int(DM)))
            self.lon_S.setText(str((DM - int(DM)) * 60))
        else:
            self.lon_M.clear()
            self.lon_S.clear()


class XYDialog(QDialog):
    crs = None

    def __init__(self):
        QDialog.__init__(self)

        self.setWindowTitle(tr('XY Point drawing tool'))

        self.X = QLineEdit()
        self.Y = QLineEdit()

        X_val = QDoubleValidator()
        Y_val = QDoubleValidator()

        self.X.setValidator(X_val)
        self.Y.setValidator(Y_val)

        self.crsButton = QPushButton("Projection")
        self.crsButton.clicked.connect(self.changeCRS)
        self.crsLabel = QLabel("")

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        grid = QGridLayout()
        grid.addWidget(QLabel("X"), 0, 0)
        grid.addWidget(QLabel("Y"), 0, 1)
        grid.addWidget(self.X, 1, 0)
        grid.addWidget(self.Y, 1, 1)
        grid.addWidget(self.crsButton, 2, 0)
        grid.addWidget(self.crsLabel, 2, 1)
        grid.addWidget(buttons, 3, 0, 1, 2)

        self.setLayout(grid)

    def changeCRS(self):
        projSelector = QgsProjectionSelectionDialog()
        projSelector.exec_()
        self.crs = projSelector.crs()
        self.crsLabel.setText(self.crs.authid())

    def getPoint(self, crs):
        # fix_print_with_import
        print(crs)
        dialog = XYDialog()
        dialog.crs = crs
        dialog.crsLabel.setText(crs.authid())
        result = dialog.exec_()

        X = 0
        Y = 0
        if dialog.X.text().strip() and dialog.Y.text().strip():
            X = float(dialog.X.text())
            Y = float(dialog.Y.text())
        return ([QgsPointXY(X, Y), dialog.crs], result == QDialog.Accepted)
