import { useState } from 'react';

export default function useMatchFilter(originalMatches = [], totalChunks = 0) {
    // State quản lý công tắc bật/tắt
    const [excludeQuotes, setExcludeQuotes] = useState(false);

    // 1. Lọc mảng vi phạm
    const filteredMatches = originalMatches.filter(match => {
        if (excludeQuotes && match.is_quote) return false;
        return true;
    });

    // 2. Tính toán các con số
    const plagiarizedCount = filteredMatches.length;
    const excludedCount = originalMatches.length - plagiarizedCount;
    // Nếu totalChunks = 0 (bên màn hình lịch sử), ta cứ cho originalCount = 0
    const originalCount = totalChunks > 0 ? (totalChunks - originalMatches.length) : 0;
    const plagiarizedPercent = totalChunks > 0 ? Math.round((plagiarizedCount / totalChunks) * 100) : 0;

    // Trả về tất cả "đồ nghề" để các Component khác mang ra dùng
    return {
        excludeQuotes,
        setExcludeQuotes,
        filteredMatches,
        plagiarizedCount,
        excludedCount,
        originalCount,
        plagiarizedPercent
    };
}