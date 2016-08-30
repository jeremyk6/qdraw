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
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Mainly comes from selectTools.py from Cadre de Permanence by Mederic Ribreux

from qgis.core import *
from qgis.gui import *
from math import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class drawRect(QgsMapTool):
  '''Classe de sélection avec un Rectangle'''
  def __init__(self, iface, couleur):
      self.canvas = iface.mapCanvas()
      QgsMapToolEmitPoint.__init__(self, self.canvas)
      self.iface = iface
      self.rb=QgsRubberBand(self.canvas,QGis.Polygon)
      self.rb.setColor( couleur )
      self.reset()
      return None

  def reset(self):
      self.startPoint = self.endPoint = None
      self.isEmittingPoint = False
      self.rb.reset( True )	# true, its a polygon

  def canvasPressEvent(self, e):
      if not e.button() == Qt.LeftButton:
          return
      self.startPoint = self.toMapCoordinates( e.pos() )
      self.endPoint = self.startPoint
      self.isEmittingPoint = True

  def canvasReleaseEvent(self, e):
      self.isEmittingPoint = False
      if not e.button() == Qt.LeftButton:
          return None
      if self.rb.numberOfVertices() > 3:
        self.emit( SIGNAL("selectionDone()") )
      return None

  def canvasMoveEvent(self, e):
      if not self.isEmittingPoint:
        return
      self.endPoint = self.toMapCoordinates( e.pos() )
      self.showRect(self.startPoint, self.endPoint)

  def showRect(self, startPoint, endPoint):
      self.rb.reset(QGis.Polygon)	# true, it's a polygon
      if startPoint.x() == endPoint.x() or startPoint.y() == endPoint.y():
        return

      point1 = QgsPoint(startPoint.x(), startPoint.y())
      point2 = QgsPoint(startPoint.x(), endPoint.y())
      point3 = QgsPoint(endPoint.x(), endPoint.y())
      point4 = QgsPoint(endPoint.x(), startPoint.y())

      self.rb.addPoint( point1, False )
      self.rb.addPoint( point2, False )
      self.rb.addPoint( point3, False )
      self.rb.addPoint( point4, True  )	# true to update canvas
      self.rb.show()

  def deactivate(self):
      self.rb.reset( True )
      QgsMapTool.deactivate(self)

class drawPolygon(QgsMapTool):
  '''Outil de sélection par polygone, tiré de selectPlusFr'''
  def __init__(self,iface, couleur):
      canvas = iface.mapCanvas()
      QgsMapTool.__init__(self,canvas)
      self.canvas = canvas
      self.iface = iface
      self.status = 0
      self.rb=QgsRubberBand(self.canvas,QGis.Polygon)
      self.rb.setColor( couleur )
      return None
      
  def keyPressEvent(self, e):
      if e.matches(QKeySequence.Undo):
         if self.rb.numberOfVertices() > 1:
           self.rb.removeLastPoint()

  def canvasPressEvent(self,e):
      if e.button() == Qt.LeftButton:
         if self.status == 0:
           self.rb.reset( QGis.Polygon )
           self.status = 1
         self.rb.addPoint(self.toMapCoordinates(e.pos()))
      else:
         if self.rb.numberOfVertices() > 2:
           self.status = 0
           self.emit( SIGNAL("selectionDone()") )
         else:
           self.reset()
      return None
    
  def canvasMoveEvent(self,e):
      if self.rb.numberOfVertices() > 0 and self.status == 1:
          self.rb.removeLastPoint(0)
          self.rb.addPoint(self.toMapCoordinates(e.pos()))
      return None

  def reset(self):
      self.status = 0
      self.rb.reset( True )

  def deactivate(self):
    self.rb.reset( True )
    QgsMapTool.deactivate(self)

