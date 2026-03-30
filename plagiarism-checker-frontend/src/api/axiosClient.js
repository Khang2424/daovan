import axios from 'axios';

const axiosClient = axios.create({
  baseURL: 'http://localhost:8000', // Đường dẫn tới Backend FastAPI
  headers: {
    'Content-Type': 'application/json',
  },
});

export default axiosClient;