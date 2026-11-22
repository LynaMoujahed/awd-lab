const app = require('./app');
const Eureka = require('eureka-js-client').Eureka;

const PORT = process.env.PORT || 8083;
const HOST = 'localhost';

const eurekaClient = new Eureka({
  instance: {
    app: 'MEETING',
    instanceId: `meeting:${PORT}`,          // unique per instance
    hostName: HOST,
    ipAddr: '127.0.0.1',
    port: { $: Number(PORT), '@enabled': true },
    vipAddress: 'meeting',
    homePageUrl: `http://${HOST}:${PORT}/`,
    statusPageUrl: `http://${HOST}:${PORT}/info`,
    healthCheckUrl: `http://${HOST}:${PORT}/health`,
    dataCenterInfo: {
      '@class': 'com.netflix.appinfo.InstanceInfo$DefaultDataCenterInfo',
      name: 'MyOwn',
    },
  },
  eureka: {
    host: 'localhost',
    port: 8761,
    servicePath: '/eureka/apps/',
  },
});

app.listen(PORT, () => {
  console.log(`meeting microservice running on http://localhost:${PORT}`);
  console.log(`Swagger UI: http://localhost:${PORT}/swagger-ui`);
  eurekaClient.start((error) => {
    console.log(error ? `Eureka registration failed: ${error}` : 'Registered in Eureka as MEETING');
  });
});

// Unregister cleanly when the process stops
process.on('SIGINT', () => {
  eurekaClient.stop(() => process.exit(0));
});