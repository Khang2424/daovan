import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report

# Cấu hình đường dẫn để nhận diện được các file trong thư mục gốc
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import model, qdrant_client
from underthesea import word_tokenize

# ==========================================
# 1. TẠO TẬP DỮ LIỆU KIỂM THỬ (GROUND TRUTH)
# ==========================================
# Nhãn thực tế: 1 = Đạo văn (Copy/Xào bài), 0 = Sạch (Tự viết)
# LƯU Ý: Bạn có thể thêm hàng chục câu test vào đây để biểu đồ chính xác hơn
test_data = [
    # --- NHÓM 1: CHẮC CHẮN ĐẠO VĂN (Nên bị bắt) ---
    {"text": "Firebase là nền tảng được xây dựng, cung cấp bởi Google, hoạt động trên nền tảng Cloud nhằm hỗ trợ phát triển các ứng dụng.", "true_label": 1},
    {"text": "ASP. Net là một nền tảng dành cho phát triển web, được Microsoft phát hành và cung cấp lần đầu tiên vào năm 2002.", "true_label": 1},
    {"text": "Buôn bán online từ lâu đã trở thành một xu hướng được rất nhiều người ưa chuộng, các cửa hàng trực tuyến ngày càng hình thành nhiều.", "true_label": 1},
    
    # --- NHÓM 2: CHẮC CHẮN SẠCH (Không nên bị bắt) ---
    {"text": "Hôm nay thời tiết thật đẹp, tôi quyết định ra ngoài đi dạo và uống một tách cà phê nóng.", "true_label": 0},
    {"text": "Đồ án này được thực hiện nhằm mục đích tìm hiểu và ứng dụng công nghệ trí tuệ nhân tạo vào thực tiễn đời sống.", "true_label": 0},
    {"text": "Cơ sở dữ liệu là nơi lưu trữ thông tin quan trọng của hệ thống, giúp người quản trị dễ dàng truy xuất và quản lý dữ liệu.", "true_label": 0}
]

# Ngưỡng quyết định (Threshold) đang dùng trong scan_router.py
THRESHOLD = 0.65

def predict_plagiarism(text):
    """Hàm đưa văn bản qua AI Qdrant để dự đoán"""
    query_segmented = word_tokenize(text, format="text")
    query_vector = model.encode(query_segmented)
    
    search_response = qdrant_client.query_points(
        collection_name="document_chunks",
        query=query_vector.tolist(),
        limit=1
    )
    
    if search_response.points:
        best_score = search_response.points[0].score
        # Trả về 1 nếu AI chấm điểm >= ngưỡng (Dự đoán là Đạo văn)
        if best_score >= THRESHOLD:
            return 1 
            
    # Trả về 0 nếu điểm thấp hoặc không tìm thấy (Dự đoán là Sạch)
    return 0 

def main():
    print("=== BẮT ĐẦU ĐÁNH GIÁ MÔ HÌNH (EVALUATION) ===")
    y_true = []
    y_pred = []

    # 2. CHẠY KIỂM THỬ TỪNG CÂU VÀ ĐỐI CHIẾU
    for i, item in enumerate(test_data):
        text = item["text"]
        true_label = item["true_label"]
        
        pred_label = predict_plagiarism(text)
        
        y_true.append(true_label)
        y_pred.append(pred_label)

    # 3. TÍNH TOÁN MA TRẬN NHẦM LẪN VÀ CHỈ SỐ
    # Sắp xếp hiển thị: Hàng 1 là Đạo văn (1), Hàng 2 là Sạch (0)
    cm = confusion_matrix(y_true, y_pred, labels=[1, 0])
    
    print("\n=== BÁO CÁO ĐỘ CHÍNH XÁC (CLASSIFICATION REPORT) ===")
    print(classification_report(y_true, y_pred, target_names=["Sạch (0)", "Đạo văn (1)"]))

    # 4. VẼ BIỂU ĐỒ TRỰC QUAN BẰNG SEABORN
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=["Dự đoán Đạo văn", "Dự đoán Sạch"],
                yticklabels=["Thực tế Đạo văn", "Thực tế Sạch"])
    
    plt.title(f"Ma trận nhầm lẫn (Ngưỡng = {THRESHOLD})", fontsize=14, pad=15)
    plt.ylabel("Nhãn Thực Tế (Ground Truth)", fontsize=12)
    plt.xlabel("Nhãn Dự Đoán (AI Predicted)", fontsize=12)

    # Lưu ảnh ra file ở thư mục gốc
    output_path = "confusion_matrix.png"
    plt.savefig(output_path, bbox_inches='tight')
    print(f"\n[+] TUYỆT VỜI! Đã xuất biểu đồ thành công ra file: {output_path}")

if __name__ == "__main__":
    main()