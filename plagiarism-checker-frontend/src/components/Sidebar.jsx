import { LayoutDashboard, History, Settings, LogOut, UploadCloud } from 'lucide-react';

export default function Sidebar({ activeTab, goToScanner, fetchHistory, handleLogout }) {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6">
        <h1 className="text-xl font-bold text-emerald-600 flex items-center gap-2">
          <LayoutDashboard className="w-6 h-6" />
          Anti-Plagiarism
        </h1>
      </div>
      
      <nav className="flex-1 px-4 space-y-2 mt-4">
        <button 
          onClick={goToScanner}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors ${activeTab === 'scanner' ? 'bg-emerald-50 text-emerald-700' : 'text-gray-600 hover:bg-gray-50'}`}
        >
          <UploadCloud className="w-5 h-5" /> Kiểm tra tài liệu
        </button>
        <button 
          onClick={fetchHistory}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors ${activeTab === 'history' || activeTab === 'report_detail' ? 'bg-emerald-50 text-emerald-700' : 'text-gray-600 hover:bg-gray-50'}`}
        >
          <History className="w-5 h-5" /> Lịch sử quét
        </button>
        <button className="w-full flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-lg font-medium transition-colors cursor-not-allowed opacity-50">
          <Settings className="w-5 h-5" /> Cài đặt
        </button>
      </nav>

      <div className="p-4 border-t border-gray-200">
        <button 
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-3 w-full text-red-600 hover:bg-red-50 rounded-lg font-medium transition-colors"
        >
          <LogOut className="w-5 h-5" /> Đăng xuất
        </button>
      </div>
    </aside>
  );
}