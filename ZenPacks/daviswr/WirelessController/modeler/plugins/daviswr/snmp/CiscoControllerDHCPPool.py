__doc__ = """CiscoControllerDHCPPool

models DHCP pools from a Cisco Wireless LAN Controller (WLC) running AireOS

"""

import ipaddr
import re

from Products.DataCollector.plugins.CollectorPlugin \
    import SnmpPlugin, GetTableMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs, RelationshipMap, ObjectMap

class CiscoControllerDHCPPool(SnmpPlugin):
    maptype = 'ControllerDHCPPool'

    relname = 'dhcpPools'
    modname = 'ZenPacks.daviswr.WirelessController.DHCPPool'

    deviceProperties = SnmpPlugin.deviceProperties + (
        'zWlanDhcpIgnoreNames',
        'zWlanDhcpIgnoreSubnets',
        )

    agentDhcpScopeEntry = {
        # agentDhcpScopeName
        '.2': 'title',
        # agentDhcpScopeNetwork
        '.4': 'network',
        # agentDhcpScopeNetmask
        '.5': 'netmask',
        # agentDhcpScopePoolStartAddress
        '.6': 'start',
        # agentDhcpScopePoolEndAddress
        '.7': 'end',
        # agentDhcpScopeDefaultRouterAddress1
        '.8': 'router1',
        # agentDhcpScopeDefaultRouterAddress2
        '.9': 'router2',
        # agentDhcpScopeDefaultRouterAddress3
        '.10': 'router3',
        # agentDhcpScopeDnsDomainName
        '.11': 'domain',
        # agentDhcpScopeDnsServerAddress1
        '.12': 'dns1',
        # agentDhcpScopeDnsServerAddress2
        '.13': 'dns2',
        # agentDhcpScopeDnsServerAddress3
        '.14': 'dns3',
        # agentDhcpScopeState
        '.18': 'enabled',
        }

    snmpGetTableMaps = (
        GetTableMap(
            'agentDhcpScopeTable',
            '.1.3.6.1.4.1.14179.1.2.15.1.1',
            agentDhcpScopeEntry
            ),
        )

    def condition(self, device, log):
        ignore = False
        model = str(device.hw.getModelName())
        if model.find('VM') > -1:
            log.info('Cisco Virtual WLC does not support DHCP pools, skipping')
            ignore = True
        return not ignore

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        getdata, tabledata = results

        log.debug('SNMP Tables:\n%s', tabledata)

        agentDhcpScopeTable = tabledata.get('agentDhcpScopeTable')
        if agentDhcpScopeTable is None:
            log.error('Unable to get agentDhcpScopeTable for %s', device.id)
            return None
        else:
            log.debug(
                'agentDhcpScopeTable has %s entries',
                len(agentDhcpScopeTable)
                )

        # Ignore criteria
        ignore_names_regex = getattr(device, 'zWlanDhcpIgnoreNames', '')
        if ignore_names_regex:
            log.info('zWlanDhcpIgnoreNames set to %s', ignore_names_regex)

        ignore_net_text = getattr(device, 'zWlanDhcpIgnoreSubnets', list())
        ignore_nets = list()
        if ignore_net_text:
            log.info(
                'zWlanDhcpIgnoreSubnets set to %s',
                str(ignore_net_text)
                )
            for net in ignore_net_text:
                try:
                    ignore_nets.append(ipaddr.IPNetwork(net))
                except:
                    log.warn('%s is not a valid CIDR address', net)
                    continue

        # DHCP pools
        rm = self.relMap()

        for snmpindex in agentDhcpScopeTable:
            row = agentDhcpScopeTable[snmpindex]
            name = row.get('title', None)
            network = row.get('network', '')

            if name is None:
                continue
            elif ignore_names_regex and re.search(ignore_names_regex, name):
                log.debug(
                    'Skipping DHCP pool %s due to zWlanDhcpIgnoreNames',
                    name
                    )
                continue
            elif self.ip_in_nets(network, ignore_nets):
                log.debug(
                    'Skipping DHCP Pool due to zWlanDhcpIgnoreSubnets',
                    name
                    )
                continue

            log.debug('%s found DHCP pool: %s', self.name(), name)

            # Clean up attributes
            if 'enabled' in row:
                row['enabled'] = True if 1 == row['enabled'] else False

            if 'network' in row and 'netmask' in row:
                cidr = self.maskToBits(row['netmask'])
                row['network'] = '{0}/{1}'.format(row['network'], cidr)

            # DNS servers & default gateways
            dns = list()
            routers = list()
            for num in range(1, 4):
                for attr_type in ['dns', 'router']:
                    attr = '{0}{1}'.format(attr_type, num)
                    if row.get(attr, '0.0.0.0') != '0.0.0.0':
                        if attr_type == 'dns':
                            dns.append(row[attr])
                        elif attr_type == 'router':
                            routers.append(row[attr])

            # Update dictionary and create Object Map
            row.update({
                'snmpindex': snmpindex.strip('.'),
                'id': self.prepId(name),
                'dns': dns,
                'routers': routers,
                })

            rm.append(ObjectMap(
                modname='ZenPacks.daviswr.WirelessController.DHCPPool',
                data=row
                ))

        log.debug('%s RelMap:\n%s', self.name(), str(rm))

        return rm


    def ip_in_nets(self, ip, nets):
        """Determines if an IP address is in a subnet in a list"""
        contains = False
        for net in nets:
            try:
                if net.Contains(ipaddr.IPAddress(ip)):
                    contains = True
                    break
            except:
                log.warn('%s ip not a valid IP address', ip)
                break
        return contains
