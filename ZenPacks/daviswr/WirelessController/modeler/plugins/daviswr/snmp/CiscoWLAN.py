__doc__ = """CiscoWLAN

models WLANs/SSIDs from a Cisco Wireless LAN Controller (WLC) running AireOS

"""

import re

from Products.DataCollector.plugins.CollectorPlugin \
    import SnmpPlugin, GetTableMap
from Products.DataCollector.plugins.DataMaps \
    import MultiArgs, RelationshipMap, ObjectMap

class CiscoWLAN(SnmpPlugin):
    maptype = 'CiscoWLAN'

    deviceProperties = SnmpPlugin.deviceProperties + (
        'zWlanWlanIgnoreNames',
        )

    bsnDot11EssEntry = {
        # bsnDot11EssSsid
        '.2': 'title',
        # bsnDot11EssMacFiltering
        '.5': 'mac_filter',
        # bsnDot11EssAdminStatus
        '.6': 'enabled',
        # bsnDot11EssStaticWEPSecurity
        '.8': 'wep',
        # bsnDot11Ess8021xSecurity
        '.13': 'wep_dot1x',
        # bsnDot11EssWebSecurity
        '.29': 'webauth',
        # bsnDot11EssDhcpServerIpAddress
        '.33': 'dhcp',
        # bsnDot11EssNumberOfMobileStations
        '.38': 'clients',
        # bsnDot11EssBroadcastSsid
        '.51': 'broadcast',
        # bsnDot11EssRadiusAuthPrimaryServer
        '.95': 'radauth1',
        # bsnDot11EssRadiusAuthSecondaryServer
        '.96': 'radauth2',
        # bsnDot11EssRadiusAuthTertiaryServer
        '.97': 'radauth3',
        # bsnDot11EssRadiusAcctPrimaryServer
        '.98': 'radacct1',
        # bsnDot11EssRadiusAcctSecondaryServer
        '.99': 'radacct2',
        # bsnDot11EssRadiusAcctTertiaryServer
        '.100': 'radacct3',
        }

    cLWlanConfigEntry = {
        # cLWlanProfileName
        '.3': 'profile',
        # cWlanSsid
        '.4': 'ssid',
        # cLWlanIsWired
        '.7': 'wired',
        # cLWlanLanSubType
        '.25': 'subtype',
        }

    cLWSecDot11EssCckmEntry = {
        # cLWSecDot11EssCckmWpa1Security
        '.2': 'wpa1',
        # cLWSecDot11EssCckmWpa1EncType
        '.3': 'wpa1_type',
        # cLWSecDot11EssCckmWpa2Security
        '.4': 'wpa2',
        # cLWSecDot11EssCckmWpa2EncType
        '.5': 'wpa2_type',
        # cLWSecDot11EssCckmKeyMgmtMode
        '.6': 'key_mgmt',
        }

    cLWSecDot11EssCkipEntry = {
        # cLWSecDot11EssCkipSecurity
        '.1': 'ckip',
        }

    # More or less modeling the controller's LDAP servers, too
    cldlServerEntry = {
        # cldlServerAddressType
        '.2': 'ip_type',
        # cldlServerAddress
        '.3': 'ip',
        # cldlServerPortNum
        '.4': 'port',
        }

    cldlWlanLdapEntry = {
        # cldlWlanLdapPrimaryServerIndex
        '.1': 'ldap1',
        # cldlWlanLdapSecondaryServerIndex
        '.2': 'ldap2',
        # cldlWlanLdapTertiaryServerIndex
        '.3': 'ldap3',
        }

    snmpGetTableMaps = (
        GetTableMap(
            'bsnDot11EssTable',
            '.1.3.6.1.4.1.14179.2.1.1.1',
            bsnDot11EssEntry
            ),
        GetTableMap(
            'cLWlanConfigTable',
            '.1.3.6.1.4.1.9.9.512.1.1.1.1',
            cLWlanConfigEntry
            ),
        GetTableMap(
            'cLWSecDot11EssCckmTable',
            '.1.3.6.1.4.1.9.9.521.1.1.1.1',
            cLWSecDot11EssCckmEntry
            ),
        GetTableMap(
            'cLWSecDot11EssCkipTable',
            '.1.3.6.1.4.1.9.9.521.1.1.2.1',
            cLWSecDot11EssCkipEntry
            ),
        GetTableMap(
            'cldlServerTable',
            '.1.3.6.1.4.1.9.9.614.1.1.1.1',
            cldlServerEntry
            ),
        GetTableMap(
            'cldlWlanLdapTable',
            '.1.3.6.1.4.1.9.9.614.1.1.2.1',
            cldlWlanLdapEntry
            ),
        )

    def process(self, device, results, log):
        """collect snmp information from this device"""
        log.info('processing %s for device %s', self.name(), device.id)
        maps = list()
        getdata, tabledata = results

        log.debug('SNMP Tables:\n%s', tabledata)

        bsnDot11EssTable = tabledata.get('bsnDot11EssTable')
        if bsnDot11EssTable is None:
            log.error('Unable to get bsnDot11EssTable from %s', device.id)
            return None
        else:
            log.debug(
                'bsnDot11EssTable has %s entries',
                str(len(bsnDot11EssTable))
                )

        cLWlanConfigTable = tabledata.get('cLWlanConfigTable')
        if cLWlanConfigTable is None:
            log.error('Unable to get cLWlanConfigTable from %s', device.id)
            return None
        else:
            log.debug(
                'cLWlanConfigTable has %s entries',
                str(len(cLWlanConfigTable))
                )

        cLWSecDot11EssCckmTable = tabledata.get('cLWSecDot11EssCckmTable')
        if cLWSecDot11EssCckmTable is None:
            log.error(
                'Unable to get cLWSecDot11EssCckmTable from %s',
                device.id
                )
            return None
        else:
            log.debug(
                'cLWSecDot11EssCckmTable has %s entries',
                str(len(cLWSecDot11EssCckmTable))
                )

        cLWSecDot11EssCkipTable = tabledata.get('cLWSecDot11EssCkipTable')
        if cLWSecDot11EssCkipTable is None:
            log.error(
                'Unable to get cLWSecDot11EssCkipTable from %s',
                device.id
                )
            return None
        else:
            log.debug(
                'cLWSecDot11EssCkipTable has %s entries',
                str(len(cLWSecDot11EssCkipTable))
                )

        cldlServerTable = tabledata.get('cldlServerTable', dict())
        if not cldlServerTable:
            # Not fatal
            log.warn('Unable to get cldlServerTable from %s', device.id)
        else:
            log.debug(
                'cldlServerTable has %s entries',
                str(len(cldlServerTable))
                )

        cldlWlanLdapTable = tabledata.get('cldlWlanLdapTable', dict())
        if not cldlWlanLdapTable:
            # Not fatal
            log.warn('Unable to get cldlWlanLdapTable from %s', device.id)
        else:
            log.debug(
                'cldlWlanLdapTable has %s entries',
                str(len(cldlWlanLdapTable))
                )

        # Ignore criteria
        ignore_names_regex = getattr(device, 'zWlanWlanIgnoreNames', '')
        if ignore_names_regex:
            log.info('zWlanWlanIgnoreNames set to %s', ignore_names_regex)

        # WLANs
        rm = RelationshipMap(
            relname='wlans',
            modname='ZenPacks.daviswr.WirelessController.WLAN'
            )

        for snmpindex in bsnDot11EssTable:
            row = bsnDot11EssTable[snmpindex]
            name = row.get('title', None)

            if name is None:
                continue
            elif ignore_names_regex and re.search(ignore_names_regex, name):
                log.debug(
                    'Skipping WLAN %s due to zWlanWlanIgnoreNames',
                    name
                    )
                continue

            log.debug('Found WLAN: %s', name)

            # Merge with other tables, indexing is the same
            row.update(cLWlanConfigTable.get(snmpindex, dict()))
            row.update(cLWSecDot11EssCckmTable.get(snmpindex, dict()))
            row.update(cLWSecDot11EssCkipTable.get(snmpindex, dict()))
            row.update(cldlWlanLdapTable.get(snmpindex, dict()))

            # Clean up attributes
            booleans = [
                'broadcast',
                'ckip',
                'enabled',
                'webauth',
                'wep',
                'wep_dot1x',
                'wired',
                'wpa1',
                'wpa2',
                ]

            for attr in booleans:
                if attr in row:
                    row[attr] = True if 1 == row[attr] else False

            attr_map = dict()
            attr_map['key_mgmt'] = {
                0x00: '',
                0x20: 'PSK',
                0x40: 'CCKM',
                0x80: '802.1x',
                0xc0: '802.1x+CCKM'
                }

            attr_map['subtype'] = {
                1: 'CiscoWLAN',
                2: 'CiscoGuestLAN',
                3: 'CiscoRemoteLAN',
                }

            # TKIP is a protocol using the RC4 cipher
            # AES is the cipher used by the CCMP protocol
            # so it's not technically comparing the same things
            attr_map['wpa1_type'] = {
                0x00: '',
                0x40: 'AES',
                0x80: 'TKIP',
                0xc0: 'AES+TKIP',
                }

            attr_map['wpa2_type'] = attr_map['wpa1_type']

            for attr in attr_map:
                if attr in row:
                    value = row[attr]
                    if attr in ['key_mgmt', 'wpa1_type', 'wpa2_type']:
                        # Hex dict keys get stored as integers
                        value = int(ord(value))
                    row[attr] = attr_map[attr].get(value)

            if row.get('dhcp') == '0.0.0.0':
                del row['dhcp']

            # Security type
            security = 'Open'
            key_mgmt = row.get('key_mgmt', '')

            # Network is WPA
            if key_mgmt:
                mode = ''
                wpa1 = row.get('wpa1')
                wpa2 = row.get('wpa2')
                wpa1_type = row.get('wpa1_type')
                wpa2_type = row.get('wpa2_type')
                if wpa1 and wpa1_type:
                    mode = 'WPA-{}'.format(wpa1_type)
                if wpa2 and wpa2_type:
                    if wpa2_type == wpa1_type:
                        mode = mode.replace('-{}'.format(wpa2_type), '')
                    mode += '/WPA2-{}'.format(wpa2_type)

                mode = mode.lstrip('/')
                security = '{0} {1}'.format(mode, key_mgmt)

            # Network is open, WEP, or CKIP
            else:
                if row.get('ckip'):
                    security = 'CKIP'
                if row.get('wep'):
                    security = 'WEP'
                if row.get('wep_dot1x'):
                    security = 'WEP 802.1x'

            if row.get('webauth'):
                security += ' + WebAuth'

            if row.get('mac_filter'):
                security += ' + MAC Filter'

            # RADIUS servers
            acct = list()
            auth = list()
            for num in range(1, 4):
                for rad in ['acct', 'auth']:
                    attr = 'rad{0}{1}'.format(rad, num)
                    if row.get(attr, 'none') != 'none':
                        server = row[attr].replace(' ', ':')
                        if 'acct' == rad:
                            acct.append(server)
                        elif 'auth' == rad:
                            auth.append(server)

            # LDAP servers
            ldap = list()
            ldap_entry = ''
            for num in range(1, 4):
                attr = 'ldap{}'.format(num)
                if str(row.get(attr, 0)) in cldlServerTable:
                    server = cldlServerTable[str(row[attr])]
                    if 'ip' in server:
                        if server.get('ip_type', 0) == 1:
                            ldap_entry = self.asip(server['ip'])
                        else:
                            ldap_entry = str(server['ip'])
                        if 'port' in server:
                            ldap_entry += ':{}'.format(server['port'])
                        ldap.append(ldap_entry)

            # Update dictionary and create Object Map
            row.update({
                'snmpindex': snmpindex.strip('.'),
                'id': self.prepId(row.get('profile', name)),
                'ldap': ldap,
                'radAcct': acct,
                'radAuth': auth,
                'security': security,
                })

            class_name = 'ZenPacks.daviswr.WirelessController.{}'.format(
                row.get('subtype', 'CiscoWLAN')
                )

            rm.append(ObjectMap(modname=class_name, data=row))

        maps.append(rm)
        log.debug('%s RelMaps:\n', maps)

        return maps
