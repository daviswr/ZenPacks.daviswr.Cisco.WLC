__doc__ = """ArubaControllerAP

models access points and AP groups from an Aruba Mobility Controller

"""

import ipaddr
import re

from Products.DataCollector.plugins.CollectorPlugin \
    import SnmpPlugin, GetTableMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs, RelationshipMap, ObjectMap

class ArubaControllerAP(SnmpPlugin):
    maptype = 'ControllerAP'

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        maps = list()
        getdata, tabledata = results

        log.debug('SNMP Tables:\n%s', tabledata)

        pass