class drawCircle(QgsMapTool):
  '''Outil de sélection par cercle, tiré de selectPlusFr'''
  def __init__(self,iface, color, segments):
      canvas = iface.mapCanvas()
      QgsMapTool.__init__(self,canvas)
      self.canvas = canvas
      self.iface = iface
      self.status = 0
      self.segments = segments
      self.rb=QgsRubberBand(self.canvas, QGis.Polygon)
      self.rb.setColor( color )
      return None

  def canvasPressEvent(self,e):
      if not e.button() == Qt.LeftButton:
          return
      self.status = 1
      self.center = self.toMapCoordinates(e.pos())
      rbcircle(self.rb, self.center, self.center, self.segments)
      return
    
  def canvasMoveEvent(self,e):
      if not self.status == 1:
          return
      # construct a circle with N segments
      cp = self.toMapCoordinates(e.pos())
      rbcircle(self.rb, self.center, cp, self.segments)
      self.rb.show()

  def canvasReleaseEvent(self,e):
      '''La sélection est faîte'''
      if not e.button() == Qt.LeftButton:
          return None
      self.status = 0
      if self.rb.numberOfVertices() > 3:
        self.emit( SIGNAL("selectionDone()") )
      else:
        radius, ok = QInputDialog.getInt(self.iface.mainWindow(), tr('Radius'), tr('Give a radius in m:'), min=0)
        cp = self.toMapCoordinates(e.pos())
        cp.setX(cp.x()+radius)
        rbcircle(self.rb, self.toMapCoordinates(e.pos()), cp, self.segments)
        self.rb.show()
        self.emit( SIGNAL("selectionDone()") )
      return None

  def reset(self):
      self.status = 0
      self.rb.reset( True )

  def deactivate(self):
    self.rb.reset( True )
    QgsMapTool.deactivate(self)

def rbcircle(rb,center,edgePoint,N):
    '''Fonction qui affiche une rubberband sous forme de cercle'''
    r = sqrt(center.sqrDist(edgePoint))
    rb.reset( QGis.Polygon )
    for itheta in range(N+1):
        theta = itheta*(2.0 * pi/N)
        rb.addPoint(QgsPoint(center.x()+r*cos(theta),center.y()+r*sin(theta)))
    return 

class drawLine(QgsMapTool):
  def __init__(self,iface, couleur):
      canvas = iface.mapCanvas()
      QgsMapTool.__init__(self,canvas)
      self.canvas = canvas
      self.iface = iface
      self.status = 0
      self.rb=QgsRubberBand(self.canvas,QGis.Line)
      self.rb.setColor( couleur )
      return None

  def canvasPressEvent(self,e):
      if e.button() == Qt.LeftButton:
         if self.status == 0:
           self.rb.reset( QGis.Line )
           self.status = 1
         self.rb.addPoint(self.toMapCoordinates(e.pos()))
      else:
         if self.rb.numberOfVertices() > 2:
           self.status = 0
           self.emit( SIGNAL("selectionDone()") )
         else:
           self.reset()
      return None
    
  def canvasMoveEvent(self,e):
      if self.rb.numberOfVertices() > 0 and self.status == 1:
          self.rb.removeLastPoint(0)
          self.rb.addPoint(self.toMapCoordinates(e.pos()))
      return None

  def reset(self):
      self.status = 0
      self.rb.reset( QGis.Line )

  def deactivate(self):
    self.rb.reset( QGis.Line )
    QgsMapTool.deactivate(self)

class drawPoint(QgsMapTool):
  def __init__(self,iface, couleur):
      canvas = iface.mapCanvas()
      QgsMapTool.__init__(self,canvas)
      self.canvas = canvas
      self.iface = iface
      self.rb=QgsRubberBand(self.canvas,QGis.Point)
      self.rb.setColor( couleur )
      self.rb.setWidth(3)
      return None

  def canvasReleaseEvent(self,e):
      if e.button() == Qt.LeftButton:
         self.rb.addPoint(self.toMapCoordinates(e.pos()))
         self.emit( SIGNAL("selectionDone()") )
      return None

  def reset(self):
      self.rb.reset( QGis.Point )

  def deactivate(self):
    self.rb.reset( QGis.Point )
    QgsMapTool.deactivate(self)

class selectPoint(QgsMapTool):
  def __init__(self,iface, couleur):
      canvas = iface.mapCanvas()
      QgsMapTool.__init__(self,canvas)
      self.canvas = canvas
      self.iface = iface
      self.rb=QgsRubberBand(self.canvas,QGis.Polygon)
      self.rb.setColor( couleur )
      return None

  def canvasReleaseEvent(self,e):
      if e.button() == Qt.LeftButton:
         self.rb.reset( QGis.Polygon )
         cp = self.toMapCoordinates(QPoint(e.pos().x()-5, e.pos().y()-5))
         self.rb.addPoint(cp)
         cp = self.toMapCoordinates(QPoint(e.pos().x()+5, e.pos().y()-5))
         self.rb.addPoint(cp)
         cp = self.toMapCoordinates(QPoint(e.pos().x()+5, e.pos().y()+5))
         self.rb.addPoint(cp)
         cp = self.toMapCoordinates(QPoint(e.pos().x()-5, e.pos().y()+5))
         self.rb.addPoint(cp)
         self.rb.show()
         self.emit( SIGNAL("selectionDone()") )
      return None

  def reset(self):
      self.rb.reset( QGis.Polygon )

  def deactivate(self):
    self.rb.reset( QGis.Polygon )
    QgsMapTool.deactivate(self)
 
