import { useState } from 'react';
import { ShieldCheck, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axiosClient from '../api/axiosClient';

export default function Login() {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  
  // Các state để lưu trữ dữ liệu người dùng nhập
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Hàm xử lý khi bấm nút Submit (Đăng nhập / Đăng ký)
  const handleSubmit = async (e) => {
    e.preventDefault(); // Ngăn trình duyệt tự động load lại trang
    setError('');
    setIsLoading(true);

    try {
      if (isLogin) {
        // LƯU Ý KỸ THUẬT: FastAPI OAuth2 mặc định yêu cầu form-data (username & password) chứ không phải JSON
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        // Gọi API Đăng nhập
        const response = await axiosClient.post('/api/v1/auth/login', formData, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });

        // Lưu Token vào LocalStorage để dùng cho các trang sau
        localStorage.setItem('access_token', response.data.access_token);
        
        // Chuyển hướng người dùng vào trang Hệ thống (Dashboard)
        navigate('/dashboard');
        
      } else {
        // Gọi API Đăng ký (Gửi JSON bình thường)
        await axiosClient.post('/api/v1/auth/register', {
          email: email,
          password: password
        });

        alert('Đăng ký thành công! Vui lòng đăng nhập.');
        setIsLogin(true); // Đẩy người dùng về lại form đăng nhập
        setPassword('');  // Xóa trắng mật khẩu
      }
    } catch (err) {
      // Bắt lỗi từ Backend trả về (Ví dụ: Sai mật khẩu, Email đã tồn tại)
      if (err.response && err.response.data) {
        setError(err.response.data.detail || 'Có lỗi xảy ra, vui lòng thử lại!');
      } else {
        setError('Không thể kết nối tới máy chủ!');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
        
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-100 mb-4">
            <ShieldCheck className="w-8 h-8 text-emerald-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">
            Hệ thống Kiểm tra Đạo văn
          </h2>
          <p className="text-sm text-gray-500 mt-2">
            {isLogin ? 'Đăng nhập để bắt đầu quét tài liệu' : 'Tạo tài khoản sinh viên mới'}
          </p>
        </div>

        {/* Khung hiển thị lỗi (Sẽ hiện ra nếu sai mật khẩu/email) */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-600 rounded-lg flex items-center text-sm">
            <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
            {error}
          </div>
        )}

        {/* Gắn sự kiện onSubmit vào form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-colors"
              placeholder="sv@gmail.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Mật khẩu</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-colors"
              placeholder="••••••••"
              required
            />
          </div>

          <button 
            type="submit"
            disabled={isLoading}
            className={`w-full text-white font-semibold py-2.5 rounded-lg transition-colors ${isLoading ? 'bg-emerald-400 cursor-not-allowed' : 'bg-emerald-600 hover:bg-emerald-700'}`}
          >
            {isLoading ? 'Đang xử lý...' : (isLogin ? 'Đăng nhập' : 'Đăng ký')}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-600">
          {isLogin ? "Chưa có tài khoản? " : "Đã có tài khoản? "}
          <button 
            type="button"
            onClick={() => {
              setIsLogin(!isLogin);
              setError(''); // Xóa lỗi cũ khi chuyển tab
            }}
            className="text-emerald-600 font-semibold hover:underline"
          >
            {isLogin ? 'Đăng ký ngay' : 'Đăng nhập'}
          </button>
        </div>

      </div>
    </div>
  );
}