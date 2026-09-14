export default function PrintReportView({ 
  reportInfo, 
  matches, 
  stats 
}) {
  const currentDate = new Date().toLocaleString('vi-VN');

  // Lấy danh sách các tài liệu nguồn tiêu biểu xuất hiện trong bài
  const topSources = Array.from(
    new Set(
      matches
        .map((m) => m.sources?.[0]?.source_title || m.sources?.[0]?.source_file_path || `Tài liệu #${m.sources?.[0]?.source_doc_id}`)
        .filter(Boolean)
    )
  );

  return (
    <div className="hidden print:block text-black p-4 text-[13px] leading-normal">
      
      {/* ========================================================================= */}
      {/* TRANG 1: TRANG TỔNG QUAN / BÌA BÁO CÁO                                    */}
      {/* ========================================================================= */}
      <div className="min-h-[90vh] flex flex-col justify-between">
        <div>
          {/* Header */}
          <div className="border-b-2 border-emerald-600 pb-3 mb-6 flex justify-between items-end">
            <div>
              <p className="text-xs uppercase tracking-widest text-gray-500 font-semibold">Hệ thống Kiểm tra Trùng lặp Học thuật</p>
              <h1 className="text-2xl font-black text-emerald-800 uppercase tracking-tight mt-1">Báo cáo kết quả kiểm tra</h1>
            </div>
            <div className="text-right text-xs text-gray-500">
              <p>Mã báo cáo: <span className="font-mono font-bold text-gray-700">#{reportInfo.id || 'TEMP'}</span></p>
              <p>Ngày tạo: {currentDate}</p>
            </div>
          </div>

          {/* Bảng thông tin tài liệu */}
          <div className="border border-gray-300 rounded-md overflow-hidden mb-6">
            <div className="bg-gray-100 px-4 py-2 font-bold text-gray-700 border-b border-gray-300 uppercase text-xs">
              Thông tin tài liệu kiểm tra
            </div>
            <div className="grid grid-cols-2 divide-x divide-gray-200">
              <div className="p-3 space-y-2">
                <p><span className="text-gray-500">Tên tài liệu:</span> <strong className="text-gray-900">{reportInfo.file_name}</strong></p>
                <p><span className="text-gray-500">Thời gian quét:</span> <span className="text-gray-800">{reportInfo.created_at || currentDate}</span></p>
              </div>
              <div className="p-3 space-y-2">
                <p><span className="text-gray-500">Tổng số phân đoạn quét:</span> <strong className="text-gray-900">{stats.totalChunks} đoạn</strong></p>
                <p><span className="text-gray-500">Số đoạn bị trùng lặp:</span> <strong className="text-red-600 font-bold">{stats.plagiarizedCount} đoạn</strong></p>
              </div>
            </div>
          </div>

          {/* Thống kê tỷ lệ dạng 4 khối tròn */}
          <div className="mb-8">
            <h3 className="font-bold text-gray-700 mb-3 uppercase text-xs tracking-wider">Kết quả phân tích tỷ lệ</h3>
            <div className="grid grid-cols-3 gap-4 text-center">
              
              <div className="border border-red-200 bg-red-50/50 p-4 rounded-lg">
                <div className="text-3xl font-black text-red-600 mb-1">{stats.plagiarizedPercent}%</div>
                <p className="text-xs font-semibold text-gray-700">Nội dung trùng lặp</p>
                <p className="text-[11px] text-gray-500 mt-1">({stats.plagiarizedCount} đoạn vi phạm)</p>
              </div>

              <div className="border border-emerald-200 bg-emerald-50/50 p-4 rounded-lg">
                <div className="text-3xl font-black text-emerald-600 mb-1">{100 - stats.plagiarizedPercent}%</div>
                <p className="text-xs font-semibold text-gray-700">Nội dung nguyên bản</p>
                <p className="text-[11px] text-gray-500 mt-1">({stats.originalCount} đoạn an toàn)</p>
              </div>

              <div className="border border-gray-200 bg-gray-50 p-4 rounded-lg">
                <div className="text-3xl font-black text-gray-600 mb-1">{stats.excludedCount}</div>
                <p className="text-xs font-semibold text-gray-700">Đoạn được loại trừ</p>
                <p className="text-[11px] text-gray-500 mt-1">(Trích dẫn / Mục lục)</p>
              </div>

            </div>
          </div>

          {/* Nguồn trùng lặp tiêu biểu */}
          <div>
            <h3 className="font-bold text-gray-700 mb-2 uppercase text-xs tracking-wider">Các tài liệu nguồn trùng lặp tiêu biểu</h3>
            {topSources.length > 0 ? (
              <ul className="border border-gray-200 rounded-md divide-y divide-gray-200 text-xs">
                {topSources.slice(0, 5).map((src, i) => (
                  <li key={i} className="p-2.5 flex items-center gap-2">
                    <span className="w-5 h-5 flex items-center justify-center bg-gray-200 text-gray-700 font-bold rounded-full text-[10px]">
                      {i + 1}
                    </span>
                    <span className="font-medium text-gray-800 truncate">{src}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-gray-500 italic">Không phát hiện nguồn trùng lặp nào.</p>
            )}
          </div>
        </div>

        {/* Chân trang bìa */}
        <div className="border-t border-gray-200 pt-3 text-center text-[11px] text-gray-400">
          Báo cáo được khởi tạo bởi Hệ thống Đạo văn Daovan Engine • Trang 1
        </div>
      </div>

      {/* ========================================================================= */}
      {/* TRANG 2 TRỞ ĐI: DANH SÁCH CÁC CÂU TRÙNG LẶP CHI TIẾT                       */}
      {/* ========================================================================= */}
      {matches.length > 0 && (
        <div className="page-break-before pt-4">
          <div className="border-b border-gray-300 pb-2 mb-4 flex justify-between items-center">
            <h2 className="text-base font-bold text-gray-800 uppercase">Danh sách các câu trùng lặp chi tiết</h2>
            <span className="text-xs text-gray-500">Tổng cộng: {matches.length} đoạn</span>
          </div>

          <div className="space-y-4">
            {matches.map((item, idx) => {
              const primarySource = item.sources?.[0] || {};
              const isExact = primarySource.match_type === 'EXACT_MATCH';

              return (
                <div key={idx} className="avoid-break border border-gray-200 rounded p-3 text-xs bg-white">
                  {/* Dòng tiêu đề câu */}
                  <div className="flex justify-between items-center mb-1.5 font-bold border-b border-gray-100 pb-1">
                    <span className="text-gray-800">
                      Câu #{item.chunk_index} • <span className={isExact ? 'text-red-600' : 'text-orange-600'}>
                        {isExact ? 'SAO CHÉP Y NGUYÊN' : 'ĐẠO Ý / SỬA TỪ'}
                      </span>
                      {item.is_quote && <span className="ml-2 font-normal text-gray-500">[Có trích dẫn]</span>}
                    </span>
                    <span className="text-red-600">
                      {((primarySource.similarity_score || 0) * 100).toFixed(1)}% Trùng lặp
                    </span>
                  </div>

                  {/* Nội dung bài sinh viên */}
                  <div className="mb-2">
                    <span className="font-semibold text-gray-600">Văn bản sinh viên: </span>
                    <span className="text-gray-900 bg-red-50/50 p-1 rounded">{item.student_text}</span>
                  </div>

                  {/* Nội dung đối chiếu từ nguồn */}
                  <div className="bg-gray-50 p-2 rounded border border-gray-100">
                    <p className="font-semibold text-emerald-700 truncate mb-1">
                      Nguồn đối chiếu: {primarySource.source_title || primarySource.source_file_path || `ID: ${primarySource.source_doc_id}`}
                    </p>
                    <p className="text-gray-700 italic">
                      "{primarySource.matched_text}"
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

    </div>
  );
}