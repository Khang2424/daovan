import { useState } from 'react';
import { AlertCircle, FileText, LayoutDashboard, Database } from 'lucide-react';

export default function MatchDetailCard({ match, index }) {
  // State để quản lý xem người dùng đang click xem Nguồn số mấy (Mặc định là 0 - Nguồn giống nhất)
  const [activeSourceIndex, setActiveSourceIndex] = useState(0);

  // Lấy ra nguồn đang được chọn để hiển thị
  const activeSource = match.sources[activeSourceIndex];
  
  // Dùng dữ liệu của nguồn đầu tiên (giống nhất) để làm màu sắc chủ đạo cho thẻ
  const primarySource = match.sources[0];
  const isExactMatch = primarySource.match_type === 'EXACT_MATCH';

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden transition-all hover:shadow-md mb-6">
        
        {/* Thanh tiêu đề thẻ (Màu Đỏ hoặc Cam dựa vào nguồn giống nhất) */}
        <div className={`px-6 py-3 border-b flex justify-between items-center ${isExactMatch ? 'bg-red-50 border-red-100' : 'bg-orange-50 border-orange-100'}`}>
            <span className={`font-bold flex items-center gap-2 ${isExactMatch ? 'text-red-700' : 'text-orange-700'}`}>
                <AlertCircle className="w-5 h-5" />
                Câu #{match.chunk_index} • {isExactMatch ? 'SAO CHÉP Y NGUYÊN' : 'ĐẠO Ý / CHỈNH SỬA TỪ'}
                {/* Hiển thị cờ báo hiệu nếu câu này nằm trong ngoặc kép */}
                {match.is_quote && <span className="ml-2 px-2 py-0.5 bg-gray-200 text-gray-700 text-xs rounded border border-gray-300">CÓ TRÍCH DẪN</span>}
            </span>
            <span className={`px-3 py-1 rounded-full text-sm font-bold shadow-sm ${isExactMatch ? 'bg-red-600 text-white' : 'bg-orange-500 text-white'}`}>
                {(primarySource.similarity_score * 100).toFixed(1)}% Trùng lặp
            </span>
        </div>

        {/* Khung nội dung 2 cột */}
        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Cột 1: Văn bản của sinh viên */}
            <div className="flex flex-col h-full">
                <p className="text-xs font-bold text-gray-400 mb-2 uppercase tracking-wider flex items-center gap-2">
                    <FileText className="w-4 h-4" /> Văn bản sinh viên
                </p>
                <div className="p-4 bg-gray-50 rounded-lg text-gray-800 text-sm leading-relaxed border border-gray-200 flex-1">
                    {match.student_text}
                </div>
            </div>

            {/* Cột 2: Nguồn dữ liệu gốc (Có Tab chọn nhiều nguồn) */}
            <div className="flex flex-col h-full">
                <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-bold text-emerald-500 uppercase tracking-wider flex items-center gap-2">
                        <Database className="w-4 h-4" /> Nguồn dữ liệu
                    </p>
                    
                    {/* Các Nút Tab để chuyển đổi giữa các tài liệu giống (Top 1, Top 2, Top 3) */}
                    <div className="flex gap-1 bg-gray-100 p-1 rounded-md border border-gray-200">
                        {match.sources.map((src, idx) => (
                            <button
                                key={idx}
                                onClick={() => setActiveSourceIndex(idx)}
                                className={`text-xs px-2 py-1 rounded font-semibold transition-colors ${
                                    activeSourceIndex === idx 
                                    ? 'bg-white text-emerald-600 shadow-sm border border-gray-200' 
                                    : 'text-gray-500 hover:text-gray-700'
                                }`}
                                title={`Doc ID: ${src.source_doc_id}`}
                            >
                                Nguồn {idx + 1}
                            </button>
                        ))}
                    </div>
                </div>
                
                {/* Nội dung của nguồn đang được chọn */}
                <div className="p-4 bg-emerald-50 rounded-lg text-emerald-900 text-sm leading-relaxed border border-emerald-200 flex-1 relative">
                    {/* Badge nhỏ góc phải hiển thị độ giống của nguồn phụ này */}
                    {activeSourceIndex > 0 && (
                        <span className="absolute top-2 right-2 text-[10px] font-bold bg-emerald-200 text-emerald-800 px-2 py-1 rounded opacity-70">
                            Khớp {(activeSource.similarity_score * 100).toFixed(1)}%
                        </span>
                    )}
                    
                    <div className="mb-2 text-xs text-emerald-600 font-medium border-b border-emerald-100 pb-2">
                        Tài liệu tham chiếu ID: {activeSource.source_doc_id}
                    </div>
                    {activeSource.matched_text}
                </div>
            </div>

        </div>
    </div>
  );
}