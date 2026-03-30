import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';
import axiosClient from '../api/axiosClient';

// Import các Component con vừa tạo
import Sidebar from '../components/Sidebar';
import ScannerTab from '../components/ScannerTab';
import HistoryTab from '../components/HistoryTab';
import ReportDetail from '../components/ReportDetail';

export default function Dashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('scanner');
  const [error, setError] = useState('');

  // States cho Scanner
  const [selectedFile, setSelectedFile] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const fileInputRef = useRef(null);

  // States cho History & Detail
  const [historyList, setHistoryList] = useState([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [detailedReport, setDetailedReport] = useState(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  // --- CÁC HÀM LOGIC XỬ LÝ (API) ---
  const handleLogout = () => { localStorage.removeItem('access_token'); navigate('/login'); };
  
  const goToScanner = () => { setActiveTab('scanner'); setError(''); };

  const fetchHistory = async () => {
    setActiveTab('history'); setIsLoadingHistory(true); setError('');
    try {
      const token = localStorage.getItem('access_token');
      const response = await axiosClient.get('/api/v1/scan/history', { headers: { Authorization: `Bearer ${token}` } });
      setHistoryList(response.data.data || []);
    } catch (err) { setError('Không thể tải lịch sử quét.'); } 
    finally { setIsLoadingHistory(false); }
  };

  const handleViewDetail = async (reportId) => {
    setActiveTab('report_detail'); setIsLoadingDetail(true); setError(''); setDetailedReport(null);
    try {
      const token = localStorage.getItem('access_token');
      const response = await axiosClient.get(`/api/v1/scan/history/${reportId}`, { headers: { Authorization: `Bearer ${token}` } });
      setDetailedReport(response.data);
    } catch (err) { setError('Không thể tải chi tiết báo cáo.'); } 
    finally { setIsLoadingDetail(false); }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type)) {
        setError('Chỉ hỗ trợ file .pdf hoặc .docx'); setSelectedFile(null); return;
      }
      setSelectedFile(file); setError(''); setScanResult(null);
    }
  };

  const handleScan = async () => {
    if (!selectedFile) return;
    setIsScanning(true); setError('');
    const formData = new FormData(); formData.append('file', selectedFile);
    try {
      const token = localStorage.getItem('access_token');
      const response = await axiosClient.post('/api/v1/scan/file', formData, { headers: { 'Content-Type': 'multipart/form-data', 'Authorization': `Bearer ${token}` } });
      setScanResult(response.data);
    } catch (err) { setError(err.response?.data?.detail || 'Lỗi quét file.'); } 
    finally { setIsScanning(false); }
  };

  // --- GIAO DIỆN LẮP RÁP ---
  return (
    <div className="flex h-screen bg-gray-50">
      
      {/* 1. Thanh Sidebar */}
      <Sidebar activeTab={activeTab} goToScanner={goToScanner} fetchHistory={fetchHistory} handleLogout={handleLogout} />

      <main className="flex-1 p-8 overflow-y-auto">
        {/* Khung báo lỗi chung */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-600 rounded-lg flex items-center">
            <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" /> {error}
          </div>
        )}

        {/* 2. Điều hướng Render các Tab */}
        {activeTab === 'scanner' && (
          <ScannerTab 
            selectedFile={selectedFile} setSelectedFile={setSelectedFile} isScanning={isScanning} 
            scanResult={scanResult} setScanResult={setScanResult} error={error} 
            handleFileChange={handleFileChange} handleScan={handleScan} fileInputRef={fileInputRef} 
          />
        )}

        {activeTab === 'history' && (
          <HistoryTab isLoadingHistory={isLoadingHistory} historyList={historyList} handleViewDetail={handleViewDetail} />
        )}

        {activeTab === 'report_detail' && (
          <ReportDetail isLoadingDetail={isLoadingDetail} detailedReport={detailedReport} setActiveTab={setActiveTab} />
        )}
      </main>
    </div>
  );
}