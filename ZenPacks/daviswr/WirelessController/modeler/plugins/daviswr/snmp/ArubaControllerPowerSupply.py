__doc__ = """ArubaControllerPowerSupply

models power supplies from an Aruba Mobility Controller

"""

from Products.DataCollector.plugins.CollectorPlugin \
    import SnmpPlugin, GetTableMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs

class ArubaControllerPowerSupply(SnmpPlugin):
    maptype = 'PowerSupply'
    compname = 'hw'
    relname = 'powersupplies'
    modname = 'Products.ZenModel.PowerSupply'

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        maps = list()
        getdata, tabledata = results

        log.debug('SNMP Tables:\n%s', tabledata)

        pass
