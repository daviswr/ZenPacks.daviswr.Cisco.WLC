__doc__ = """CiscoControllerVLAN

models VLAN interfaces from a Cisco Wireless LAN Controller 
(WLC) running AireOS

"""

import ipaddr
import re

from Products.DataCollector.plugins.CollectorPlugin \
    import SnmpPlugin, GetTableMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs, RelationshipMap, ObjectMap

class CiscoControllerVLAN(SnmpPlugin):
    maptype = 'ControllerVLAN'

    relname = 'vlanInterfaces'
    modname = 'ZenPacks.daviswr.WirelessController.VlanInterface'

    deviceProperties = SnmpPlugin.deviceProperties + (
        'zWlanInterfaceIgnoreNames',
        'zWlanInterfaceIgnoreSubnets',
        'zWlanInterfaceIgnoreVlans',
        )

    agentInterfaceConfigEntry = {
        # agentInterfaceName
        '.1': 'title',
        # agentInterfaceVlanId
        '.2': 'vlan',
        # agentInterfaceMacAddress
        '.4': 'mac',
        # agentInterfaceIPAddress
        '.5': 'ip',
        # agentInterfaceIPNetmask
        '.6': 'netmask',
        }

    snmpGetTableMaps = (
        GetTableMap(
            'agentInterfaceConfigTable',
            '.1.3.6.1.4.1.14179.1.2.13.1',
            agentInterfaceConfigEntry
            ),
        )

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        maps = list()
        getdata, tabledata = results

        log.debug('SNMP Tables:\n%s', tabledata)

        agentInterfaceConfigTable = tabledata.get('agentInterfaceConfigTable')
        if agentInterfaceConfigTable is None:
            log.error(
                'Unable to get agentInterfaceConfigTable from %s',
                device.id
                )
            return None
        else:
            log.debug(
                'agentInterfaceConfigTable has %s entries',
                len(agentInterfaceConfigTable)
                )

        # Ignore critera
        ignore_names_regex = getattr(device, 'zWlanInterfaceIgnoreNames', '')
        if ignore_names_regex:
            log.info('zWlanInterfaceIgnoreNames set to %s', ignore_names_regex)

        ignore_net_text = getattr(device, 'zWlanInterfaceIgnoreSubnets', list())
        ignore_nets = list()
        if ignore_net_text:
            log.info(
                'zWlanInterfaceIgnoreSubnets set to %s',
                str(ignore_net_text)
                )
            for net in ignore_net_text:
                try:
                    ignore_nets.append(ipaddr.IPNetwork(net))
                except:
                    log.warn('%s is not a valid CIDR address', net)
                    continue

        ignore_vlan_list = getattr(device, 'zWlanInterfaceIgnoreVlans', list())
        if ignore_vlan_list:
            log.info(
                'zWlanInterfaceIgnoreVlans set to %s',
                str(ignore_vlan_list)
                )

        # VLAN Interfaces
        rm = self.relMap()

        for snmpindex in agentInterfaceConfigTable:
            row = agentInterfaceConfigTable[snmpindex]
            name = row.get('title', None)
            ip = row.get('ip', None)
            vlan = row.get('vlan', None)

            if name is None:
                continue
            elif ignore_names_regex and re.search(ignore_names_regex, name):
                log.debug(
                    'Skipping VLAN interface %s due to zWlanInterfaceIgnoreNames',
                    name
                    )
                continue
            elif self.ip_in_nets(ip, ignore_nets):
                log.debug(
                    'Skipping VLAN interface %s due to zWlanInterfaceIgnoreSubnets',
                    name
                    )
                continue
            elif str(vlan) in ignore_vlan_list:
                log.debug(
                    'Skipping VLAN interface %s due to zWlanInterfaceIgnoreVlans',
                    name
                    )
                continue

            # Clean up attributes
            if ip and 'netmask' in row:
                cidr = self.maskToBits(row['netmask'])
                row['ip'] = '{0}/{1}'.format(ip, cidr)

            if 'mac' in row:
                row['mac'] = self.asmac(row.get('mac'))

            row['id'] = self.prepId('vlan_{}'.format(name).replace('-', '_'))
            row['snmpindex'] = snmpindex.strip('.')
            log.debug('Found VLAN interface: %s', name)

            rm.append(ObjectMap(
                modname='ZenPacks.daviswr.WirelessController.VlanInterface',
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
