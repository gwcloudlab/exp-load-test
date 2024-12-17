import http from 'k6/http';
import { htmlReport } from "https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js";


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
  }
};

// export default function() {
//   http.get(url);
// }

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
