import { useRef, useState } from 'react'; // [MỚI] Thêm useState
import { UploadCloud, FileText, Loader2 } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import MatchDetailCard from './MatchDetailCard';
import useMatchFilter from '../hooks/useMatchFilter';

export default function ScannerTab({
  selectedFile, setSelectedFile, isScanning, scanResult, setScanResult, 
  error, handleFileChange, handleScan, fileInputRef
}) {
  
  // [MỚI] Khai báo State quản lý chế độ quét (mặc định là hybrid)
  const [scanMode, setScanMode] = useState("hybrid");

  // Lấy toàn bộ công cụ từ Hook ra dùng
  const { 
    excludeQuotes, setExcludeQuotes, excludeReferences, setExcludeReferences, filteredMatches, 
    plagiarizedCount, excludedCount, originalCount, plagiarizedPercent 
  } = useMatchFilter(scanResult?.matches || [], scanResult?.total_chunks_scanned || 0);

  return (
    <div className="animate-fade-in-up">
      <header className="mb-8">
        <h2 className="text-2xl font-bold text-gray-800">Khu vực kiểm tra tài liệu</h2>
        <p className="text-gray-500 mt-1">Tải lên file Word hoặc PDF để hệ thống quét đạo văn</p>
      </header>

      {/* KHU VỰC CHỌN FILE */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center border-dashed border-2 hover:border-emerald-400 transition-colors">
        <input 
          type="file" className="hidden" ref={fileInputRef} onChange={handleFileChange}
          onClick={(e) => (e.target.value = null)} accept=".pdf,.docx" 
        />
        {!selectedFile ? (
          <>
            <UploadCloud className="w-16 h-16 text-emerald-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">Kéo thả file vào đây</h3>
            <p className="text-gray-500 mt-2 mb-6">Hỗ trợ định dạng .pdf, .docx (Tối đa 10MB)</p>
            <button 
              onClick={() => fileInputRef.current.click()}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2.5 px-6 rounded-lg transition-colors"
            >
              Chọn file từ máy tính
            </button>
          </>
        ) : (
          <div className="py-6">
            <FileText className="w-16 h-16 text-emerald-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">{selectedFile.name}</h3>
            <p className="text-gray-500 mt-1 mb-6">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
            
            {/* ================================================= */}
            {/* [MỚI] Cụm Menu chọn chế độ quét */}
            <div className="max-w-xs mx-auto mb-6 text-left">
                <label className="block text-sm font-semibold text-gray-700 mb-2">Chế độ phân tích:</label>
                <select 
                    value={scanMode} 
                    onChange={(e) => setScanMode(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg p-2.5 text-sm focus:ring-emerald-500 focus:border-emerald-500 bg-white"
                >
                    <option value="offline">⚡ Cơ bản (Nhanh, Offline)</option>
                    <option value="hybrid">⚖️ Kết hợp (Cân bằng tốc độ & AI)</option>
                    <option value="online">🧠 Chuyên sâu (100% Gemini AI)</option>
                </select>
            </div>
            {/* ================================================= */}

            <div className="flex justify-center gap-4">
              <button 
                onClick={() => { setSelectedFile(null); setScanResult(null); if (fileInputRef.current) fileInputRef.current.value = null; }}
                disabled={isScanning}
                className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              > Hủy bỏ </button>
              <button 
                /* [CẬP NHẬT] Truyền scanMode vào hàm handleScan khi bấm nút */
                onClick={() => handleScan(scanMode)} 
                disabled={isScanning}
                className="flex items-center bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2.5 px-6 rounded-lg transition-colors disabled:bg-emerald-400"
              >
                {isScanning ? <><Loader2 className="w-5 h-5 mr-2 animate-spin" /> Đang xử lý...</> : 'Bắt đầu quét'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* KẾT QUẢ & BIỂU ĐỒ */}
      {scanResult && (
        <div className="mt-8 animate-fade-in-up">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-8">
                
                {/* Thông tin bên trái & Checkbox */}
                <div className="flex-1">
                    <h3 className="text-xl font-bold text-gray-800 mb-2">Báo cáo kết quả quét</h3>
                    <p className="text-gray-500 mb-6">File: <span className="font-medium text-emerald-600">{scanResult.file_name}</span></p>
                    <div className="space-y-3">
                        {/* Checkbox Loại trừ Danh mục tài liệu tham khảo */}
                        <label className="flex items-center gap-3 cursor-pointer">
                            <input 
                                type="checkbox" 
                                className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500" 
                                checked={excludeReferences}
                                onChange={(e) => setExcludeReferences(e.target.checked)}
                            />
                            <span className="text-gray-700">Loại trừ Danh mục tài liệu tham khảo</span>
                        </label>
                        
                        {/* Checkbox kích hoạt bộ lọc */}
                        <label className="flex items-center gap-3 cursor-pointer">
                            <input 
                                type="checkbox" 
                                className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500" 
                                checked={excludeQuotes}
                                onChange={(e) => setExcludeQuotes(e.target.checked)}
                            />
                            <span className="text-gray-700">Loại trừ câu trích dẫn trong ngoặc kép</span>
                        </label>
                    </div>
                </div>
                
                {/* Biểu đồ Donut bên phải */}
                <div className="w-full md:w-1/2 flex items-center justify-center gap-8">
                    <div className="w-48 h-48 relative">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie data={[
                                        { name: 'Trùng lặp', value: plagiarizedCount, color: '#ef4444' }, 
                                        { name: 'Nguyên bản', value: originalCount, color: '#10b981' }, 
                                        { name: 'Loại trừ', value: excludedCount, color: '#9ca3af' } 
                                    ]} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value" >
                                    {[{ color: '#ef4444' }, { color: '#10b981' }, { color: '#9ca3af' }].map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                            <span className="text-3xl font-bold text-gray-800">{plagiarizedPercent}%</span>
                            <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">Trùng lặp</span>
                        </div>
                    </div>
                    <div className="space-y-4">
                        <div className="flex items-center gap-3"><div className="w-4 h-4 rounded-full bg-red-500"></div><div><p className="text-sm font-bold text-gray-800">{plagiarizedCount} đoạn</p><p className="text-xs text-gray-500">Bị trùng lặp</p></div></div>
                        <div className="flex items-center gap-3"><div className="w-4 h-4 rounded-full bg-emerald-500"></div><div><p className="text-sm font-bold text-gray-800">{originalCount} đoạn</p><p className="text-xs text-gray-500">Nguyên bản</p></div></div>
                        <div className={`flex items-center gap-3 ${excludedCount === 0 ? 'opacity-50' : ''}`}><div className="w-4 h-4 rounded-full bg-gray-400"></div><div><p className="text-sm font-bold text-gray-800">{excludedCount} đoạn</p><p className="text-xs text-gray-500">Đã loại trừ</p></div></div>
                    </div>
                </div>
            </div>
          </div>
          
          {/* DANH SÁCH THẺ VI PHẠM */}
          {filteredMatches.length > 0 ? (
            <div className="space-y-6">
                <h4 className="text-lg font-bold text-gray-800 border-b pb-2">Chi tiết các đoạn trùng lặp</h4>
                {filteredMatches.map((match, index) => (
                    <MatchDetailCard key={index} match={match} index={index} />
                ))}
            </div>
          ) : (
            <div className="bg-emerald-50 text-emerald-700 p-8 rounded-xl text-center shadow-sm">
                <UploadCloud className="w-10 h-10 mx-auto text-emerald-600 mb-4" /> 
                <h3 className="text-2xl font-bold mb-2">Xin chúc mừng!</h3>
                <p>Tài liệu của bạn hoàn toàn nguyên bản (hoặc các trích dẫn đã được loại trừ hợp lệ).</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}