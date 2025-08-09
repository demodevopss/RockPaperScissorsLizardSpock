import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
export let errorRate = new Rate('errors');

// Test configuration
export let options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up to 10 users
    { duration: '5m', target: 10 }, // Stay at 10 users
    { duration: '2m', target: 20 }, // Ramp up to 20 users
    { duration: '5m', target: 20 }, // Stay at 20 users
    { duration: '2m', target: 0 },  // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests must finish within 2s
    http_req_failed: ['rate<0.1'],     // Error rate must be below 10%
    errors: ['rate<0.1'],              // Custom error rate must be below 10%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://192.168.64.153:30080';

export default function() {
  // Test 1: Health Check
  let healthResponse = http.get(`${BASE_URL}/health`);
  let healthCheck = check(healthResponse, {
    'health status is 200': (r) => r.status === 200,
    'health response time < 500ms': (r) => r.timings.duration < 500,
  });
  errorRate.add(!healthCheck);

  sleep(1);

  // Test 2: Swagger UI
  let swaggerResponse = http.get(`${BASE_URL}/swagger/index.html`);
  let swaggerCheck = check(swaggerResponse, {
    'swagger status is 200': (r) => r.status === 200,
    'swagger response time < 1000ms': (r) => r.timings.duration < 1000,
    'swagger contains title': (r) => r.body.includes('Swagger'),
  });
  errorRate.add(!swaggerCheck);

  sleep(1);

  // Test 3: Root redirect
  let rootResponse = http.get(`${BASE_URL}/`);
  let rootCheck = check(rootResponse, {
    'root redirect works': (r) => r.status === 200 || r.status === 302,
    'root response time < 500ms': (r) => r.timings.duration < 500,
  });
  errorRate.add(!rootCheck);

  sleep(2);
}

export function handleSummary(data) {
  return {
    'reports/performance/api-load-test-results.json': JSON.stringify(data, null, 2),
    'reports/performance/api-load-test-summary.html': `
      <!DOCTYPE html>
      <html>
      <head>
        <title>API Load Test Results</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; }
          .metric { margin: 10px 0; padding: 10px; border-left: 4px solid #007cba; }
          .pass { border-left-color: #28a745; }
          .fail { border-left-color: #dc3545; }
        </style>
      </head>
      <body>
        <h1>API Load Test Results</h1>
        <h2>Summary</h2>
        <div class="metric ${data.metrics.http_req_duration.values.p95 < 2000 ? 'pass' : 'fail'}">
          <strong>Response Time (95th percentile):</strong> ${Math.round(data.metrics.http_req_duration.values.p95)}ms
          <br><em>Threshold: < 2000ms</em>
        </div>
        <div class="metric ${data.metrics.http_req_failed.values.rate < 0.1 ? 'pass' : 'fail'}">
          <strong>Error Rate:</strong> ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%
          <br><em>Threshold: < 10%</em>
        </div>
        <div class="metric">
          <strong>Total Requests:</strong> ${data.metrics.http_reqs.values.count}
        </div>
        <div class="metric">
          <strong>Average Response Time:</strong> ${Math.round(data.metrics.http_req_duration.values.avg)}ms
        </div>
      </body>
      </html>
    `,
  };
}
