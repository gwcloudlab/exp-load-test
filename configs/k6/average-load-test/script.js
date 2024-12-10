import http from 'k6/http';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';


const url = __ENV.URL;
const exp_dir = __ENV.EXP_DIR;

export const options = {
    stages: [
        { duration: '20s', target: 100 },  // Ramp-up from 1 to 100 users
        { duration: '30s', target: 100 }, // Maintain 100 users
        { duration: '5s', target: 0 },    // Ramp-down to 0 users
    ],
};

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