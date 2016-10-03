__doc__ = """CiscoAP

models access points and AP groups from a Cisco Wireless LAN Controller
(WLC) running AireOS

"""

import ipaddr
import re

from Products.DataCollector.plugins.CollectorPlugin \
    import SnmpPlugin, GetTableMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs, RelationshipMap, ObjectMap

class CiscoAP(SnmpPlugin):
    maptype = 'CiscoAP'

    deviceProperties = SnmpPlugin.deviceProperties + (
        'zWlanApGroupIgnoreNames',
        'zWlanApIgnoreModels',
        'zWlanApIgnoreNames',
        'zWlanApIgnoreSubnets',
        )

    bsnAPGroupsVlanEntry = {
        '.1': 'bsnAPGroupsVlanName',
        '.2': 'bsnAPGroupsVlanDescription',
        '.20': 'bsnAPGroupsVlanRowStatus',
        }

    bsnAPEntry = {
        '.1': 'bsnAPDot3MacAddress',
        '.2': 'bsnAPNumOfSlots',
        '.3': 'bsnAPName',
        '.4': 'bsnAPLocation',
        '.6': 'bsnAPOperationStatus',
        '.8': 'bsnAPSoftwareVersion',
        '.9': 'bsnAPBootVersion',
        '.16': 'bsnAPModel',
        '.17': 'bsnAPSerialNumber',
        '.19': 'bsnApIpAddress',
        '.26': 'bsnAPNetmask',
        '.27': 'bsnAPGateway',
        '.30': 'bsnAPGroupVlanName',
        '.31': 'bsnAPIOSVersion',
        '.33': 'bsnAPEthernetMacAddress',
        '.37': 'bsnAPAdminStatus',
        }

    clcCdpApCacheEntry = {
        '.2': 'clcCdpApCacheApName',
        '.6': 'clcCdpApCacheNeighName',
        '.7': 'clcCdpApCacheNeighAddressType',
        '.8': 'clcCdpApCacheNeighAddress',
        '.9': 'clcCdpApCacheNeighInterface',
        '.12': 'clcCdpApCachePlatform',
        }

    bsnAPIfEntry = {
        '.1': 'bsnAPIfSlotId',
        '.2': 'bsnAPIfType',
        '.3': 'bsnAPIfPhyChannelAssignment',
        '.4': 'bsnAPIfPhyChannelNumber',
        '.7': 'bsnAPIfPhyAntennaMode',
        '.8': 'bsnAPIfPhyAntennaType',
        '.9': 'bsnAPIfPhyAntennaDiversity',
        '.12': 'bsnAPIfOperStatus',
        '.20': 'bsnAPIfAntennaGain',
        '.34': 'bsnAPIfAdminStatus',
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
            'clcCdpApCacheTable',
            '.1.3.6.1.4.1.9.9.623.1.3.1.1',
            clcCdpApCacheEntry
            ),
        GetTableMap(
            'bsnAPIfTable',
            '.1.3.6.1.4.1.14179.2.2.2.1',
            bsnAPIfEntry
            ),
        )


    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        maps = list()
        getdata, tabledata = results

        # Check for empty tables
        # There's probably a better way to do this
        bsnAPGroupsVlanTable = tabledata.get('bsnAPGroupsVlanTable')
        if bsnAPGroupsVlanTable is None:
            log.error('Unable to get bsnAPGroupsVlanTable from %s', device.id)
            return None
        else:
            log.debug(
                'bsnAPGroupsVlanTable has %s entries',
                str(len(bsnAPGroupsVlanTable))
                )

        bsnAPTable = tabledata.get('bsnAPTable')
        if bsnAPTable is None:
            log.error('Unable to get bsnAPTable from %s', device.id)
            return None
        else:
            log.debug('bsnAPTable has %s entries', str(len(bsnAPTable)))

        clcCdpApCacheTable = tabledata.get('clcCdpApCacheTable')
        if clcCdpApCacheTable is None:
            # Not fatal
            log.warning('Unable to get clcCdpApCacheTable from %s', device.id)
        else:
            log.debug(
                'clcCdpApCacheTable has %s entries',
                str(len(clcCdpApCacheTable))
                )

        bsnAPIfTable = tabledata.get('bsnAPIfTable')
        if bsnAPIfTable is None:
            # Not fatal... ?
            log.warning('Unable to get bsnAPIfTable from %s', device.id)
        else:
            log.debug('bsnAPIfTable has %s entries', str(len(bsnAPIfTable)))


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
            name = row.get('bsnAPGroupsVlanName', None)

            if name is None:
                continue
            elif ignore_group_regex and re.match(ignore_group_regex, name):
                log.debug(
                    '%s skipping AP Group %s due to zWlanApGroupIgnoreNames',
                    self.name(),
                    name
                    )
                continue

            log.debug('%s found AP Group: %s', self.name(), name)

            row.update({
                'snmpindex': snmpindex.strip('.'),
                'id': self.prepId(name),
                'title': name,
                'access_points': dict(),
                })

            ap_groups[name] = row


        # Access Points
        ap_radios = dict()
        for snmpindex in bsnAPTable:
            skip_net = False
            row = bsnAPTable[snmpindex]
            name = row.get('bsnAPName', None)
            model = row.get('bsnAPModel', '')
            ip = row.get('bsnApIpAddress', '')
            group = row.get('bsnAPGroupVlanName', 'default-group')

            if name is None:
                continue
            elif ignore_ap_regex and re.match(ignore_ap_regex, name):
                log.debug(
                    '%s skipping AP %s due to zWlanApIgnoreNames',
                    self.name(),
                    name
                    )
                continue
            elif model in ignore_model_list:
                log.debug(
                    '%s skipping AP %s due to zWlanApIgnoreModels',
                    self.name(),
                    name
                    )
                continue

            for net in ignore_nets:
                if ip and net.Contains(ipaddr.IPAddress(ip)):
                    skip_net = True
                    break
            if skip_net:
                log.debug(
                    '%s skipping AP due to zWlanApIgnoreSubnets',
                    self.name(),
                    name
                    )
                continue

            log.debug('%s found AP: %s in group %s', self.name(), name, group)

            # Clean up some values
            macs = [
                'bsnAPDot3MacAddress',
                'bsnAPEthernetMacAddress',
                ]
            for attr in macs:
                if attr in row:
                    row[attr] = self.asmac(row[attr])

            if 'bsnAPModel' in row:
                row['bsnAPModel'] = row['bsnAPModel'].strip(' ')

            # AP CDP neighbor
            cdpindex = '{}.1'.format(snmpindex)
            if clcCdpApCacheTable and cdpindex in clcCdpApCacheTable:
                cdp_entry = clcCdpApCacheTable[cdpindex]
                inet_type = cdp_entry.get('clcCdpApCacheNeighAddressType', '')
                if inet_type and 1 == inet_type:
                    cdp_entry['clcCdpApCacheNeighAddress'] = self.asip(cdp_entry['clcCdpApCacheNeighAddress'])
                row.update(clcCdpApCacheTable[cdpindex])

            row.update({
                'snmpindex': snmpindex.strip('.'),
                'id': self.prepId(name),
                'title': name,
                })

            if group not in ap_groups:
                log.info('AP %s in unknown group %s', name, group)
                ap_groups[group] = {
                    'id': self.prepId(group),
                    'title': name,
                    }

            ap_groups[group]['access_points'][name] = row
            ap_radios[snmpindex.strip('.')] = dict()


        # AP Radios
        for snmpindex in bsnAPIfTable:
            row = bsnAPIfTable[snmpindex]
            ap_index = '.'.join(snmpindex.split('.')[:-1]).strip('.')
            radio_index = snmpindex.replace(ap_index, '').strip('.')

            # Could rely on enums in the yaml
            # but this should make human-readable values
            # available in zendmd, etc?
            attr_map = dict()
            attr_map['bsnAPIfType'] = {
                1: '2.4 GHz',
                2: '5 GHz',
                }

            attr_map['bsnAPIfPhyAntennaDiversity'] = {
                0: 'Connector A',
                1: 'Connector B',
                255: 'Enabled',
                }

            attr_map['bsnAPIfPhyAntennaMode'] = {
                1: 'Sector A',
                2: 'Sector B',
                3: 'Omnidirectional',
                99: 'Not Applicable',
                }

            attr_map['bsnAPIfPhyAntennaType'] = {
                1: 'Internal',
                2: 'External',
                }

            attr_map['bsnAPIfPhyChannelAssignment'] = {
                1: 'Automatic',
                2: 'Customized',
                }

            for attr in attr_map:
                if attr in row:
                    row[attr] = attr_map[attr].get(row[attr], row[attr])

            # Gain is reported in multiples of 0.5 dBm
            if 'bsnAPIfAntennaGain' in row:
                row['bsnAPIfAntennaGain'] = row['bsnAPIfAntennaGain']*0.5

            log.debug(
                '%s found radio %s for AP index %s',
                self.name(),
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
                compname='apGroups/{}'.format(group_id),
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
                    radio['title'] = '{0} Radio {1}'.format(
                        ap_name,
                        radio_index,
                        )
                    radio_rm.append(ObjectMap(
                        modname='ZenPacks.daviswr.WirelessController.CiscoAPRadio',
                        data=radio
                        ))
                # Append this AP's radio RelMap
                radio_rm_list.append(radio_rm)

            # Append this group's AP RelMap
            ap_rm_list.append(ap_rm)

        maps.append(group_rm)
        maps += ap_rm_list
        maps += radio_rm_list

        return maps
