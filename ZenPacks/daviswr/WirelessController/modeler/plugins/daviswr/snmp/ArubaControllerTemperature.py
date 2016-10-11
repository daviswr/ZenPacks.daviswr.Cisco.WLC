__doc__ = """ArubaControllerTemperature

models temperature sensors from an Aruba Mobility Controller

"""

from Products.DataCollector.plugins.CollectorPlugin \
    import SnmpPlugin, GetTableMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs

class ArubaControllerTemperature(SnmpPlugin):
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
