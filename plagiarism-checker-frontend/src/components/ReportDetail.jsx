import { ArrowLeft, Loader2, UploadCloud } from 'lucide-react';
import MatchDetailCard from './MatchDetailCard'; 
import useMatchFilter from '../hooks/useMatchFilter'; // Hook đã được import

export default function ReportDetail({ isLoadingDetail, detailedReport, setActiveTab }) {
  
  // 1. [MỚI] Khởi tạo Hook để lấy công cụ tính toán
  // Truyền 0 vào vì màn hình Lịch sử không có tổng số đoạn (total_chunks)
  const { 
    excludeQuotes, 
    setExcludeQuotes,
    excludeReferences,     // [MỚI] Đã lấy cờ lọc Danh mục TLTK
    setExcludeReferences,  // [MỚI] Đã lấy hàm set cờ
    filteredMatches, 
    plagiarizedCount 
  } = useMatchFilter(detailedReport?.matches || [], 0);

  return (
    <div className="animate-fade-in-up">
      <header className="mb-8 flex items-center justify-between border-b pb-4">
        <div>
          <button onClick={() => setActiveTab('history')} className="flex items-center gap-2 text-gray-500 hover:text-emerald-600 mb-2 font-medium">
            <ArrowLeft className="w-4 h-4" /> Quay lại danh sách
          </button>
          <h2 className="text-2xl font-bold text-gray-800">Chi tiết báo cáo</h2>
        </div>
      </header>

      {isLoadingDetail ? (
         <div className="p-12 text-center text-gray-500 flex flex-col items-center">
            <Loader2 className="w-8 h-8 animate-spin mb-4 text-emerald-500" /> Đang tải...
         </div>
      ) : detailedReport ? (
        <div className="space-y-6">
          
          {/* 2. [CẬP NHẬT] Thêm Checkbox vào khung thông tin */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col md:flex-row justify-between items-start md:items-center border-l-4 border-l-emerald-500 gap-4">
            <div>
              <h3 className="text-lg font-bold text-gray-800">{detailedReport.report_info.file_name}</h3>
              <p className="text-sm text-gray-500 mt-1 mb-4">Ngày quét: {detailedReport.report_info.created_at}</p>
              
              {/* [MỚI] Bọc 2 Checkbox trong div space-y-3 để tạo khoảng cách dọc */}
              <div className="space-y-3">
                  {/* Thẻ Checkbox 1 */}
                  <label className="flex items-center gap-3 cursor-pointer">
                      <input 
                          type="checkbox" 
                          className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500" 
                          checked={excludeQuotes}
                          onChange={(e) => setExcludeQuotes(e.target.checked)}
                      />
                      <span className="text-gray-700 font-medium">Loại trừ câu trích dẫn trong ngoặc kép</span>
                  </label>

                  {/* [MỚI] Thẻ Checkbox 2: Loại trừ Danh mục tài liệu tham khảo */}
                  <label className="flex items-center gap-3 cursor-pointer">
                      <input 
                          type="checkbox" 
                          className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500" 
                          checked={excludeReferences}
                          onChange={(e) => setExcludeReferences(e.target.checked)}
                      />
                      <span className="text-gray-700 font-medium">Loại trừ Danh mục tài liệu tham khảo</span>
                  </label>
              </div>
            </div>
            
            <div className="text-right">
              <p className="text-sm text-gray-500 font-medium">Số đoạn phát hiện trùng lặp</p>
              {/* [CẬP NHẬT] Thay total_matches_found tĩnh bằng plagiarizedCount động từ Hook */}
              <p className="text-2xl font-bold text-red-600">{plagiarizedCount} đoạn</p>
            </div>
          </div>

          {/* 3. [CẬP NHẬT] Chạy vòng lặp bằng mảng filteredMatches đã lọc thay vì mảng gốc */}
          {filteredMatches.length > 0 ? (
            filteredMatches.map((match, index) => (
               <MatchDetailCard key={index} match={match} index={index} />
            ))
          ) : (
            <div className="bg-emerald-50 text-emerald-700 p-8 rounded-xl text-center">
              <UploadCloud className="w-8 h-8 mx-auto mb-4" />
              Tài liệu sạch (Hoặc các đoạn trùng lặp đã được loại trừ hợp lệ)
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}