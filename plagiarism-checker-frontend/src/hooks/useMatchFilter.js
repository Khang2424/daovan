import { useState } from 'react';

export default function useMatchFilter(originalMatches = [], totalChunks = 0) {
    const [excludeQuotes, setExcludeQuotes] = useState(false);

    // 1. Lọc mảng vi phạm
    const filteredMatches = originalMatches.filter(match => {
        // Kiểm tra an toàn xem nguồn có tồn tại không
        const hasSources = match.sources && match.sources.length > 0;
        
        // Điều kiện khắt khe: PHẢI CÓ TRÍCH DẪN + PHẢI LÀ CHÉP Y NGUYÊN (EXACT_MATCH)
        const isStrictQuote = match.is_quote === true && hasSources && match.sources[0].match_type === 'EXACT_MATCH';

        // Nếu bật bộ lọc VÀ đáp ứng đủ điều kiện khắt khe -> Ẩn thẻ (return false)
        if (excludeQuotes && isStrictQuote) {
            return false; 
        }
        return true; // Các trường hợp khác giữ lại bình thường
    });

    // 2. Tính toán các con số để đưa ra Biểu đồ
    const plagiarizedCount = filteredMatches.length;
    const excludedCount = originalMatches.length - plagiarizedCount;
    // Nếu totalChunks = 0 (bên màn hình lịch sử), ta cứ cho originalCount = 0
    const originalCount = totalChunks > 0 ? (totalChunks - originalMatches.length) : 0;
    const plagiarizedPercent = totalChunks > 0 ? Math.round((plagiarizedCount / totalChunks) * 100) : 0;

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