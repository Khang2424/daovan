import { History, FileText, Loader2, Eye } from 'lucide-react';

export default function HistoryTab({ isLoadingHistory, historyList, handleViewDetail }) {
  return (
    <div className="animate-fade-in-up">
      <header className="mb-8">
        <h2 className="text-2xl font-bold text-gray-800">Lịch sử tài liệu đã nộp</h2>
        <p className="text-gray-500 mt-1">Xem lại các báo cáo phân tích đạo văn trước đây của bạn</p>
      </header>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {isLoadingHistory ? (
          <div className="p-12 text-center text-gray-500 flex flex-col items-center">
            <Loader2 className="w-8 h-8 animate-spin mb-4 text-emerald-500" /> Đang tải dữ liệu...
          </div>
        ) : historyList.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            <History className="w-12 h-12 mx-auto mb-4 opacity-50" /> Chưa có tài liệu nào.
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b text-sm text-gray-600 uppercase">
                <th className="p-4 font-semibold">Tên tài liệu</th>
                <th className="p-4 font-semibold">Ngày quét</th>
                <th className="p-4 font-semibold text-center">Trạng thái</th>
                <th className="p-4 font-semibold text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {historyList.map((item) => (
                <tr key={item.report_id} className="hover:bg-gray-50">
                  <td className="p-4"><div className="flex items-center gap-3"><FileText className="w-5 h-5 text-gray-400" /><span className="font-medium text-gray-900">{item.file_name}</span></div></td>
                  <td className="p-4 text-sm text-gray-600">{item.created_at}</td>
                  <td className="p-4 text-center"><span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700">Hoàn thành</span></td>
                  <td className="p-4 text-right">
                    <button onClick={() => handleViewDetail(item.report_id)} className="inline-flex items-center gap-2 px-4 py-2 border rounded-lg text-sm hover:text-emerald-600">
                      <Eye className="w-4 h-4" /> Xem chi tiết
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}