__doc__ = """ArubaControllerCPU

models processors from an Aruba Mobility Controller

"""

from Products.DataCollector.plugins.CollectorPlugin \
    import SnmpPlugin, GetTableMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs


class ArubaControllerCPU(SnmpPlugin):
    maptype = 'CPUMap'
    compname = 'hw'
    relname = 'cpus'
    modname = 'Products.ZenModel.CPU'

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        maps = list()
        getdata, tabledata = results

        log.debug('SNMP Tables:\n%s', tabledata)

        pass
