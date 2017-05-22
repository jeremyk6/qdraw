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

from PyQt4.QtCore import SIGNAL, QTranslator
from PyQt4.QtGui import QAction, QIcon, QMessageBox

from qgis.core import *

from drawtools import *
from qdrawsettings import *

import os
import resources

class Qdraw:

    def __init__(self, iface):
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            os.path.dirname(__file__),
            'i18n',
            'qdraw_{}.qm'.format(locale))
        
        self.translator = None
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
    
        self.iface = iface
        self.iface.currentLayerChanged.connect(self.currentLayerChanged)
        self.sb = self.iface.mainWindow().statusBar()
        self.tool = None
        self.toolname = None

        self.actions = []
        self.menu = '&Qdraw'
        self.toolbar = self.iface.addToolBar('Qdraw')
        self.toolbar.setObjectName('Qdraw')
        
        self.settings = QdrawSettings()
        
    def unload(self):
        for action in self.actions:
            self.iface.removePluginVectorMenu('&Qdraw', action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar
        
    def tr(self, message):
        return QCoreApplication.translate('Qdraw', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        checkable=False,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
	menu=None,
        parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        action.setCheckable(checkable)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)
            
        if menu is not None:
            action.setMenu(menu)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        menu = QMenu()
        menu.addAction(QIcon(':/plugins/Qgeric/resources/icon_DrawPtXY.png'), self.tr('XY Point drawing tool'), self.drawXYPoint)
        menu.addAction(QIcon(':/plugins/Qgeric/resources/icon_DrawPtDMS.png'), self.tr('DMS Point drawing tool'), self.drawDMSPoint)
        icon_path = ':/plugins/Qgeric/resources/icon_DrawPt.png'
        self.add_action(
            icon_path,
            text=self.tr('Point drawing tool'),
            checkable=True,
            menu = menu,
            callback=self.drawPoint,
            parent=self.iface.mainWindow()
        )
        icon_path = ':/plugins/Qgeric/resources/icon_DrawL.png'
        self.add_action(
            icon_path,
            text=self.tr('Line drawing tool'),
            checkable=True,
            callback=self.drawLine,
            parent=self.iface.mainWindow()
        ) 
        icon_path = ':/plugins/Qgeric/resources/icon_DrawR.png'
        self.add_action(
            icon_path,
            text=self.tr('Rectangle drawing tool'),
            checkable=True,
            callback=self.drawRect,
            parent=self.iface.mainWindow()
        ) 
        icon_path = ':/plugins/Qgeric/resources/icon_DrawC.png'
        self.add_action(
            icon_path,
            text=self.tr('Circle drawing tool'),
            checkable=True,
            callback=self.drawCircle,
            parent=self.iface.mainWindow()
        ) 
        icon_path = ':/plugins/Qgeric/resources/icon_DrawP.png'
        self.add_action(
            icon_path,
            text=self.tr('Polygon drawing tool'),
            checkable=True,
            callback=self.drawPolygon,
            parent=self.iface.mainWindow()
        ) 
        icon_path = ':/plugins/Qgeric/resources/icon_DrawT.png'
        self.add_action(
            icon_path,
            text=self.tr('Buffer drawing tool on the selected layer'),
            checkable=True,
            callback=self.drawBuffer,
            parent=self.iface.mainWindow()
        ) 
        icon_path = ':/plugins/Qgeric/resources/icon_DrawTP.png'
        self.add_action(
            icon_path,
            text=self.tr('Polygon buffer drawing tool on the selected layer'),
            checkable=True,
            callback=self.drawPolygonBuffer,
            parent=self.iface.mainWindow()
        ) 
        icon_path = ':/plugins/Qgeric/resources/icon_DrawCp.png'
        self.add_action(
            icon_path,
            text=self.tr('Attributes copying tool'),
            checkable=True,
            callback=self.copyFeatures,
            parent=self.iface.mainWindow()
        ) 
        icon_path = ':/plugins/Qgeric/resources/icon_Settings.png'
        self.add_action(
            icon_path,
            text=self.tr('Settings'),
            callback=self.showSettingsWindow,
            parent=self.iface.mainWindow()
        )      
            
    def drawPoint(self):
        if self.tool:
            self.tool.reset()
        self.tool = drawPoint(self.iface, self.settings.getColor())
        self.tool.setAction(self.actions[0])
        self.iface.connect(self.tool, SIGNAL("selectionDone()"), self.draw)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.drawShape = 'point'
        self.toolname = 'drawPoint'
        self.sb.showMessage(self.tr('Left click to place a point.'))
        
    def drawXYPoint(self):
        tuple, ok = XYDialog().getPoint(self.iface.mapCanvas().mapRenderer().destinationCrs())
        point = tuple[0]
        self.XYcrs = tuple[1]
        if ok:
            if point.x() == 0 and point.y() == 0:
                QMessageBox.critical(self.iface.mainWindow(), self.tr('Error'), self.tr('Invalid input !'))
            else:
                self.drawPoint()
                self.tool.rb = QgsRubberBand(self.iface.mapCanvas(),QGis.Point)
                self.tool.rb.setColor( self.settings.getColor() )
                self.tool.rb.setWidth(3)
                self.tool.rb.addPoint(point)
                self.drawShape = 'XYpoint'
                self.draw()
                
    def drawDMSPoint(self):
        point, ok = DMSDialog().getPoint()
        self.XYcrs = QgsCoordinateReferenceSystem(4326)
        if ok:
            if point.x() == 0 and point.y() == 0:
                QMessageBox.critical(self.iface.mainWindow(), self.tr('Error'), self.tr('Invalid input !'))
            else:
                self.drawPoint()
                self.tool.rb = QgsRubberBand(self.iface.mapCanvas(),QGis.Point)
                self.tool.rb.setColor( self.settings.getColor() )
                self.tool.rb.setWidth(3)
                self.tool.rb.addPoint(point)
                self.drawShape = 'XYpoint'
                self.draw()
        
    def drawLine(self):
        if self.tool:
            self.tool.reset()
        self.tool = drawLine(self.iface, self.settings.getColor())
        self.tool.setAction(self.actions[1])
        self.iface.connect(self.tool, SIGNAL("selectionDone()"), self.draw)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.drawShape = 'line'
        self.toolname = 'drawLine'
        self.sb.showMessage(self.tr('Left click to place points. Right click to confirm.'))
        
    def drawRect(self):
        if self.tool:
            self.tool.reset()
        self.tool = drawRect(self.iface, self.settings.getColor())
        self.tool.setAction(self.actions[2])
        self.iface.connect(self.tool, SIGNAL("selectionDone()"), self.draw)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.drawShape = 'polygon'
        self.toolname = 'drawRect'
        self.sb.showMessage(self.tr('Maintain the left click to draw a rectangle.'))
        
    def drawCircle(self):
        if self.tool:
            self.tool.reset()
        self.tool = drawCircle(self.iface, self.settings.getColor(), 40)
        self.tool.setAction(self.actions[3])
        self.iface.connect(self.tool, SIGNAL("selectionDone()"), self.draw)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.drawShape = 'polygon'
        self.toolname = 'drawCircle'
        self.sb.showMessage(self.tr('Maintain the left click to draw a circle. Simple Left click to give a perimeter.'))
        
    def drawPolygon(self):
        if self.tool:
            self.tool.reset()
        self.tool = drawPolygon(self.iface, self.settings.getColor())
        self.tool.setAction(self.actions[4])
        self.iface.connect(self.tool, SIGNAL("selectionDone()"), self.draw)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.drawShape = 'polygon'
        self.toolname = 'drawPolygon'
        self.sb.showMessage(self.tr('Left click to place points. Right click to confirm.'))
        
    def drawBuffer(self):
        if self.tool:
            self.tool.reset()
        self.tool = selectPoint(self.iface, self.settings.getColor())
        self.tool.setAction(self.actions[5])
        self.iface.connect(self.tool, SIGNAL("selectionDone()"), self.draw)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.drawShape = 'polygon'
        self.toolname = 'drawBuffer'
        self.sb.showMessage(self.tr('Select a vector layer in the Layer Tree, then left click on an attribute of this layer on the map.'))
        
    def drawPolygonBuffer(self):
        if self.tool:
            self.tool.reset()
        self.tool = drawPolygon(self.iface, self.settings.getColor())
        self.tool.setAction(self.actions[6])
        self.iface.connect(self.tool, SIGNAL("selectionDone()"), self.draw)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.drawShape = 'polygon'
        self.toolname = 'drawBuffer'
        self.sb.showMessage(self.tr('Left click to place points. Right click to confirm.'))
        
    def copyFeatures(self):
        if self.tool:
            self.tool.reset()
        layer = self.iface.legendInterface().currentLayer()
        self.tool = copyFeatures(self.iface, self.settings.getColor(), self.iface.legendInterface().currentLayer())
        self.tool.setAction(self.actions[7])
        self.iface.mapCanvas().setMapTool(self.tool)
        if layer is not None and layer.type() == QgsMapLayer.VectorLayer and self.iface.legendInterface().isLayerVisible(layer):
            self.iface.connect(self.tool, SIGNAL("selectionDone()"), self.draw)
            self.drawShape = 'polygon'
            self.toolname = 'drawCopies'
            self.sb.showMessage(self.tr('Select a vector layer in the Layer Tree, then left click on attributes of this layer on the map. Right Click to confirm.'))
        else:
            self.iface.messageBar().pushMessage(self.tr('Attributes copying tool'), self.tr('No vector layer selected !'), level=QgsMessageBar.WARNING, duration=3)
            self.iface.mapCanvas().unsetMapTool(self.tool)
    
    def currentLayerChanged(self, layer):
        if self.toolname == 'drawCopies':
            self.copyFeatures()
        
    def showSettingsWindow(self):
        self.iface.connect(self.settings, SIGNAL("settingsChanged()"), self.settingsChanged)
        self.settings.show() 
      
    # triggered when a setting is changed
    # reload the current tool so it uses the new settings
    def settingsChanged(self):
        if self.toolname == 'drawPoint':
            self.drawPoint()
        elif self.toolname == 'drawRect':
            self.drawRect()
        elif self.toolname == 'drawPolygon':
            self.drawPolygon()
        elif self.toolname == 'drawCopies':
            self.copyFeatures()
        elif self.toolname == 'drawCircle':
            self.drawCircle()
        elif self.toolname == 'drawLine':
            self.drawLine()
        elif self.toolname == 'drawBuffer':
            self.drawBuffer()
        else:
            return
            
    def geomTransform(self, geom, crs_orig, crs_dest):
        g = QgsGeometry(geom)
        crsTransform = QgsCoordinateTransform(crs_orig, crs_dest)
        g.transform(crsTransform)
        return g
        
    def draw(self):
        rb = self.tool.rb
        g = rb.asGeometry()
        
        ok = True
        warning = False
        errBuffer_noAtt = False
        errBuffer_Vertices = False
        
        if self.toolname == 'drawBuffer':
            legende = self.iface.legendInterface()
            layer = legende.currentLayer()
            if layer is not None and layer.type() == QgsMapLayer.VectorLayer and legende.isLayerVisible(layer):
                # rubberband reprojection
                g = self.geomTransform(rb.asGeometry(), self.iface.mapCanvas().mapRenderer().destinationCrs(), layer.crs())
                features = layer.getFeatures(QgsFeatureRequest(g.boundingBox()))
                rbGeom = []
                for feature in features:
                    geom = feature.geometry()
                    try:
                        if g.intersects(geom):
                            rbGeom.append(feature.geometryAndOwnership())
                    except:
                        # there's an error but it intersects
                        print 'error with '+layer.name()+' on '+str(feature.id())
                        rbGeom.append(feature.geometryAndOwnership())
                if len(rbGeom) > 0:
                    union_geoms = rbGeom[0]
                    for geometry in rbGeom:
                        if union_geoms.combine(geometry) is not None:
                            union_geoms = union_geoms.combine(geometry)
                    rb.setToGeometry(union_geoms, layer)
                    perim = 0
                    if self.toolname == 'drawBuffer':
                        perim, ok = QInputDialog.getInt(self.iface.mainWindow(), self.tr('Perimeter'), self.tr('Give a perimeter in m:')+'\n'+self.tr('(works only with metric crs)'), min=0)                       
                    g = union_geoms.buffer(perim, 40)
                    rb.setToGeometry(g, QgsVectorLayer("Polygon?crs="+layer.crs().authid(),"","memory"))
                    if g.length() == 0 and ok:
                        warning = True
                        errBuffer_Vertices = True
                else:
                    warning = True
                    errBuffer_noAtt = True
            else:
                warning = True
                
        if self.toolname == 'drawCopies':
            if g.length() < 0:
                warning = True
                errBuffer_noAtt = True
                
            
        if ok and warning == False:
            name = ''
            ok = True
            while not name.strip() and ok == True:
                name, ok = QInputDialog.getText(self.iface.mainWindow(), self.tr('Drawing'), self.tr('Give a name to the layer:'))
        if ok and warning == False:
            layer = None
            if self.drawShape == 'point':
                layer = QgsVectorLayer("Point?crs="+self.iface.mapCanvas().mapRenderer().destinationCrs().authid()+"&field="+self.tr('Drawings')+":string(255)",name,"memory")
            elif self.drawShape == 'XYpoint':
                layer = QgsVectorLayer("Point?crs="+self.XYcrs.authid()+"&field="+self.tr('Drawings')+":string(255)",name,"memory")
            elif self.drawShape == 'line':
                layer = QgsVectorLayer("LineString?crs="+self.iface.mapCanvas().mapRenderer().destinationCrs().authid()+"&field="+self.tr('Drawings')+":string(255)",name,"memory")
                print "LineString?crs="+self.iface.mapCanvas().mapRenderer().destinationCrs().authid()+"&field="+self.tr('Drawings')+":string(255)"
            else:
                layer = QgsVectorLayer("Polygon?crs="+self.iface.mapCanvas().mapRenderer().destinationCrs().authid()+"&field="+self.tr('Drawings')+":string(255)",name,"memory")
            layer.startEditing()
            symbols = layer.rendererV2().symbols()
            symbols[0].setColor(self.settings.getColor())
            feature = QgsFeature()
            feature.setGeometry(g)
            feature.setAttributes([name])
            layer.dataProvider().addFeatures([feature])
            layer.commitChanges()
            QgsMapLayerRegistry.instance().addMapLayer(layer, False)
            if QgsProject.instance().layerTreeRoot().findGroup(self.tr('Drawings')) == None:
                QgsProject.instance().layerTreeRoot().insertChildNode(0,QgsLayerTreeGroup(self.tr('Drawings')))
            group = QgsProject.instance().layerTreeRoot().findGroup(self.tr('Drawings'))
            group.insertLayer(0,layer)
            self.iface.mapCanvas().refresh()
        else:
            if warning:
                if errBuffer_noAtt:
                    self.iface.messageBar().pushMessage(self.tr('Warning'), self.tr('You didn\'t click on a layer\'s attribute !'), level=QgsMessageBar.WARNING, duration=3)
                elif errBuffer_Vertices:
                    self.iface.messageBar().pushMessage(self.tr('Warning'), self.tr('You must give a non-null value for a point\'s or line\'s perimeter !'), level=QgsMessageBar.WARNING, duration=3)
                else:
                    self.iface.messageBar().pushMessage(self.tr('Warning'), self.tr('There is no selected layer, or it is not vector nor visible !'), level=QgsMessageBar.WARNING, duration=3)
        self.tool.reset()
