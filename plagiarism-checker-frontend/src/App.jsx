import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Đường dẫn trang Đăng nhập */}
        <Route path="/login" element={<Login />} />
        
        {/* Đường dẫn trang Bảng điều khiển */}
        <Route path="/dashboard" element={<Dashboard />} />
        
        {/* Nếu gõ đường dẫn linh tinh, văng về login */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;