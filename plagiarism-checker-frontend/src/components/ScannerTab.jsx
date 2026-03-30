import useMatchFilter from '../hooks/useMatchFilter';
import { UploadCloud, FileText, Loader2, LayoutDashboard } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import MatchDetailCard from './MatchDetailCard'; // [MỚI] Nhúng Component thẻ vi phạm vào đây

export default function ScannerTab({
  selectedFile, setSelectedFile, isScanning, scanResult, setScanResult, 
  error, handleFileChange, handleScan, fileInputRef
}) {
  const { 
    excludeQuotes, setExcludeQuotes, filteredMatches, 
    plagiarizedCount, excludedCount, originalCount, plagiarizedPercent 
  } = useMatchFilter(scanResult?.matches || [], scanResult?.total_chunks_scanned || 0);
  return (
    <div className="animate-fade-in-up">
      <header className="mb-8">
        <h2 className="text-2xl font-bold text-gray-800">Khu vực kiểm tra tài liệu</h2>
        <p className="text-gray-500 mt-1">Tải lên file Word hoặc PDF để hệ thống quét đạo văn</p>
      </header>

      {/* Khung tải file */}
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
            <div className="flex justify-center gap-4">
              <button 
                onClick={() => { setSelectedFile(null); setScanResult(null); if (fileInputRef.current) fileInputRef.current.value = null; }}
                disabled={isScanning}
                className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              > Hủy bỏ </button>
              <button 
                onClick={handleScan} disabled={isScanning}
                className="flex items-center bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2.5 px-6 rounded-lg transition-colors disabled:bg-emerald-400"
              >
                {isScanning ? <><Loader2 className="w-5 h-5 mr-2 animate-spin" /> Đang xử lý...</> : 'Bắt đầu quét'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Kết quả & Biểu đồ */}
      {scanResult && (
        <div className="mt-8 animate-fade-in-up">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-8">
                <div className="flex-1">
                    <h3 className="text-xl font-bold text-gray-800 mb-2">Báo cáo kết quả quét</h3>
                    <p className="text-gray-500 mb-6">File: <span className="font-medium text-emerald-600">{scanResult.file_name}</span></p>
                    <div className="space-y-3">
                        <label className="flex items-center gap-3"><input type="checkbox" className="w-5 h-5 text-emerald-600" /><span>Loại trừ tài liệu tham khảo (Sắp ra mắt)</span></label>
                        <label className="flex items-center gap-3"><input type="checkbox" className="w-5 h-5 text-emerald-600" /><span>Loại trừ câu trích dẫn trong ngoặc kép</span></label>
                    </div>
                </div>
                <div className="w-full md:w-1/2 flex items-center justify-center gap-8">
                    <div className="w-48 h-48 relative">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie data={[
                                        { name: 'Trùng lặp', value: scanResult.plagiarized_chunks_found, color: '#ef4444' }, 
                                        { name: 'Nguyên bản', value: scanResult.total_chunks_scanned - scanResult.plagiarized_chunks_found, color: '#10b981' }, 
                                        { name: 'Loại trừ', value: 0, color: '#9ca3af' } 
                                    ]} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value" >
                                    {[{ color: '#ef4444' }, { color: '#10b981' }, { color: '#9ca3af' }].map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                            <span className="text-3xl font-bold text-gray-800">{Math.round((scanResult.plagiarized_chunks_found / scanResult.total_chunks_scanned) * 100)}%</span>
                            <span className="text-xs text-gray-500 font-medium uppercase tracking-wider">Trùng lặp</span>
                        </div>
                    </div>
                    <div className="space-y-4">
                        <div className="flex items-center gap-3"><div className="w-4 h-4 rounded-full bg-red-500"></div><div><p className="text-sm font-bold text-gray-800">{scanResult.plagiarized_chunks_found} đoạn</p><p className="text-xs text-gray-500">Bị trùng lặp</p></div></div>
                        <div className="flex items-center gap-3"><div className="w-4 h-4 rounded-full bg-emerald-500"></div><div><p className="text-sm font-bold text-gray-800">{scanResult.total_chunks_scanned - scanResult.plagiarized_chunks_found} đoạn</p><p className="text-xs text-gray-500">Nguyên bản</p></div></div>
                    </div>
                </div>
            </div>
          </div>
          
          {/* [MỚI] Chi tiết đoạn văn vi phạm - ĐÃ ĐƯỢC THU GỌN */}
          {scanResult.matches.length > 0 ? (
            <div className="space-y-6">
                <h4 className="text-lg font-bold text-gray-800 border-b pb-2">Chi tiết các đoạn trùng lặp</h4>
                {scanResult.matches.map((match, index) => (
                    // Cả khối div hàng chục dòng nay chỉ còn gọi đúng thẻ này
                    <MatchDetailCard key={index} match={match} index={index} />
                ))}
            </div>
          ) : (
            <div className="bg-emerald-50 text-emerald-700 p-8 rounded-xl text-center shadow-sm">
                <UploadCloud className="w-10 h-10 mx-auto text-emerald-600 mb-4" /> 
                <h3 className="text-2xl font-bold mb-2">Xin chúc mừng!</h3>
                <p>Tài liệu của bạn hoàn toàn nguyên bản.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}