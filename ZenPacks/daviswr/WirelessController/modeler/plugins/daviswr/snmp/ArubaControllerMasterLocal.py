__doc__ = """ArubaControllerMasterLocal

models master & local controllers from an Aruba Mobility Controller

"""

import re

from Products.DataCollector.plugins.CollectorPlugin \
    import SnmpPlugin, GetTableMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs, RelationshipMap, ObjectMap


class ArubaControllerMasterLocal(SnmpPlugin):
    maptype = 'ArubaControllerMasterLocal'

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        maps = list()
        getdata, tabledata = results

        log.debug('SNMP Tables:\n%s', tabledata)

        pass
