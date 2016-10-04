__doc__ = """CiscoController

gathers OS and hardware information from a Cisco Wireless LAN Controller 
(WLC) running AireOS

"""

from Products.DataCollector.plugins.CollectorPlugin \
    import SnmpPlugin, GetMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs, ObjectMap

class CiscoController(SnmpPlugin):
    maptype = 'CiscoController'

    snmpGetMap = GetMap({
        '.1.3.6.1.4.1.14179.1.1.1.3.0': 'agentInventoryMachineModel',
        '.1.3.6.1.4.1.14179.1.1.1.4.0': 'agentInventorySerialNumber',
        '.1.3.6.1.4.1.14179.1.1.1.12.0': 'agentInventoryManufacturerName',
        '.1.3.6.1.4.1.14179.1.1.1.14.0': 'agentInventoryProductVersion',
        '.1.3.6.1.4.1.14179.1.1.5.2.0': 'agentTotalMemory',
        '.1.3.6.1.4.1.14179.2.3.1.17.0': 'bsnRFMobilityDomainName',
        '.1.3.6.1.4.1.14179.1.1.1.18.0': 'agentInventoryMaxNumberOfAPsSupported',
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

        om = self.objectMap()
        maps = list()

        manufacturer = getdata.get('agentInventoryManufacturerName', '')
        if manufacturer.lower().find('cisco') > -1 or len(manufacturer) == 0:
            manufacturer = 'Cisco'

        model = getdata.get('agentInventoryMachineModel', None)
        if model:
            log.debug(
                '%s setting model to %s %s',
                self.name(),
                manufacturer,
                model
                )
            om.setHWProductKey = MultiArgs(model, manufacturer)

        os = 'AireOS'
        version = getdata.get('agentInventoryProductVersion', None)
        if version:
            os = '{0} {1}'.format(os, version)
        log.debug(
            '%s setting model to %s %s',
            self.name(),
            manufacturer,
            os
            )
        om.setOSProductKey = MultiArgs(os, manufacturer)

        maps.append(om)

        serial = getdata.get('agentInventorySerialNumber', None)
        if serial:
            log.debug(
                '%s setting serial number to %s',
                self.name(),
                serial
                )
            maps.append(ObjectMap({'setHWSerialNumber': serial}))

        memory = getdata.get('agentTotalMemory', None)
        if memory:
            # AIRESPACE-SWITCHING-MIB::agentTotalMemory is in kilobytes
            memory = str(int(memory)*1024)
            log.debug(
                '%s setting memory size to %s bytes',
                self.name(),
                memory
                )
            maps.append(ObjectMap({'totalMemory': memory}, compname='hw'))

        mobility = getdata.get('bsnRFMobilityDomainName', None)
        if mobility:
            log.debug(
                '%s setting mobility domain to %s',
                self.name(),
                mobility
                )
            maps.append(ObjectMap({'mobilityDomains': [mobility,]}))

        max_ap = getdata.get('agentInventoryMaxNumberOfAPsSupported', None)
        if max_ap:
            log.debug(
                '%s setting platform max APs to %s',
                self.name(),
                max_ap
                )
            maps.append(ObjectMap({'platformMaxAPs': int(max_ap)}))

        return maps
