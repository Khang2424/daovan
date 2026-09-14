import { useRef, useState } from 'react'; // [MỚI] Thêm useState
import { UploadCloud, FileText, Loader2, Printer } from 'lucide-react'; // [MỚI] Bổ sung icon Printer
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import MatchDetailCard from './MatchDetailCard';
import useMatchFilter from '../hooks/useMatchFilter';
import PrintReportView from './PrintReportView'; // [MỚI] Bổ sung component view in ấn chuẩn A4 chuyên biệt

export default function ScannerTab({
  selectedFile, setSelectedFile, isScanning, scanResult, setScanResult, 
  error, handleFileChange, handleScan, fileInputRef
}) {
  
  // [MỚI] Khai báo State quản lý chế độ quét (mặc định là offline)
  const [scanMode, setScanMode] = useState("offline");

  // =========================================================================
  // [MỚI] STATE BỘ LỌC NHANH & SẮP XẾP
  // =========================================================================
  const [matchTypeFilter, setMatchTypeFilter] = useState('ALL'); // 'ALL' | 'EXACT' | 'PARAPHRASE'
  const [sortBy, setSortBy] = useState('index_asc'); // 'index_asc' | 'score_desc'

  // Lấy toàn bộ công cụ từ Hook ra dùng
  const { 
    excludeQuotes, setExcludeQuotes, excludeReferences, setExcludeReferences, filteredMatches, 
    plagiarizedCount, excludedCount, originalCount, plagiarizedPercent 
  } = useMatchFilter(scanResult?.matches || [], scanResult?.total_chunks_scanned || 0);

  // =========================================================================
  // [MỚI] TÍNH TOÁN DANH SÁCH HIỂN THỊ DỰA TRÊN BỘ LỌC NHANH
  // =========================================================================
  const displayMatches = [...filteredMatches]
    .filter((m) => {
      const primaryType = m.sources?.[0]?.match_type;
      if (matchTypeFilter === 'EXACT') return primaryType === 'EXACT_MATCH';
      if (matchTypeFilter === 'PARAPHRASE') return primaryType === 'PARAPHRASED';
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'score_desc') {
        const scoreA = a.sources?.[0]?.similarity_score || 0;
        const scoreB = b.sources?.[0]?.similarity_score || 0;
        return scoreB - scoreA;
      }
      return (a.chunk_index || 0) - (b.chunk_index || 0);
    });

  return (
    <>
      {/* ========================================================================= */}
      {/* GIAO DIỆN WEB HIỂN THỊ: Ẩn hoàn toàn khi thực hiện in qua class print:hidden */}
      {/* ========================================================================= */}
      <div className="animate-fade-in-up print:hidden">
        {/* [CẬP NHẬT] Thêm no-print vào header để đảm bảo an toàn tuyệt đối khi in */}
        <header className="mb-8 no-print">
          <h2 className="text-2xl font-bold text-gray-800">Khu vực kiểm tra tài liệu</h2>
          <p className="text-gray-500 mt-1">Tải lên file Word hoặc PDF để hệ thống quét đạo văn</p>
        </header>

        {/* KHU VỰC CHỌN FILE - Ẩn khi in ấn bằng no-print */}
        <div className="no-print bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center border-dashed border-2 hover:border-emerald-400 transition-colors">
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
            {/* ================================================================= */}
            {/* [MỚI] THANH ĐIỀU HƯỚNG XUẤT BÁO CÁO (Ẩn khi in ấn qua no-print) */}
            {/* ================================================================= */}
            <div className="flex justify-end mb-3 no-print">
              <button
                onClick={() => window.print()}
                className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium px-4 py-2.5 rounded-lg shadow-sm transition-colors cursor-pointer"
                title="Xuất file PDF hoặc in toàn bộ kết quả quét"
              >
                <Printer className="w-4 h-4" />
                <span>Xuất PDF / In kết quả</span>
              </button>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-6">
              <div className="flex flex-col md:flex-row items-center justify-between gap-8">
                  
                  {/* Thông tin bên trái & Checkbox */}
                  <div className="flex-1">
                      <h3 className="text-xl font-bold text-gray-800 mb-2">Báo cáo kết quả quét</h3>
                      <p className="text-gray-500 mb-6">File: <span className="font-medium text-emerald-600">{scanResult.file_name}</span></p>
                      
                      {/* [CẬP NHẬT] Thêm no-print vào cụm checkbox để file in sạch đẹp */}
                      <div className="space-y-3 no-print">
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
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-3">
                      <h4 className="text-lg font-bold text-gray-800">Chi tiết các đoạn trùng lặp</h4>

                      {/* ================================================================= */}
                      {/* [MỚI] THANH CÔNG CỤ BỘ LỌC NHANH & SẮP XẾP */}
                      {/* [CẬP NHẬT] Thêm no-print để ẩn công cụ lọc khi in file PDF */}
                      {/* ================================================================= */}
                      <div className="no-print flex flex-wrap items-center gap-2">
                          {/* Nhóm nút lọc theo loại */}
                          <div className="flex items-center bg-gray-100 p-1 rounded-lg border border-gray-200 text-xs">
                              <button
                                  onClick={() => setMatchTypeFilter('ALL')}
                                  className={`px-2.5 py-1 rounded font-medium transition-colors ${
                                      matchTypeFilter === 'ALL'
                                          ? 'bg-white text-gray-800 shadow-sm'
                                          : 'text-gray-600 hover:text-gray-900'
                                  }`}
                              >
                                  Tất cả ({filteredMatches.length})
                              </button>
                              <button
                                  onClick={() => setMatchTypeFilter('EXACT')}
                                  className={`px-2.5 py-1 rounded font-medium transition-colors ${
                                      matchTypeFilter === 'EXACT'
                                          ? 'bg-red-600 text-white shadow-sm'
                                          : 'text-red-700 hover:bg-red-50'
                                  }`}
                              >
                                  Y nguyên
                              </button>
                              <button
                                  onClick={() => setMatchTypeFilter('PARAPHRASE')}
                                  className={`px-2.5 py-1 rounded font-medium transition-colors ${
                                      matchTypeFilter === 'PARAPHRASE'
                                          ? 'bg-orange-500 text-white shadow-sm'
                                          : 'text-orange-700 hover:bg-orange-50'
                                  }`}
                              >
                                  Đạo ý
                              </button>
                          </div>

                          {/* Menu chọn sắp xếp */}
                          <select
                              value={sortBy}
                              onChange={(e) => setSortBy(e.target.value)}
                              className="bg-white border border-gray-200 text-gray-700 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                          >
                              <option value="index_asc">Thứ tự câu</option>
                              <option value="score_desc">% Trùng lặp cao</option>
                          </select>
                      </div>
                  </div>

                  {/* HIỂN THỊ DANH SÁCH THẺ ĐÃ QUA LỌC */}
                  {displayMatches.length > 0 ? (
                      displayMatches.map((match, index) => (
                          <MatchDetailCard key={match.chunk_index || index} match={match} index={index} />
                      ))
                  ) : (
                      <div className="p-8 text-center text-gray-500 bg-gray-50 rounded-xl border border-dashed border-gray-200">
                          Không có đoạn trùng lặp nào thuộc phân loại đã chọn.
                      </div>
                  )}
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

      {/* ========================================================================= */}
      {/* [MỚI] BẢN IN PDF CHUẨN A4: Chỉ xuất hiện khi gọi lệnh in (window.print())    */}
      {/* Tách riêng khỏi màn hình web, tự động lấy đúng kết quả sau khi loại trừ    */}
      {/* ========================================================================= */}
      {scanResult && (
        <PrintReportView
          reportInfo={{
            id: scanResult.report_id,
            file_name: scanResult.file_name,
          }}
          matches={displayMatches}
          stats={{
            totalChunks: scanResult.total_chunks_scanned || 0,
            plagiarizedCount,
            originalCount,
            excludedCount,
            plagiarizedPercent,
          }}
        />
      )}
    </>
  );
}