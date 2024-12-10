import axios from 'axios';

const API_URL = process.env.REACT_APP_API_GATEWAY_URL;

class FileService {
  async listFiles() {
    const token = localStorage.getItem('token');
    const response = await axios.get(`${API_URL}/files`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.data;
  }

  async generateFile() {
    const token = localStorage.getItem('token');
    const response = await axios.post(`${API_URL}/files/generate`, {}, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.data;
  }

  async deleteFile(fileName) {
    const token = localStorage.getItem('token');
    await axios.delete(`${API_URL}/files/${fileName}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
  }
}

export default new FileService();