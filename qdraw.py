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
from PyQt4.QtGui import QAction, QIcon

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
            self.iface.removePluginMenu('&Qdraw', action)
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

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        icon_path = ':/plugins/Qgeric/resources/icon_DrawPt.png'
        self.add_action(
            icon_path,
            text=self.tr('Point drawing tool'),
            callback=self.drawPoint,
            parent=self.iface.mainWindow()
        ) 
        icon_path = ':/plugins/Qgeric/resources/icon_DrawL.png'
        self.add_action(
            icon_path,
            text=self.tr('Line drawing tool'),
            callback=self.drawLine,
            parent=self.iface.mainWindow()
        ) 
        icon_path = ':/plugins/Qgeric/resources/icon_DrawR.png'
        self.add_action(
            icon_path,
            text=self.tr('Rectangle drawing tool'),
            callback=self.drawRect,
            parent=self.iface.mainWindow()
        ) 
        icon_path = ':/plugins/Qgeric/resources/icon_DrawC.png'
        self.add_action(
            icon_path,
            text=self.tr('Circle drawing tool'),
            callback=self.drawCircle,
            parent=self.iface.mainWindow()
        ) 
        icon_path = ':/plugins/Qgeric/resources/icon_DrawP.png'
        self.add_action(
            icon_path,
            text=self.tr('Polygon drawing tool'),
            callback=self.drawPolygon,
            parent=self.iface.mainWindow()
        ) 
        icon_path = ':/plugins/Qgeric/resources/icon_DrawT.png'
        self.add_action(
            icon_path,
            text=self.tr('Buffer drawing tool'),
            callback=self.drawBuffer,
            parent=self.iface.mainWindow()
        ) 
        icon_path = ':/plugins/Qgeric/resources/icon_DrawCp.png'
        self.add_action(
            icon_path,
            text=self.tr('Attributes copying tool'),
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
        self.iface.connect(self.tool, SIGNAL("selectionDone()"), self.draw)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.drawShape = 'point'
        self.toolname = 'drawPoint'
        self.sb.showMessage(self.tr('Left click to place a point.'))
        
    def drawLine(self):
        if self.tool:
            self.tool.reset()
        self.tool = drawLine(self.iface, self.settings.getColor())
        self.iface.connect(self.tool, SIGNAL("selectionDone()"), self.draw)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.drawShape = 'line'
        self.toolname = 'drawLine'
        self.sb.showMessage(self.tr('Left click to place points. Right click to confirm.'))
        
    def drawRect(self):
        if self.tool:
            self.tool.reset()
        self.tool = drawRect(self.iface, self.settings.getColor())
        self.iface.connect(self.tool, SIGNAL("selectionDone()"), self.draw)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.drawShape = 'polygon'
        self.toolname = 'drawRect'
        self.sb.showMessage(self.tr('Maintain the left click to draw a rectangle.'))
        
    def drawCircle(self):
        if self.tool:
            self.tool.reset()
        self.tool = drawCircle(self.iface, self.settings.getColor(), 40)
        self.iface.connect(self.tool, SIGNAL("selectionDone()"), self.draw)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.drawShape = 'polygon'
        self.toolname = 'drawCircle'
        self.sb.showMessage(self.tr('Maintain the left click to draw a circle. Simple Left click to give a perimeter.'))
        
    def drawPolygon(self):
        if self.tool:
            self.tool.reset()
        self.tool = drawPolygon(self.iface, self.settings.getColor())
        self.iface.connect(self.tool, SIGNAL("selectionDone()"), self.draw)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.drawShape = 'polygon'
        self.toolname = 'drawPolygon'
        self.sb.showMessage(self.tr('Left click to place points. Right click to confirm.'))
        
    def drawBuffer(self):
        if self.tool:
            self.tool.reset()
        self.tool = selectPoint(self.iface, self.settings.getColor())
        self.iface.connect(self.tool, SIGNAL("selectionDone()"), self.draw)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.drawShape = 'polygon'
        self.toolname = 'drawBuffer'
        self.sb.showMessage(self.tr('Select a vector layer in the Layer Tree, then left click on an attribute of this layer on the map.'))
        
    def copyFeatures(self):
        if self.tool:
            self.tool.reset()
        self.tool = copyFeatures(self.iface, self.settings.getColor())
        self.iface.connect(self.tool, SIGNAL("selectionDone()"), self.draw)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.drawShape = 'polygon'
        self.toolname = 'drawCopies'
        self.sb.showMessage(self.tr('Select a vector layer in the Layer Tree, then left click on attributes of this layer on the map. Right Click to confirm.'))
        
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
        
        if self.toolname == 'drawBuffer' or self.toolname == 'drawCopies':
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
                        perim, ok = QInputDialog.getInt(self.iface.mainWindow(), self.tr('Perimeter'), self.tr('Give a perimeter in m:'), min=0)  
                    buffer_geom_crs = QgsCoordinateReferenceSystem(2154) # use a CRS that supports metric system
                    g = self.geomTransform(union_geoms, layer.crs(), buffer_geom_crs).buffer(perim, 40) 
                    rb.setToGeometry(g, QgsVectorLayer("Polygon?crs=epsg:2154","","memory"))
                    if rb.numberOfVertices() <= 1 and ok:
                        warning = True
                        errBuffer_Vertices = True
                else:
                    warning = True
                    errBuffer_noAtt = True
            else:
                warning = True
        else:        
            g = self.geomTransform(rb.asGeometry(), self.iface.mapCanvas().mapRenderer().destinationCrs(), QgsCoordinateReferenceSystem(2154))
            
        if ok and warning == False:
            name, ok = QInputDialog.getText(self.iface.mainWindow(), self.tr('Drawing'), self.tr('Give a name to the layer:'))
        if ok and warning == False:
            layer = None
            if self.drawShape == 'point':
                layer = QgsVectorLayer("Point?crs=epsg:2154&field="+self.tr('Drawings')+":string(255)",name,"memory")
            elif self.drawShape == 'line':
                layer = QgsVectorLayer("LineString?crs=epsg:2154&field="+self.tr('Drawings')+":string(255)",name,"memory")
            else:
                layer = QgsVectorLayer("Polygon?crs=epsg:2154&field="+self.tr('Drawings')+":string(255)",name,"memory")
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