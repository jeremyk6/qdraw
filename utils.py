from qgis.PyQt.QtCore import QCoreApplication

def tr(message):
    return QCoreApplication.translate('Qdraw', message)