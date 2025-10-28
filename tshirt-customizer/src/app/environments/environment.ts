export const environment = {
    production: false,
    apiUrl: 'http://localhost:5001', // Factory monitoring API
    factoryId: 'tshirt-factory-001', // Generated factory ID
    factoryType: 'textile_tshirt',
    mqttBroker: 'ws://localhost:9001', // MQTT WebSocket
    mqttTopicPrefix: 'factory/tshirt-factory-001',
    workflows: {
      standard: 'standard-tshirt-production',
      premium: 'premium-tshirt-production',
      custom: 'custom-print-tshirt'
    }
   };