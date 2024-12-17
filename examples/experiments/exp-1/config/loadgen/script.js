import http from 'k6/http';
import { Trend } from 'k6/metrics';

const url = __ENV.URL;
const exp_dir = __ENV.EXP_DIR;

export const options = {
  scenarios: {
    open_model: {
      executor: 'constant-arrival-rate',
      rate: 100, // Number of iterations per time unit
      timeUnit: '1s', // Time unit for the rate
      duration: '60s',
      preAllocatedVUs: 100, // Number of VUs to pre-allocate
      maxVUs: 200, // Maximum number of VUs to allow
    }
  },
  summaryTrendStats: ["avg", "max", "min", "med", "p(90)", "p(95)", "p(99)", "p(99.9)", "p(99.99)", "p(99.999)", "count"],
};

// export default function() {
//   http.get(url);
// }

const customTrend = new Trend('custom_trend');

export default function() {
  const res = http.get(url);
  const record = {
    timestamp: Math.floor(Date.now() / 1000),
    url: url,
    method: 'GET',
    status: res.status,
    response_time: res.timings.duration,
    body_size: res.body.length,
  };
  customTrend.add(res.timings.duration);
  console.log(`${record.timestamp},${record.url},${record.method},${record.status},${record.response_time},${record.body_size}`);
}
