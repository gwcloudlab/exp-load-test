import http from 'k6/http';
import { Trend } from 'k6/metrics';


const url = __ENV.URL;
const exp_dir = __ENV.EXP_DIR;

export const options = {
  vus: 3, // Key for Smoke test. Keep it at 2, 3, max 5 VUs
  duration: '30s', // This can be shorter or just a few iterations
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