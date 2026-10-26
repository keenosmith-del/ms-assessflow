param serverName string
param outboundIps array
resource server 'Microsoft.DBforPostgreSQL/flexibleServers@2022-12-01' existing = {
  name: serverName
}
resource firewall 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2022-12-01' = [for (ip, i) in outboundIps: {
  parent: server
  name: 'api-egress-${i}'
  properties: { startIpAddress: ip, endIpAddress: ip }
}]
