__doc__ = """CiscoControllerTemperature

models temperature sensors from an Cisco Wireless LAN Controller 
(WLC) running AireOS

"""

from Products.DataCollector.plugins.CollectorPlugin \
    import SnmpPlugin, GetTableMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs

class CiscoControllerTemperature(SnmpPlugin):
    maptype = 'TemperatureSensorMap'
    compname = 'hw'
    relname = 'temperaturesensors'
    modname = 'Products.ZenModel.TemperatureSensor'

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        maps = list()
        getdata, tabledata = results

        log.debug('SNMP Tables:\n%s', tabledata)

        pass
