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

    bsnGlobalDot11Config = {
        # bsnOperatingTemperatureEnvironment
        '.12': 'state',
        # bsnSensorTemperature
        '.13': 'temperature_celsius'
        }

    snmpGetTableMaps = (
        GetTableMap(
            'bsnSensorTemperature',
            '.1.3.6.1.4.1.14179.2.3.1',
            bsnGlobalDot11Config
            ),
        )

    def condition(self, device, log):
        ignore = False
        model = str(device.hw.getModelName())
        if model.find('VM') > -1 or model.find('WISM') > -1:
            log.info('Cisco vWLC and WiSM lack temperature sensors, skipping')
            ignore = True
        return not ignore

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        getdata, tabledata = results

        log.debug('SNMP Tables:\n%s', tabledata)

        bsnSensorTemperature = tabledata.get('bsnSensorTemperature')
        if bsnSensorTemperature is None:
            log.error('Unable to get bsnSensorTemperature for %s', device.id)
            return None
        else:
            log.debug(
                'bsnSensorTemperature has %s entries',
                len(bsnSensorTemperature),
                )

        # Temperator sensors
        rm = self.relMap()

        for snmpindex in bsnSensorTemperature:
            row = bsnSensorTemperature[snmpindex]
            num = int(snmpindex.replace('.', '')) + 1
            name = 'Temperature Sensor {}'.format(num)

            # Clean up attributes
            attr_map = dict()
            attr_map['state'] = {
                1: 'Commercial',
                2: 'Industrial',
                }

            for attr in attr_map:
                if attr in row:
                    row[attr] = attr_map[attr].get(row[attr], row[attr])

            if 'temperature_celsius' in row:
                # The vWLC & WiSM lack temperature sensors, return 5000 deg. C
                # condition() above should catch this if CiscoControllerDevice
                # modeler has ran before
                if 5000 == row['temperature_celsius']:
                    log.debug(
                        'Cisco vWLC or WiSM detected, skipping temperature sensor model'
                        )
                    return None
                temp_f = (row['temperature_celsius'] * (9/5)) + 32
                row['temperature_fahrenheit'] = temp_f

            row.update({
                'id': self.prepId(name.replace(' ', '')),
                'title': name,
                'snmpindex': snmpindex.strip('.'),
                })
            rm.append(self.objectMap(row))

        log.debug('%s RelMap:\n%s', self.name(), str(rm))
        return rm
