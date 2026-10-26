targetScope = 'resourceGroup'

@description('Lowercase globally unique prefix, 3-12 alphanumeric characters.')
@minLength(3)
@maxLength(12)
param prefix string
param location string = resourceGroup().location
param environment string = 'staging'
param apiImage string
param webImage string
param tenantId string
param apiClientId string
param apiAudience string
param copilotClientId string = ''
param foundryProjectEndpoint string
param modelDeployment string
param languageEndpoint string
param searchEndpoint string
param postgresAdmin string = 'assessflowadmin'
@secure()
param postgresPassword string

var suffix = uniqueString(resourceGroup().id, prefix)
var apiName = '${prefix}-api-${suffix}'
var webName = '${prefix}-web-${suffix}'
var postgresName = '${prefix}-pg-${suffix}'

resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: '${prefix}-plan'
  location: location
  sku: { name: 'B1', tier: 'Basic', capacity: 1 }
  kind: 'linux'
  properties: { reserved: true }
}
resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${prefix}-kv-${suffix}'
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    publicNetworkAccess: 'Enabled'
  }
}
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2022-12-01' = {
  name: postgresName
  location: location
  sku: { name: 'Standard_B1ms', tier: 'Burstable' }
  properties: {
    version: '16'
    administratorLogin: postgresAdmin
    administratorLoginPassword: postgresPassword
    storage: { storageSizeGB: 32 }
    backup: { backupRetentionDays: 7, geoRedundantBackup: 'Disabled' }
    highAvailability: { mode: 'Disabled' }
  }
}
resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2022-12-01' = {
  parent: postgres
  name: 'assessflow'
  properties: { charset: 'UTF8', collation: 'en_US.utf8' }
}
resource connectionSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'database-url'
  properties: {
    value: 'postgresql+psycopg://${postgresAdmin}:${uriComponent(postgresPassword)}@${postgres.properties.fullyQualifiedDomainName}:5432/assessflow?sslmode=require'
  }
}
resource api 'Microsoft.Web/sites@2023-12-01' = {
  name: apiName
  location: location
  kind: 'app,linux,container'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'DOCKER|${apiImage}'
      acrUseManagedIdentityCreds: true
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      alwaysOn: true
      healthCheckPath: '/ready'
      appSettings: [
        { name: 'WEBSITES_PORT', value: '5050' }
        { name: 'ASSESSFLOW_MODE', value: 'azure' }
        { name: 'ASSESSFLOW_ENV', value: 'production' }
        { name: 'CORS_ORIGINS', value: 'https://${webName}.azurewebsites.net' }
        { name: 'DATABASE_URL', value: '@Microsoft.KeyVault(SecretUri=${connectionSecret.properties.secretUriWithVersion})' }
        { name: 'ENTRA_TENANT_ID', value: tenantId }
        { name: 'ENTRA_CLIENT_ID', value: apiClientId }
        { name: 'ENTRA_AUDIENCE', value: apiAudience }
        { name: 'ENTRA_COPILOT_CLIENT_ID', value: copilotClientId }
        { name: 'FOUNDRY_PROJECT_ENDPOINT', value: foundryProjectEndpoint }
        { name: 'AZURE_OPENAI_DEPLOYMENT', value: modelDeployment }
        { name: 'AZURE_LANGUAGE_ENDPOINT', value: languageEndpoint }
        { name: 'AZURE_SEARCH_ENDPOINT', value: searchEndpoint }
        { name: 'AZURE_SEARCH_INDEX', value: 'assessflow-policies' }
      ]
    }
  }
  tags: { application: 'AssessFlow', environment: environment }
}
resource web 'Microsoft.Web/sites@2023-12-01' = {
  name: webName
  tags: { application: 'AssessFlow', environment: environment }
  location: location
  kind: 'app,linux,container'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'DOCKER|${webImage}'
      acrUseManagedIdentityCreds: true
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      appSettings: [{ name: 'WEBSITES_PORT', value: '8080' }]
    }
  }
}
// Allow only this app's current outbound addresses. Reconcile after plan/network changes.
module databaseFirewall './database-firewall.bicep' = {
  name: '${prefix}-database-firewall'
  params: {
    serverName: postgres.name
    outboundIps: split(api.properties.outboundIpAddresses, ',')
  }
}
output apiUrl string = 'https://${api.properties.defaultHostName}'
output webUrl string = 'https://${web.properties.defaultHostName}'
output apiPrincipalId string = api.identity.principalId
output webPrincipalId string = web.identity.principalId
output vaultId string = vault.id
output databaseHost string = postgres.properties.fullyQualifiedDomainName
