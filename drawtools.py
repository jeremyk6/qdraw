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
      sb = self.iface.mainWindow().statusBar()
      sb.showMessage(u"Dessiner un rectangle")
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
      sb = self.iface.mainWindow().statusBar()
      sb.showMessage(u"Clic gauche pour poser des points, clic droit pour terminer la saisie")
      return None

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
      sb = self.iface.mainWindow().statusBar()
      sb.showMessage(u"Placer le centre et déplacer le curseur de la souris pour fixer le rayon")
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
      r = sqrt(self.center.sqrDist(cp))
      sb = self.iface.mainWindow().statusBar()
      sb.showMessage(u"Centre: X=%s Y=%s, RAYON: %s m" % (str(self.center.x()),str(self.center.y()),str(r)))
      self.rb.show()

  def canvasReleaseEvent(self,e):
      '''La sélection est faîte'''
      if not e.button() == Qt.LeftButton:
          return None
      self.status = 0
      if self.rb.numberOfVertices() > 3:
        self.emit( SIGNAL("selectionDone()") )
      else:
        radius, ok = QInputDialog.getInt(self.iface.mainWindow(), 'Rayon', u'Entrez un rayon en m:', min=0)
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
      sb = self.iface.mainWindow().statusBar()
      sb.showMessage(u"Clic gauche pour poser des points, clic droit pour terminer la saisie")
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

class drawPoint(QgsMapTool):
  def __init__(self,iface, couleur):
      canvas = iface.mapCanvas()
      QgsMapTool.__init__(self,canvas)
      self.canvas = canvas
      self.iface = iface
      self.rb=QgsRubberBand(self.canvas,QGis.Point)
      self.rb.setColor( couleur )
      self.rb.setWidth(3)
      sb = self.iface.mainWindow().statusBar()
      sb.showMessage(u"Clic gauche pour poser un point")
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

class selectPoint(QgsMapTool):
  def __init__(self,iface, couleur):
      canvas = iface.mapCanvas()
      QgsMapTool.__init__(self,canvas)
      self.canvas = canvas
      self.iface = iface
      self.rb=QgsRubberBand(self.canvas,QGis.Polygon)
      self.rb.setColor( couleur )
      sb = self.iface.mainWindow().statusBar()
      sb.showMessage(u"clic gauche pour poser un point")
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
 
class copyFeatures(QgsMapTool):
  def __init__(self,iface,color):
      self.canvas = iface.mapCanvas()
      QgsMapTool.__init__(self, self.canvas)
      self.iface = iface
      self.rb = QgsRubberBand(self.canvas, QGis.Point)
      self.rb.setWidth(3)
      self.color = color
      self.rb.setColor( color )
      sb = self.iface.mainWindow().statusBar()
      sb.showMessage(u"Cliquer sur les éléments à copier")
      
      self.geom = []
      
      return None

  def canvasReleaseEvent(self,e):
    if e.button() == Qt.LeftButton:
        point = self.toMapCoordinates(e.pos())
        self.rb.addPoint(point)
        self.rb.show()
    else:
        self.emit( SIGNAL("selectionDone()"))

  def reset(self):
    self.rb.reset( QGis.Point )
    return
    
  def deactivate(self):
    self.rb.reset( QGis.Point )
    return
