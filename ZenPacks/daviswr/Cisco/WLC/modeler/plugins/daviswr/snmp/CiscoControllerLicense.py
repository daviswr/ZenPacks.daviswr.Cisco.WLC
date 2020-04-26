__doc__ = """CiscoControllerLicense

models licenses from a Cisco Wireless LAN Controller (WLC) running AireOS

"""

import re

from copy \
    import deepcopy
from Products.DataCollector.plugins.CollectorPlugin \
    import SnmpPlugin, GetTableMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs, RelationshipMap, ObjectMap


class CiscoControllerLicense(SnmpPlugin):
    maptype = 'ControllerLicense'

    relname = 'licenses'
    modname = 'ZenPacks.daviswr.Cisco.WLC.License'

    clmgmtLicenseInfoEntry = {
        # clmgmtLicenseFeatureName
        '.3': 'title',
        # clmgmtLicenseType
        '.5': 'type',
        # clmgmtLicenseValidityPeriodRemaining
        '.8': 'remaining',
        # clmgmtLicenseMaxUsageCount
        '.10': 'count',
        # clmgmtLicenseStatus
        '.14': 'status',
        }

    snmpGetTableMaps = (
        GetTableMap(
            'clmgmtLicenseInfoTable',
            '.1.3.6.1.4.1.9.9.543.1.2.3.1',
            clmgmtLicenseInfoEntry
            ),
        )

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        maps = list()
        getdata, tabledata = results

        log.debug('SNMP Tables:\n%s', tabledata)

        clmgmtLicenseInfoTable = tabledata.get('clmgmtLicenseInfoTable')
        if clmgmtLicenseInfoTable is None:
            log.error('Unable to get clmgmtLicenseInfoTable for %s', device.id)
            return None
        else:
            log.debug(
                'clmgmtLicenseInfoTable has %s entries',
                len(clmgmtLicenseInfoTable)
                )

        # Licenses
        rm = self.relMap()

        for snmpindex in clmgmtLicenseInfoTable:
            row = clmgmtLicenseInfoTable[snmpindex]
            name = row.get('title', None)

            if name is None or '' == name:
                continue

            log.debug('%s found license: %s', self.name(), name)

            # Need to save the original numeric value for grid display enum
            if 'status' in row:
                row['statusSev'] = deepcopy(row['status'])

            # Clean up attributes
            attr_map = dict()
            attr_map['status'] = {
                1: 'inactive',
                2: 'not in use',
                3: 'in use',
                4: 'expired, in use',
                5: 'expire, not in use',
                6: 'usage count consumed',
                }

            attr_map['type'] = {
                1: 'evaluation',
                2: 'extension',
                3: 'grace period',
                4: 'permanent',
                5: 'paid subscription',
                6: 'evaluation subscription',
                7: 'extension subscription',
                8: 'evaluation right to use',
                9: 'right to use',
                10: 'permanent right to use',
                }

            for attr in attr_map:
                if attr in row:
                    row[attr] = attr_map[attr].get(row[attr], row[attr])

            if 'type' in row:
                row['title'] = '{0} {1}'.format(row['type'].title(), name)
                if 'permanent' == row['type']:
                    row['expiration'] = 'Never'

            # Match formatting in WLC web interface
            if 'remaining' in row and row.get('expiration', '') != 'Never':
                row['expiration'] = ''
                if row['remaining'] > 604800:
                    row['expiration'] = '{0} weeks, '.format(
                        row['remaining'] / 604800
                        )
                row['expiration'] += '{0} days'.format(
                    (row['remaining'] % 604800) / 86400
                    )

            # Update dictionary and create Object Map
            row.update({
                'snmpindex': snmpindex.strip('.'),
                'id': self.prepId('license_{0}'.format(snmpindex))
                })

            rm.append(ObjectMap(
                modname='ZenPacks.daviswr.Cisco.WLC.License',
                data=row
                ))

        log.debug('%s RelMap:\n%s', self.name(), str(rm))

        return rm
