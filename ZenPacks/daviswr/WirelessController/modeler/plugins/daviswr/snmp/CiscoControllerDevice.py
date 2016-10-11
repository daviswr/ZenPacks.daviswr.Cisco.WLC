__doc__ = """CiscoControllerDevice

gathers OS and hardware information from a Cisco Wireless LAN Controller 
(WLC) running AireOS

"""

from Products.DataCollector.plugins.CollectorPlugin \
    import SnmpPlugin, GetMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs, ObjectMap

class CiscoControllerDevice(SnmpPlugin):
    maptype = 'ControllerDevice'

    snmpGetMap = GetMap({
        # entPhysicalDescr
        '.1.3.6.1.2.1.47.1.1.1.1.2.1': 'snmpDescr',
        # entPhysicalHardwareRev
        '.1.3.6.1.2.1.47.1.1.1.1.8.1': 'hwVersion',
        # agentInventoryMachineModel
        '.1.3.6.1.4.1.14179.1.1.1.3.0': 'model',
        # agentInventorySerialNumber
        '.1.3.6.1.4.1.14179.1.1.1.4.0': 'setHWSerialNumber',
        # agentInventoryManufacturerName
        '.1.3.6.1.4.1.14179.1.1.1.12.0': 'manufacturer',
        # agentInventoryProductVersion
        '.1.3.6.1.4.1.14179.1.1.1.14.0': 'version',
        # agentInventoryMaxNumberOfAPsSupported
        '.1.3.6.1.4.1.14179.1.1.1.18.0': 'platformMaxAPs',
        # agentTotalMemory
        '.1.3.6.1.4.1.14179.1.1.5.2.0': 'memory',
        # bsnRFMobilityDomainName
        '.1.3.6.1.4.1.14179.2.3.1.17.0': 'mobility',
        })

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info(
            'processing %s for device %s',
            self.name(),
            device.id
            )
        getdata, tabledata = results
        if getdata is None:
            log.warn(
                'Unable to get data from AIRESPACE-SWITCHING-MIB on %s - skipping model',
                device.id
                )
            return None

        maps = list()

        # Hardware model
        manufacturer = getdata.get('manufacturer', '')
        if manufacturer.lower().find('cisco') > -1 or len(manufacturer) == 0:
            manufacturer = 'Cisco'

        if 'model' in getdata:
            getdata['setHWProductKey'] = MultiArgs(getdata['model'], manufacturer)

        # Software version
        os = 'AireOS'
        if 'version' in getdata:
            os = '{0} {1}'.format(os, getdata['version'])
        getdata['setOSProductKey'] = MultiArgs(os, manufacturer)

        # Mobility Domain
        if 'mobility' in getdata:
            getdata.update({'mobilityDomains': [getdata['mobility'],]})

        maps.append(ObjectMap(
            modname='ZenPacks.daviswr.WirelessController.CiscoController',
            data=getdata
            ))

        # Memory
        if 'memory' in getdata:
            # AIRESPACE-SWITCHING-MIB::agentTotalMemory is in kilobytes
            memory = int(getdata['memory'])*1024
            maps.append(ObjectMap({'totalMemory': memory}, compname='hw'))

        log.debug('%s ObjMaps:\n%s', self.name(), str(maps))
        return maps
