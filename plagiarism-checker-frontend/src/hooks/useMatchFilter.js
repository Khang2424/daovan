import { useState } from 'react';

export default function useMatchFilter(originalMatches = [], totalChunks = 0) {
    const [excludeQuotes, setExcludeQuotes] = useState(false);
    const [excludeReferences, setExcludeReferences] = useState(false);

    // 1. Lọc mảng vi phạm
    const filteredMatches = originalMatches.filter(match => {
        // Kiểm tra an toàn xem nguồn có tồn tại không
        const hasSources = match.sources && match.sources.length > 0;
        
        // Điều kiện khắt khe: PHẢI CÓ TRÍCH DẪN + PHẢI LÀ CHÉP Y NGUYÊN (EXACT_MATCH)
        const isStrictQuote = match.is_quote === true && hasSources && match.sources[0].match_type === 'EXACT_MATCH';
        // Điều kiện tham khảo: CÓ CỜ THAM KHẢO (is_reference)
        const isRef = match.is_reference === true;

        // Nếu bật bộ lọc VÀ đáp ứng đủ điều kiện khắt khe -> Ẩn thẻ (return false)
        if (excludeQuotes && isStrictQuote) {
            return false; 
        }
        // Nếu bật bộ lọc VÀ trúng cờ tham khảo -> Ẩn thẻ (return false)
        if (excludeReferences && isRef) {
            return false;
        } //Nếu bật lọc và trúng cờ thì ẩn, còn lại thì giữ nguyên
        return true; // Các trường hợp khác giữ lại bình thường
    });

    // 2. Tính toán các con số để đưa ra Biểu đồ
    const plagiarizedCount = filteredMatches.length;
    const excludedCount = originalMatches.length - plagiarizedCount;
    const originalCount = totalChunks > 0 ? (totalChunks - originalMatches.length) : 0;

    // ====================================================================
    // 3. [THUẬT TOÁN MỚI] TÍNH TOÁN PHẦN TRĂM ĐẠO VĂN DỰA TRÊN ĐIỂM SỐ THỰC
    // ====================================================================
    let totalSimilaritySum = 0;
    
    if (totalChunks > 0) {
        // Duyệt qua từng đoạn văn đã bị bắt lỗi (sau khi đã đi qua bộ lọc)
        filteredMatches.forEach(match => {
            // Lấy điểm số cao nhất trong các nguồn của đoạn này (thường nằm ở vị trí [0])
            const highestScore = match.sources[0]?.similarity_score || 0;
            
            // Cộng dồn điểm thực tế. Ví dụ: Đoạn này giống 83.6% thì cộng 0.836
            totalSimilaritySum += highestScore; 
        });
    }

    // Công thức: (Tổng điểm thực tế của các đoạn / Tổng số đoạn cả bài) * 100
    // Ví dụ: (0.603 + 0.835 + 0.706 + 0.979 + 0.950) / 6 đoạn = 0.6788 -> 68%
    const plagiarizedPercent = totalChunks > 0 
        ? Math.round((totalSimilaritySum / totalChunks) * 100) 
        : 0;

    return {
        excludeQuotes, setExcludeQuotes,
        excludeReferences, setExcludeReferences, 
        filteredMatches, plagiarizedCount, excludedCount, originalCount, plagiarizedPercent
    };
}