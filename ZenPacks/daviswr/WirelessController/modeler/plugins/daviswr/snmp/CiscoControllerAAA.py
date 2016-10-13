__doc__ = """CiscoControllerAAA

models AAA servers from a Cisco Wireless LAN Controller (WLC) running AireOS

"""

import ipaddr
import re

from Products.DataCollector.plugins.CollectorPlugin \
    import SnmpPlugin, GetTableMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs, RelationshipMap, ObjectMap

class CiscoControllerAAA(SnmpPlugin):
    maptype = 'ControllerAAA'

    relname = 'aaaServers'
    modname = 'ZenPacks.daviswr.WirelessController.AAAServer'

    deviceProperties = SnmpPlugin.deviceProperties + (
        'zWlanServerIgnoreNames',
        'zWlanServerIgnoreSubnets',
        'zWlanServerIgnoreTypes',
        )

    cldlServerEntry = {
        # cldlServerAddressType
        '.2': 'ip_type',
        # cldlServerAddress
        '.3': 'ip',
        # cldlServerPortNum
        '.4': 'port',
        # cldlServerState
        '.5': 'enabled',
        # cldlServerUserBase
        '.7': 'baseDN',
        # cldlServerUserNameAttribute
        '.8': 'userAttr',
        # cldlServerAuthBindUserName
        '.14': 'user',
        }

    snmpGetTableMaps = (
        GetTableMap(
            'cldlServerTable',
            '.1.3.6.1.4.1.9.9.614.1.1.1.1',
            cldlServerEntry
            ),
        )

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        getdata, tabledata = results

        log.debug('SNMP Tables:\n%s', tabledata)

        cldlServerTable = tabledata.get('cldlServerTable', dict())
        if not cldlServerTable:
            # Not fatal
            log.warn('Unable to get cldlServerTable from %s', device.id)
        else:
            log.debug(
                'cldlServerTable has %s entries',
                len(cldlServerTable)
                )

        # Ignore criteria
        ignore_names_regex = getattr(device, 'zWlanServerIgnoreNames', '')
        if ignore_names_regex:
            log.info(
                'zWlanServerIgnoreNames set to %s',
                ignore_names_regex
                )

        ignore_net_text = getattr(device, 'zWlanServerIgnoreSubnets', list())
        ignore_nets = list()
        if ignore_net_text:
            log.info(
                'zWlanServerIgnoreSubnets set to %s',
                str(ignore_net_text)
                )
            for net in ignore_net_text:
                try:
                    ignore_nets.append(ipaddr.IPNetwork(net))
                except:
                    log.warn('%s is not a valid CIDR address', net)
                    continue

        ignore_types_list = getattr(device, 'zWlanServerIgnoreTypes', list())
        if ignore_types_list:
            log.info(
                'zWlanServerIgnoreTypes set to %s',
                str(ignore_types_list)
                )

        rm = self.relMap()

        # LDAP servers
        # Empty SNMP LDAP servers table if we're ignoring LDAP
        if 'LDAP' in ignore_types_list or 'ldap' in ignore_types_list:
            log.info('Skipping all LDAP servers due to zWlanServerIgnoreTypes')
            cldlServerTable = dict()
        for snmpindex in cldlServerTable:
            row = cldlServerTable[snmpindex]
            skip_net = False

            if 'ip' in row and row.get('ip_type', 0) == 1:
                row['ip'] = self.asip(row['ip'])
                log.debug('Found LDAP server: %s', row['ip'])

                # Check ignore criteria, if we have an IP
                for net in ignore_nets:
                    if net.Contains(ipaddr.IPAddress(row['ip'])):
                        skip_net = True
                        break
                if skip_net:
                    log.debug(
                        'Skipping LDAP server %s due to zWlanServerIgnoreSubnets',
                        row['ip']
                        )
                    continue

                # Generate a title if not skipping
                if 'port' in row:
                    row['title'] = '{0}:{1}'.format(row['ip'], row['port'])
                else:
                    row['title'] = row['ip']

            else:
                row['title'] = 'LDAP Server {}'.format(
                    snmpindex.replace('.', '')
                    )

            # Clean up attributes
            if 'enabled' in row:
                row['enabled'] = True if 1 == row['enabled'] else False

            row['id'] = self.prepId('ldap_{}'.format(row['title']))

            rm.append(ObjectMap(
                modname='ZenPacks.daviswr.WirelessController.LDAPServer',
                data=row
                ))


        log.debug('%s RelMap:\n%s', self.name(), str(rm))
        return rm