class copyFeatures(QgsMapTool):
  def __init__(self,iface,color,layer):
      self.canvas = iface.mapCanvas()
      QgsMapTool.__init__(self, self.canvas)
      self.iface = iface
      self.rb = QgsRubberBand(self.canvas, QGis.Polygon)
      self.rb.setWidth(3)
      self.color = color
      self.rb.setColor( color )
      
      self.layer = layer
      
      self.geom = []
      
      return None

  def canvasReleaseEvent(self,e):
    if e.button() == Qt.LeftButton:
        point = self.toMapCoordinates(e.pos())
        geom = QgsGeometry()
        geom.addPart([point], QGis.Point)
        features = self.layer.getFeatures(QgsFeatureRequest(geom.boundingBox()))
        for feature in features:
            self.rb.addGeometry(feature.geometry(), self.layer)
            self.rb.show()
    else:
        self.emit( SIGNAL("selectionDone()"))

  def reset(self):
    self.rb.reset( QGis.Polygon )
    return
    
  def deactivate(self):
    self.rb.reset( QGis.Polygon )
    QgsMapTool.deactivate(self)
    return

def tr(message):
    return QCoreApplication.translate('Qdraw', message)
    
class DMSDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
    
        self.setWindowTitle(tr('DMS Point Tool'))
        
        self.lat_D = QLineEdit()
        self.lat_M = QLineEdit()
        self.lat_S = QLineEdit()
        self.lon_D = QLineEdit()
        self.lon_M = QLineEdit()
        self.lon_S = QLineEdit()
        
        int_val = QIntValidator()
        int_val.setBottom(0)
        
        float_val = QDoubleValidator()
        float_val.setBottom(0)
        
        self.lat_D.setValidator(int_val)
        self.lat_M.setValidator(int_val)
        self.lat_S.setValidator(float_val)
        
        self.lon_D.setValidator(int_val)
        self.lon_M.setValidator(int_val)
        self.lon_S.setValidator(float_val)
        
        self.lat_NS = QComboBox()
        self.lat_NS.addItem("N")
        self.lat_NS.addItem("S")
        
        self.lon_EW = QComboBox()
        self.lon_EW.addItem("E")
        self.lon_EW.addItem("W")
        
        buttons =   QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
       
        grid = QGridLayout()
        #grid.setContentsMargins(0,0,0,0)
        grid.addWidget(QLabel(tr("Latitude")),0,0)
        grid.addWidget(QLabel(tr("Degrees")),1,0)
        grid.addWidget(QLabel(tr("Minutes")),1,1)
        grid.addWidget(QLabel(tr("Seconds")),1,2)
        grid.addWidget(QLabel(tr("Direction")),1,3)
        grid.addWidget(self.lat_D,2,0)
        grid.addWidget(self.lat_M,2,1)
        grid.addWidget(self.lat_S,2,2)
        grid.addWidget(self.lat_NS,2,3)
        grid.addWidget(QLabel(tr("Longitude")),3,0)
        grid.addWidget(QLabel(tr("Degrees")),4,0)
        grid.addWidget(QLabel(tr("Minutes")),4,1)
        grid.addWidget(QLabel(tr("Seconds")),4,2)
        grid.addWidget(QLabel(tr("Direction")),4,3)
        grid.addWidget(self.lon_D,5,0)
        grid.addWidget(self.lon_M,5,1)
        grid.addWidget(self.lon_S,5,2) 
        grid.addWidget(self.lon_EW,5,3)         
        grid.addWidget(buttons,6,2,1,2)
        
        self.setLayout(grid)
        
    def getPoint(self):
        dialog = DMSDialog()
        result = dialog.exec_()
        
        latitude = 0
        longitude = 0
        if (dialog.lat_D.text().strip() and dialog.lat_M.text().strip() and dialog.lat_S.text().strip()
            and dialog.lon_D.text().strip() and dialog.lon_M.text().strip() and dialog.lon_S.text().strip()):
            latitude = int(dialog.lat_D.text())+ float(dialog.lat_M.text())/60 + float(dialog.lat_S.text())/3600
            if dialog.lat_NS.currentIndex() == 1:
                latitude *= -1
            longitude = int(dialog.lon_D.text())+ float(dialog.lon_M.text())/60 + float(dialog.lon_S.text())/3600  
            if dialog.lon_EW.currentIndex() == 1:
                longitude *= -1
        return (QgsPoint(longitude, latitude), result == QDialog.Accepted)