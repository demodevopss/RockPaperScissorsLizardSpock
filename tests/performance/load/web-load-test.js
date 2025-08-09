import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
export let errorRate = new Rate('errors');
export let pageLoadTime = new Rate('page_load_time');

// Test configuration
export let options = {
  stages: [
    { duration: '30s', target: 5 },  // Ramp up to 5 users
    { duration: '2m', target: 5 },   // Stay at 5 users
    { duration: '30s', target: 10 }, // Ramp up to 10 users
    { duration: '2m', target: 10 },  // Stay at 10 users
    { duration: '30s', target: 0 },  // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'], // 95% of requests must finish within 5s
    http_req_failed: ['rate<0.1'],     // Error rate must be below 10%
    errors: ['rate<0.1'],              // Custom error rate must be below 10%
  },
};

const WEB_URL = __ENV.WEB_URL || 'http://192.168.64.153:30081';

export default function() {
  // Test 1: Load main page
  let startTime = Date.now();
  let mainPageResponse = http.get(WEB_URL);
  let pageLoadCheck = check(mainPageResponse, {
    'main page status is 200': (r) => r.status === 200,
    'main page loads within 5s': (r) => r.timings.duration < 5000,
    'main page contains app div': (r) => r.body.includes('id="app"'),
    'main page contains game title': (r) => r.body.includes('Rock') || r.body.includes('Spock'),
  });
  errorRate.add(!pageLoadCheck);

  sleep(2);

  // Test 2: Load static resources (simulate browser behavior)
  let staticRequests = [
    `${WEB_URL}/_framework/blazor.webassembly.js`,
    `${WEB_URL}/_framework/blazor.boot.json`,
    `${WEB_URL}/css/app.css`,
  ];

  staticRequests.forEach(url => {
    let response = http.get(url);
    let staticCheck = check(response, {
      [`static resource ${url} loads successfully`]: (r) => r.status === 200,
      [`static resource ${url} loads quickly`]: (r) => r.timings.duration < 3000,
    });
    errorRate.add(!staticCheck);
  });

  sleep(1);

  // Test 3: Simulate user interaction patterns
  let userActions = [
    // Simulate loading the game multiple times
    () => {
      let gameResponse = http.get(WEB_URL);
      return check(gameResponse, {
        'game reload successful': (r) => r.status === 200,
        'game reload fast': (r) => r.timings.duration < 3000,
      });
    },
    
    // Simulate challenger page load (if accessible)
    () => {
      let challengerResponse = http.get(`${WEB_URL}/challenger`);
      return check(challengerResponse, {
        'challenger page accessible': (r) => r.status === 200 || r.status === 404, // 404 is OK for SPA
        'challenger page loads quickly': (r) => r.timings.duration < 3000,
      });
    },
  ];

  // Execute random user action
  let randomAction = userActions[Math.floor(Math.random() * userActions.length)];
  let actionSuccess = randomAction();
  errorRate.add(!actionSuccess);

  sleep(3);
}

export function handleSummary(data) {
  return {
    'reports/performance/web-load-test-results.json': JSON.stringify(data, null, 2),
    'reports/performance/web-load-test-summary.html': `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Web Load Test Results</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; }
          .metric { margin: 10px 0; padding: 10px; border-left: 4px solid #007cba; }
          .pass { border-left-color: #28a745; }
          .fail { border-left-color: #dc3545; }
          .chart { width: 100%; height: 200px; border: 1px solid #ddd; margin: 20px 0; }
        </style>
      </head>
      <body>
        <h1>Web Application Load Test Results</h1>
        <h2>Summary</h2>
        <div class="metric ${data.metrics.http_req_duration.values.p95 < 5000 ? 'pass' : 'fail'}">
          <strong>Page Load Time (95th percentile):</strong> ${Math.round(data.metrics.http_req_duration.values.p95)}ms
          <br><em>Threshold: < 5000ms</em>
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
        <div class="metric">
          <strong>Data Transferred:</strong> ${Math.round(data.metrics.data_received.values.count / 1024 / 1024 * 100) / 100} MB
        </div>
        
        <h2>Performance Analysis</h2>
        <p><strong>Blazor WebAssembly Performance:</strong></p>
        <ul>
          <li>Initial load time includes framework download</li>
          <li>Subsequent navigation should be faster (SPA)</li>
          <li>Static resource caching improves performance</li>
        </ul>
      </body>
      </html>
    `,
  };
}
