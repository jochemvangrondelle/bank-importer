import axios from "axios";
import { API_CONFIG } from "../config/settings";

// Create axios instance
const axiosInstance = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export default axiosInstance;
