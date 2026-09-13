import { useState } from 'react'; // [MỚI] Bổ sung useState để quản lý state lọc và sắp xếp
import { ArrowLeft, Loader2, UploadCloud } from 'lucide-react';
import MatchDetailCard from './MatchDetailCard'; 
import useMatchFilter from '../hooks/useMatchFilter'; 

export default function ReportDetail({ isLoadingDetail, detailedReport, setActiveTab }) {
  
  const { 
    excludeQuotes, setExcludeQuotes,
    excludeReferences, setExcludeReferences,
    filteredMatches, plagiarizedCount 
  } = useMatchFilter(detailedReport?.matches || [], 0);

  // =========================================================================
  // [MỚI] STATE BỘ LỌC NHANH & SẮP XẾP
  // =========================================================================
  const [matchTypeFilter, setMatchTypeFilter] = useState('ALL'); // 'ALL' | 'EXACT' | 'PARAPHRASE'
  const [sortBy, setSortBy] = useState('index_asc'); // 'index_asc' | 'score_desc'

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
          
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col md:flex-row justify-between items-start md:items-center border-l-4 border-l-emerald-500 gap-4">
            <div>
              <h3 className="text-lg font-bold text-gray-800">{detailedReport.report_info.file_name}</h3>
              <p className="text-sm text-gray-500 mt-1 mb-4">Ngày quét: {detailedReport.report_info.created_at}</p>
              
              <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer">
                      <input 
                          type="checkbox" 
                          className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500" 
                          checked={excludeQuotes}
                          onChange={(e) => setExcludeQuotes(e.target.checked)}
                      />
                      <span className="text-gray-700 font-medium">Loại trừ câu trích dẫn trong ngoặc kép</span>
                  </label>

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
              <p className="text-sm text-gray-500 font-medium">Số câu phát hiện trùng lặp</p>
              <p className="text-2xl font-bold text-red-600">{plagiarizedCount} câu</p>
            </div>
          </div>

          {/* ================================================================= */}
          {/* [MỚI] THANH CÔNG CỤ BỘ LỌC NHANH & SẮP XẾP */}
          {/* ================================================================= */}
          {filteredMatches.length > 0 && (
            <div className="bg-white p-3 rounded-lg border border-gray-200 flex flex-wrap items-center justify-between gap-3 text-sm">
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider mr-1">
                  Mức độ:
                </span>
                <button
                  onClick={() => setMatchTypeFilter('ALL')}
                  className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                    matchTypeFilter === 'ALL'
                      ? 'bg-gray-800 text-white shadow-sm'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  Tất cả ({filteredMatches.length})
                </button>
                <button
                  onClick={() => setMatchTypeFilter('EXACT')}
                  className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                    matchTypeFilter === 'EXACT'
                      ? 'bg-red-600 text-white shadow-sm'
                      : 'bg-red-50 text-red-700 hover:bg-red-100'
                  }`}
                >
                  Sao chép y nguyên
                </button>
                <button
                  onClick={() => setMatchTypeFilter('PARAPHRASE')}
                  className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                    matchTypeFilter === 'PARAPHRASE'
                      ? 'bg-orange-500 text-white shadow-sm'
                      : 'bg-orange-50 text-orange-700 hover:bg-orange-100'
                  }`}
                >
                  Đạo ý / Sửa từ
                </button>
              </div>

              <div className="flex items-center gap-2">
                <label htmlFor="sort-detail-select" className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Sắp xếp:
                </label>
                <select
                  id="sort-detail-select"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="bg-gray-50 border border-gray-200 text-gray-700 text-xs rounded-md px-2.5 py-1 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="index_asc">Thứ tự câu trong bài</option>
                  <option value="score_desc">% Trùng lặp (Cao nhất trước)</option>
                </select>
              </div>
            </div>
          )}

          {/* DÙNG displayMatches ĐÃ ĐƯỢC LỌC VÀ SẮP XẾP */}
          {filteredMatches.length > 0 ? (
            displayMatches.length > 0 ? (
              displayMatches.map((match, index) => (
                 <MatchDetailCard key={match.chunk_index || index} match={match} index={index} />
              ))
            ) : (
              <div className="p-8 text-center text-gray-500 bg-gray-50 rounded-xl border border-dashed border-gray-200">
                Không có đoạn trùng lặp nào thuộc phân loại đã chọn.
              </div>
            )
          ) : (
            <div className="bg-emerald-50 text-emerald-700 p-8 rounded-xl text-center">
              <UploadCloud className="w-8 h-8 mx-auto mb-4" />
              Tài liệu sạch (Hoặc các câu trùng lặp đã được loại trừ hợp lệ)
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}