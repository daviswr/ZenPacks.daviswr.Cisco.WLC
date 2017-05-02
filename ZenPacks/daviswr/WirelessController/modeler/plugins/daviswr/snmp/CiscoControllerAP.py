# pylint: disable=C0301

__doc__ = """CiscoControllerAP

models access points and AP groups from a Cisco Wireless LAN Controller
(WLC) running AireOS

"""

import ipaddr
import re

from Products.DataCollector.plugins.CollectorPlugin \
    import SnmpPlugin, GetTableMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs, RelationshipMap, ObjectMap


class CiscoControllerAP(SnmpPlugin):
    maptype = 'ControllerAP'

    deviceProperties = SnmpPlugin.deviceProperties + (
        'zWlanApGroupIgnoreNames',
        'zWlanApIgnoreModels',
        'zWlanApIgnoreNames',
        'zWlanApIgnoreSubnets',
        )

    bsnAPGroupsVlanEntry = {
        # bsnAPGroupsVlanName
        '.1': 'title',
        # bsnAPGroupsVlanDescription
        '.2': 'description',
        }

    bsnAPEntry = {
        # bsnAPDot3MacAddress
        '.1': 'radioMac',
        # bsnAPNumOfSlots
        '.2': 'radioCount',
        # bsnAPName
        '.3': 'title',
        # bsnAPLocation
        '.4': 'location',
        # bsnAPMonitorOnlyMode
        '.5': 'mode',
        # bsnAPSoftwareVersion
        '.8': 'swVersion',
        # bsnAPBootVersion
        '.9': 'bootVersion',
        # bsnAPModel
        '.16': 'model',
        # bsnAPSerialNumber
        '.17': 'serial',
        # bsnApIpAddress
        '.19': 'ip',
        # bsnAPNetmask
        '.26': 'netmask',
        # bsnAPGateway
        '.27': 'gateway',
        # bsnAPGroupVlanName
        '.30': 'group',
        # bsnAPIOSVersion
        '.31': 'iosVersion',
        # bsnAPEthernetMacAddress
        '.33': 'mac',
        # bsnAPAdminStatus
        '.37': 'enabled',
        }

    cLApLinkLatencyEntry = {
        # cLApLinkLatencyEnable
        '.1': 'latency',
        }

    cLApEntry = {
        # cLApEntPhysicalIndex
        '.4': 'ent_idx',
        }

    entPhysicalEntry = {
        # entPhysicalHardwareRev
        '.8': 'hwVersion',
        }

    clcCdpApCacheEntry = {
        # clcCdpApCacheNeighName
        '.6': 'neighborName',
        # clcCdpApCacheNeighAddressType
        '.7': 'neighborIpType',
        # clcCdpApCacheNeighAddress
        '.8': 'neighborIp',
        # clcCdpApCacheNeighInterface
        '.9': 'neighborInterface',
        # clcCdpApCachePlatform
        '.12': 'neighborModel',
        }

    bsnAPIfEntry = {
        # bsnAPIfType
        '.2': 'band',
        # bsnAPIfPhyChannelAssignment
        '.3': 'assignment',
        # bsnAPIfPhyChannelNumber
        '.4': 'channel',
        # bsnAPIfPhyAntennaMode
        '.7': 'mode',
        # bsnAPIfPhyAntennaType
        '.8': 'antenna',
        # bsnAPIfPhyAntennaDiversity
        '.9': 'diversity',
        # bsnAPIfAntennaGain
        '.20': 'gain',
        # bsnAPIfAdminStatus
        '.34': 'enabled',
        }

    cLApDot11IfEntry = {
        # cLApDot11nSupport
        '.4': '11n',
        # cLAp11nChannelBandwidth
        '.5': 'width',
        # No entry in CISCO-LWAPP-AP-MIB
        # cLAp11nChannelBandwidth only has values up to 40 MHz
        '.23': 'width_new',
        # No entry in CISCO-LWAPP-AP-MIB
        # cLApExtensionChannel only works for 40 MHz, not 80+
        '.24': 'ext_channel',
        }

    snmpGetTableMaps = (
        GetTableMap(
            'bsnAPGroupsVlanTable',
            '.1.3.6.1.4.1.14179.2.10.2.1',
            bsnAPGroupsVlanEntry
            ),
        GetTableMap(
            'bsnAPTable',
            '.1.3.6.1.4.1.14179.2.2.1.1',
            bsnAPEntry
            ),
        GetTableMap(
            'cLApLinkLatencyTable',
            '.1.3.6.1.4.1.9.9.513.1.5.1.1',
            cLApLinkLatencyEntry
            ),
        GetTableMap(
            'cLApTable',
            '.1.3.6.1.4.1.9.9.513.1.1.1.1',
            cLApEntry,
            ),
        GetTableMap(
            'entPhysicalTable',
            '.1.3.6.1.2.1.47.1.1.1.1',
            entPhysicalEntry
            ),
        GetTableMap(
            'clcCdpApCacheTable',
            '.1.3.6.1.4.1.9.9.623.1.3.1.1',
            clcCdpApCacheEntry
            ),
        GetTableMap(
            'bsnAPIfTable',
            '.1.3.6.1.4.1.14179.2.2.2.1',
            bsnAPIfEntry
            ),
        GetTableMap(
            'cLApDot11IfTable',
            '.1.3.6.1.4.1.9.9.513.1.2.1.1',
            cLApDot11IfEntry
            ),
        )

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        maps = list()
        getdata, tabledata = results

        log.debug('SNMP Tables:\n%s', tabledata)

        bsnAPGroupsVlanTable = tabledata.get('bsnAPGroupsVlanTable')
        log.debug(
            'bsnAPGroupsVlanTable has %s entries',
            len(bsnAPGroupsVlanTable)
            )

        bsnAPTable = tabledata.get('bsnAPTable')
        log.debug('bsnAPTable has %s entries', len(bsnAPTable))

        cLApLinkLatencyTable = tabledata.get('cLApLinkLatencyTable', dict())
        log.debug(
            'cLApLinkLatencyTable has %s entries',
            len(cLApLinkLatencyTable)
            )

        cLApTable = tabledata.get('cLApTable')
        log.debug('cLApTable has %s entries', len(cLApTable))

        entPhysicalTable = tabledata.get('entPhysicalTable')
        log.debug('entPhysicalTable has %s entries', len(entPhysicalTable))

        clcCdpApCacheTable = tabledata.get('clcCdpApCacheTable')
        log.debug(
            'clcCdpApCacheTable has %s entries',
            len(clcCdpApCacheTable)
            )

        bsnAPIfTable = tabledata.get('bsnAPIfTable')
        log.debug('bsnAPIfTable has %s entries', len(bsnAPIfTable))

        cLApDot11IfTable = tabledata.get('cLApDot11IfTable', dict())
        log.debug('cLApDot11IfTable has %s entries', len(cLApDot11IfTable))

        # Ignore criteria
        ignore_group_regex = getattr(device, 'zWlanApGroupIgnoreNames', '')
        if ignore_group_regex:
            log.info(
                'zWlanApGroupIgnoreNames set to %s',
                ignore_group_regex
                )

        ignore_model_list = getattr(device, 'zWlanApIgnoreModels', list())
        if ignore_model_list:
            log.info(
                'zWlanApIgnoreModels set to %s',
                str(ignore_model_list)
                )

        ignore_ap_regex = getattr(device, 'zWlanApIgnoreNames', '')
        if ignore_ap_regex:
            log.info('zWlanApIgnoreNames set to %s', ignore_ap_regex)

        ignore_net_text = getattr(device, 'zWlanApIgnoreSubnets', list())
        ignore_nets = list()
        if ignore_net_text:
            log.info(
                'zWlanApIgnoreSubnets set to %s',
                str(ignore_net_text)
                )
            for net in ignore_net_text:
                try:
                    ignore_nets.append(ipaddr.IPNetwork(net))
                except:
                    log.warn('%s is not a valid CIDR address', net)
                    continue

        # AP Groups
        ap_groups = dict()
        for snmpindex in bsnAPGroupsVlanTable:
            row = bsnAPGroupsVlanTable[snmpindex]
            name = row.get('title', None)

            if name is None:
                continue
            elif ignore_group_regex and re.search(ignore_group_regex, name):
                log.debug(
                    'Skipping AP Group %s due to zWlanApGroupIgnoreNames',
                    name
                    )
                continue

            log.debug('Found AP Group: %s', name)

            row.update({
                'snmpindex': snmpindex.strip('.'),
                'id': self.prepId(name),
                'access_points': dict(),
                })

            ap_groups[name] = row

        # Access Points
        ap_radios = dict()
        for snmpindex in bsnAPTable:
            row = bsnAPTable[snmpindex]
            name = row.get('title', None)
            model = row.get('model', '')
            ip = row.get('ip', '')
            group = row.get('group', 'default-group')

            if name is None:
                continue
            elif ignore_ap_regex and re.search(ignore_ap_regex, name):
                log.debug(
                    'Skipping AP %s due to zWlanApIgnoreNames',
                    name
                    )
                continue
            elif model in ignore_model_list:
                log.debug(
                    'Skipping AP %s due to zWlanApIgnoreModels',
                    name
                    )
                continue
            elif self.ip_in_nets(ip, ignore_nets):
                log.debug(
                    'Skipping AP due to zWlanApIgnoreSubnets',
                    name
                    )
                continue

            log.debug('Found AP: %s in group %s', name, group)

            # Merge other tables with same indexing
            row.update(cLApLinkLatencyTable.get(snmpindex, dict()))
            row.update(cLApTable.get(snmpindex, dict()))

            # Clean up some values
            attr_map = dict()
            attr_map['enabled'] = {
                1: True,
                2: False,
                }

            attr_map['latency'] = attr_map['enabled']

            attr_map['mode'] = {
                0: 'Local',
                1: 'Monitor',
                # (H)REAP
                2: 'FlexConnect',
                3: 'Rogue Detector',
                4: 'Sniffer',
                5: 'Bridge',
                #  CleanAir-enabled models only
                6: 'Spectrum Expert Connect',
                }

            for attr in attr_map:
                if attr in row:
                    row[attr] = attr_map[attr].get(row[attr], row[attr])

            macs = [
                'radioMac',
                'mac',
                ]
            for attr in macs:
                if attr in row:
                    row[attr] = self.asmac(row[attr])

            if model:
                row['model'] = row['model'].strip(' ')

            if 'iosVersion' in row:
                row['iosVersion'] = row['iosVersion'].strip('$')

            # Entity hardware version
            entity = entPhysicalTable.get(str(row.get('ent_idx', 0)), dict())
            row['hwVersion'] = entity.get('hwVersion', None)

            # AP CDP neighbor
            cdpindex = '{0}.1'.format(snmpindex)
            if clcCdpApCacheTable and cdpindex in clcCdpApCacheTable:
                cdp_entry = clcCdpApCacheTable[cdpindex]
                inet_type = cdp_entry.get('neighborIpType', '')
                if inet_type and 1 == inet_type:
                    cdp_entry['neighborIp'] = self.asip(cdp_entry['neighborIp'])  # noqa
                row.update(clcCdpApCacheTable[cdpindex])

            row.update({
                'snmpindex': snmpindex.strip('.'),
                'id': self.prepId(name),
                })

            if group not in ap_groups:
                log.info('AP %s in unknown group %s', name, group)
                ap_groups[group] = {
                    'id': self.prepId(group),
                    'title': group,
                    }

            ap_groups[group]['access_points'][name] = row
            ap_radios[snmpindex.strip('.')] = dict()

        # AP Radios
        for snmpindex in bsnAPIfTable:
            row = bsnAPIfTable[snmpindex]
            ap_index = '.'.join(snmpindex.split('.')[:-1]).strip('.')
            radio_index = snmpindex.replace(ap_index, '').strip('.')

            # Merge with other AP radio table, same indexing
            row.update(cLApDot11IfTable.get(snmpindex, dict()))

            attr_map = dict()
            attr_map['11n'] = {
                1: True,
                2: False,
                }

            attr_map['antenna'] = {
                1: 'Internal',
                2: 'External',
                }

            attr_map['assignment'] = {
                1: 'Automatic',
                2: 'Customized',
                }

            attr_map['band'] = {
                1: '2.4 GHz',
                2: '5 GHz',
                }

            attr_map['diversity'] = {
                # Right?
                0: 'Connector A',
                # Left?
                1: 'Connector B',
                255: 'Enabled',
                }

            attr_map['enabled'] = attr_map['11n']

            attr_map['mode'] = {
                1: 'Sector A',
                2: 'Sector B',
                3: 'Omnidirectional',
                99: 'Not Applicable',
                }

            # Assuming cLApDot11IfEntry.24's lower values are
            # compatible with cLAp11nChannelBandwidth
            attr_map['width'] = {
                1: '5 MHz',
                2: '10 MHz',
                3: '20 MHz',
                4: '40 MHz',
                5: '80 MHz',
                }

            attr_map['width_new'] = attr_map['width']

            for attr in attr_map:
                if attr in row:
                    row[attr] = attr_map[attr].get(row[attr], row[attr])

            # Gain is reported in multiples of 0.5 dBm
            if 'gain' in row:
                row['gain'] = row['gain']*0.5

            # IEEE 802.11 radio type
            row['dot11'] = '802.11'
            if row.get('11n'):
                row['dot11'] += 'n'
            else:
                # Assuming there aren't any more strictly-11b radios out there
                dot11_map = {
                    '2.4 GHz': 'g',
                    '5 GHz': 'a',
                    }
                row['dot11'] += dot11_map.get(row.get('band'), '')

            # Extension Channels
            if len(row.get('ext_channel', '')) > 0:
                row['channel'] = '{0},{1}'.format(
                    row['channel'],
                    row['ext_channel']
                    )
            if 'width_new' in row:
                row['width'] = row['width_new']
            # This assumption will not work when 11ax is released
            # Still no way to detect 11ac (VHT) with a 20- or 40-MHz channel
            if '80 MHz' == row['width'] and '802.11ac' != row['dot11']:
                row['dot11'] = '802.11ac'

            log.debug(
                'Found radio %s for AP index %s',
                radio_index,
                ap_index
                )
            row['snmpindex'] = snmpindex.strip('.')
            ap_radios[ap_index][radio_index] = row

        # Build Relationship Maps
        group_rm = RelationshipMap(
            relname='apGroups',
            modname='ZenPacks.daviswr.WirelessController.APGroup'
            )
        ap_rm_list = list()
        radio_rm_list = list()

        for group_name in ap_groups:
            group_id = self.prepId(group_name)
            group = ap_groups[group_name]
            group_rm.append(ObjectMap(
                modname='ZenPacks.daviswr.WirelessController.APGroup',
                data=group
                ))

            ap_rm = RelationshipMap(
                compname='apGroups/{0}'.format(group_id),
                relname='accessPoints',
                modname='ZenPacks.daviswr.WirelessController.AccessPoint'
                )
            for ap_name in group['access_points']:
                ap_id = self.prepId(ap_name)
                ap = group['access_points'][ap_name]
                ap_rm.append(ObjectMap(
                    modname='ZenPacks.daviswr.WirelessController.CiscoAP',
                    data=ap
                    ))
                radio_rm = RelationshipMap(
                    compname='apGroups/{0}/accessPoints/{1}'.format(
                        group_id,
                        ap_id
                        ),
                    relname='apRadios',
                    modname='ZenPacks.daviswr.WirelessController.APRadio'
                    )
                for radio_index in ap_radios[ap['snmpindex']]:
                    radio = ap_radios[ap['snmpindex']][radio_index]
                    radio['id'] = self.prepId('{0}_{1}'.format(
                        ap_id,
                        radio_index
                        ))
                    radio['title'] = '{0} Slot {1}'.format(
                        ap_name,
                        radio_index
                        )
                    radio_rm.append(ObjectMap(
                        modname='ZenPacks.daviswr.WirelessController.CiscoAPRadio',  # noqa
                        data=radio
                        ))
                # Append this AP's radio RelMap
                radio_rm_list.append(radio_rm)

            # Append this group's AP RelMap
            ap_rm_list.append(ap_rm)

        maps.append(group_rm)
        maps += ap_rm_list
        maps += radio_rm_list
        log.debug('%s RelMaps:\n%s', self.name(), str(maps))

        return maps

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
