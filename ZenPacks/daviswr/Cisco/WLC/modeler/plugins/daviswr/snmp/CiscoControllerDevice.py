# pylint: disable=C0301

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
        # bsnOperatingTemperatureEnvironment
        '.1.3.6.1.4.1.14179.2.3.1.12.0': 'environment',
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
        if not getdata:
            log.warn(
                'Unable to get data from AIRESPACE-SWITCHING-MIB on %s - skipping model',  # noqa
                device.id
                )
            return None

        maps = list()

        # Hardware model
        manufacturer = getdata.get('manufacturer', '')
        if 'cisco' in manufacturer.lower() or not manufacturer:
            manufacturer = 'Cisco'

        if 'model' in getdata:
            getdata['setHWProductKey'] = MultiArgs(
                getdata['model'],
                manufacturer
                )

        # Software version
        os = 'AireOS'
        if 'version' in getdata:
            os = '{0} {1}'.format(os, getdata['version'])
        getdata['setOSProductKey'] = MultiArgs(os, manufacturer)

        # Mobility Domain
        if 'mobility' in getdata:
            getdata.update({'mobilityDomains': [getdata['mobility'], ]})

        # Operating Temperature threshold
        if 'environment' in getdata:
            env_map = dict()
            # Commercial
            env_map[1] = {
                'tempThresholdLow': 0,
                'tempThresholdHigh': 40,
                }
            # Industrial
            env_map[2] = {
                'tempThresholdLow': -10,
                'tempThresholdHigh': 70,
                }
            getdata.update(env_map.get(getdata['environment'], dict()))

        maps.append(ObjectMap(
            modname='ZenPacks.daviswr.Cisco.WLC.Controller',
            data=getdata
            ))

        # Memory
        if 'memory' in getdata:
            # AIRESPACE-SWITCHING-MIB::agentTotalMemory is in kilobytes
            memory = int(getdata['memory'])*1024
            maps.append(ObjectMap({'totalMemory': memory}, compname='hw'))

        log.debug('%s ObjMaps:\n%s', self.name(), str(maps))
        return maps
