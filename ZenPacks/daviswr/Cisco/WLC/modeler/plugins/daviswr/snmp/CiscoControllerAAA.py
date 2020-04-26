# pylint: disable=C0301

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
    modname = 'ZenPacks.daviswr.Cisco.WLC.AAAServer'

    deviceProperties = SnmpPlugin.deviceProperties + (
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
        }

    bsnRadiusAuthServerEntry = {
        # bsnRadiusAuthServerAddress
        '.2': 'ip',
        # bsnRadiusAuthClientServerPortNumber
        '.3': 'port',
        # bsnRadiusAuthServerStatus
        '.5': 'enabled',
        }

    bsnRadiusAccServerEntry = {
        # bsnRadiusAccServerAddress
        '.2': 'ip',
        # bsnRadiusAccClientServerPortNumber
        '.3': 'port',
        # bsnRadiusAccServerStatus
        '.5': 'enabled',
        }

    claTacacsServerEntry = {
        # claTacacsServerAddressType
        '.3': 'ip_type',
        # claTacacsServerAddress
        '.4': 'ip',
        # claTacacsServerPortNum
        '.5': 'port',
        # claTacacsServerEnabled
        '.6': 'enabled',
        }

    snmpGetTableMaps = (
        GetTableMap(
            'cldlServerTable',
            '.1.3.6.1.4.1.9.9.614.1.1.1.1',
            cldlServerEntry
            ),
        GetTableMap(
            'bsnRadiusAuthServerTable',
            '.1.3.6.1.4.1.14179.2.5.1.1',
            bsnRadiusAuthServerEntry
            ),
        GetTableMap(
            'bsnRadiusAccServerTable',
            '.1.3.6.1.4.1.14179.2.5.2.1',
            bsnRadiusAccServerEntry
            ),
        GetTableMap(
            'claTacacsServerTable',
            '.1.3.6.1.4.1.9.9.598.1.1.2.1',
            claTacacsServerEntry
            ),
        )

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        getdata, tabledata = results

        log.debug('SNMP Tables:\n%s', tabledata)

        cldlServerTable = tabledata.get('cldlServerTable', dict())
        log.debug('cldlServerTable has %s entries', len(cldlServerTable))

        bsnRadiusAuthServerTable = tabledata.get(
            'bsnRadiusAuthServerTable',
            dict()
            )
        log.debug(
            'bsnRadiusAuthServerTable has %s entries',
            len(bsnRadiusAuthServerTable)
            )

        bsnRadiusAccServerTable = tabledata.get(
            'bsnRadiusAccServerTable',
            dict()
            )
        log.debug(
            'bsnRadiusAccServerTable has %s entries',
            len(bsnRadiusAccServerTable)
            )

        claTacacsServerTable = tabledata.get('claTacacsServerTable', dict())
        log.debug(
            'claTacacsServerTable has %s entries',
            len(claTacacsServerTable)
            )

        # Ignore criteria
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
                except ValueError:
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
        if 'ldap' in ignore_types_list:
            log.info('Skipping all LDAP servers due to zWlanServerIgnoreTypes')
            cldlServerTable = dict()
        for snmpindex in cldlServerTable:
            row = cldlServerTable[snmpindex]

            if 'ip' in row and row.get('ip_type', 0) == 1:
                row['ip'] = self.asip(row['ip'])

                # Check ignore criteria, if we have an IP
                if self.ip_in_nets(row['ip'], ignore_nets):
                    log.debug(
                        'Skipping LDAP server %s due to zWlanServerIgnoreSubnets',  # noqa
                        row['ip']
                        )
                    continue

                row['title'] = self.format_title(row['ip'], row.get('port'))

            # Have an IP but can't convert it to dotted-quad format
            elif 'ip' in row:
                row['title'] = 'LDAP Server {0}'.format(
                    snmpindex.replace('.', '')
                    )
            else:
                continue

            # Clean up attributes
            if 'enabled' in row:
                row['enabled'] = True if 1 == row['enabled'] else False

            row['id'] = self.prepId('ldap_{0}'.format(row['title']))
            row['snmpindex'] = snmpindex.strip('.')
            log.debug('Found LDAP server: %s', row['title'])

            rm.append(ObjectMap(
                modname='ZenPacks.daviswr.Cisco.WLC.LDAPServer',
                data=row
                ))

        # RADIUS servers
        # Empty SNMP RADIUS auth servers table if we're ignoring them
        if 'radiusauth' in ignore_types_list or 'radius' in ignore_types_list:
            log.info(
                'Skipping all RADIUS auth servers due to zWlanServerIgnoreTypes'  # noqa
                )
            bsnRadiusAuthServerTable = dict()
        for snmpindex in bsnRadiusAuthServerTable:
            row = bsnRadiusAuthServerTable[snmpindex]
            ip = row.get('ip')

            if not ip:
                continue
            elif self.ip_in_nets(ip, ignore_nets):
                log.debug(
                    'Skipping RADIUS auth server %s due to zWlanServerIgnoreSubnets',  # noqa
                    ip
                    )
                continue

            # Clean up attributes
            if 'enabled' in row:
                row['enabled'] = True if 1 == row['enabled'] else False

            row['title'] = self.format_title(ip, row.get('port'))
            row['id'] = self.prepId('radauth_{0}'.format(row['title']))
            row['snmpindex'] = snmpindex.strip('.')
            log.debug('Found RADIUS auth server: %s', row['title'])

            rm.append(ObjectMap(
                modname='ZenPacks.daviswr.Cisco.WLC.RadAuthServer',
                data=row
                ))

        # Empty SNMP RADIUS acct servers table if we're ignoring them
        if 'radiusacct' in ignore_types_list or 'radius' in ignore_types_list:
            log.info(
                'Skipping all RADIUS acct servers due to zWlanServerIgnoreTypes'  # noqa
                )
            bsnRadiusAccServerTable = dict()
        for snmpindex in bsnRadiusAccServerTable:
            row = bsnRadiusAccServerTable[snmpindex]
            ip = row.get('ip')

            if not ip:
                continue
            elif self.ip_in_nets(ip, ignore_nets):
                log.debug(
                    'Skipping RADIUS acct server %s due to zWlanServerIgnoreSubnets',  # noqa
                    ip
                    )
                continue

            # Clean up attributes
            if 'enabled' in row:
                row['enabled'] = True if 1 == row['enabled'] else False
            row['title'] = self.format_title(ip, row.get('port'))
            row['id'] = self.prepId('radacct_{0}'.format(row['title']))
            row['snmpindex'] = snmpindex.strip('.')
            log.debug('Found RADIUS acct server: %s', row['title'])

            rm.append(ObjectMap(
                modname='ZenPacks.daviswr.Cisco.WLC.RadAcctServer',
                data=row
                ))

        # TACACS servers
        # Empty SNMP TACACS servers table if we're ignoring TACACS
        if 'tacacs' in ignore_types_list:
            log.info(
                'Skipping all TACACS servers due to zWlanServerIgnoreTypes'
                )
            claTacacsServerTable = dict()
        for snmpindex in claTacacsServerTable:
            row = claTacacsServerTable[snmpindex]

            type_map = {
                '1': 'TacAuthn',
                '2': 'TacAuthz',
                '3': 'TacAcct',
                }

            tac_type = type_map.get(snmpindex.split('.')[0], 'Tacacs')

            if tac_type.lower() in ignore_types_list:
                log.debug(
                    'Skipping %s server due to zWlanServerIgnoreTypes',
                    tac_type
                    )
                continue

            if 'ip' in row and row.get('ip_type', 0) == 1:
                row['ip'] = self.asip(row['ip'])

                # Check ignore criteria, if we have an IP
                if self.ip_in_nets(row['ip'], ignore_nets):
                    log.debug(
                        'Skipping TACACS server %s due to zWlanServerIgnoreSubnets',  # noqa
                        row['ip']
                        )
                    continue

                row['title'] = self.format_title(row['ip'], row.get('port'))

            # Have an IP but can't convert it to dotted-quad format
            elif 'ip' in row:
                row['title'] = '{0} Server {1}'.format(
                    tac_type,
                    snmpindex.split('.')[1]
                    )
            else:
                continue

            # Clean up attributes
            if 'enabled' in row:
                row['enabled'] = True if 1 == row['enabled'] else False

            row['id'] = self.prepId('{0}_{1}'.format(
                tac_type.lower(),
                row['title']
                ))
            row['snmpindex'] = snmpindex.strip('.')
            log.debug('Found %s server: %s', tac_type, row['title'])

            rm.append(ObjectMap(
                modname='ZenPacks.daviswr.Cisco.WLC.{0}Server'.format(
                    tac_type
                    ),
                data=row
                ))

        log.debug('%s RelMap:\n%s', self.name(), str(rm))
        return rm

    def format_title(self, ip, port):
        """Returns IP & port as colon-delimited string, if possible"""
        return '{0}:{1}'.format(ip, port) if port is not None else ip

    def ip_in_nets(self, ip, nets):
        """Determines if an IP address is in a subnet in a list"""
        contains = False
        for net in nets:
            try:
                if net.Contains(ipaddr.IPAddress(ip)):
                    contains = True
                    break
            except ValueError:
                log.warn('%s ip not a valid IP address', ip)
                break
        return contains
