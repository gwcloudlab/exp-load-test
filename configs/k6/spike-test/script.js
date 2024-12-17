import http from 'k6/http';
import { Trend } from 'k6/metrics';


const url = __ENV.URL;
const exp_dir = __ENV.EXP_DIR;

export const options = {
    stages: [
        { duration: '15s', target: 1 }, // Maintain 200 users
        { duration: '30s', target: 1000 }, // Maintain 100 users
        { duration: '15s', target: 1 }, // Maintain 200 users
        { duration: '30s', target: 500 }, // Maintain 100 users
        { duration: '15s', target: 100 }, // Maintain 100 users
        { duration: '20s', target: 0 },    // Ramp-down to 0 users
        { duration: '15s', target: 100 }, // Maintain 100 users
        { duration: '15s', target: 0 }, // Maintain 100 users
    ],
    summaryTrendStats: ["avg", "max", "min", "med", "p(90)", "p(95)", "p(99)", "p(99.9)", "p(99.99)", "p(99.999)", "count"],
};

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
  console.log(`${record.timestamp},${record.url},${record.method},${record.status},${record.response_time},${record.body_size}`);
}

// export function handleSummary(data) {
//   return {
//     'stdout': textSummary(data, { indent: ' ', enableColors: true }),
//   };
// }