# PLAN: Xây Dựng Hệ Thống Prompt Đa Nhiệm (Multi-Agent Prompt Architecture) V3

Mục tiêu: Biến Bot từ một "máy đọc tin" thành một "Ban Cố Vấn" (Board of Advisors) thực thụ. Mỗi Agent chuyên trách sẽ có tính cách (Persona), nhiệm vụ (Mission), và quy tắc (Ruleset) riêng biệt.

## 1. Cấu Trúc Tổng Thể (Files Structure)
```
prompts/
├── base.txt            # [CORE] Cấu trúc chung, Format Output, Anti-Hallucination
└── agents/
    ├── finance.txt     # [Analyst] Vĩ mô, Chứng khoán, Tỷ giá
    ├── crypto.txt      # [Veteran] Risk Management, Market Sentiment
    ├── shopping.txt    # [Shopper] Săn Sale, Value/Money, Chống lãng phí
    ├── events.txt      # [Secretary] Lịch trình, Chuẩn bị, Prioritization
    ├── weather.txt     # [Safety Officer] An toàn di chuyển, Sức khỏe
    └── news.txt        # [Intel Officer] Lọc tin rác, Insight
```

## 2. Chi Tiết Từng Agent (Đã triển khai)

### A. FINANCE AGENT (Tài chính & Vĩ mô)
- **Persona**: Chiến lược gia lạnh lùng.
- **Ruleset**: "Holy Trinity" (DXY, Yield Curve, VN-Index).
- **Core Value**: Bảo vệ NAV. Cảnh báo rủi ro trước lợi nhuận.

### B. CRYPTO AGENT (Thị trường Tiền số)
- **Persona**: Degen hoàn lương (Risk Manager).
- **Ruleset**: Fear & Greed Index Check.
- **Core Value**: Chống FOMO. Kỷ luật cắt lỗ/chốt lời.

### C. SHOPPING AGENT (Chi tiêu & Săn Sale)
- **Persona**: Quản gia khó tính.
- **Ruleset**: Needs (Cần) vs Wants (Muốn). Check giá ảo.
- **Core Value**: Chỉ mua "Value for Money".

### D. EVENTS AGENT (Lịch trình)
- **Persona**: Thư ký điều hành (Executive Secretary).
- **Ruleset**: Ma trận Eisenhower. Review chuẩn bị trước giờ G.
- **Core Value**: Không bao giờ để Sếp trễ giờ hoặc thiếu tài liệu.

### E. WEATHER AGENT (Giao thông & Thời tiết)
- **Persona**: Sĩ quan an toàn (Hậu cần).
- **Ruleset**: Tác động thời tiết lên di chuyển & sức khỏe.
- **Core Value**: Đi đến nơi, về đến chốn an toàn.

### F. NEWS AGENT (Tin tức & Kiến thức)
- **Persona**: Chuyên gia tình báo.
- **Ruleset**: Signal vs Noise. "So What?" (Tin này thì sao?).
- **Core Value**: Lợi thế thông tin (Information Edge).

## 3. Cách Hoạt Động (Orchestration)
Khi chạy, hệ thống sẽ:
1. Load nội dung `base.txt` (Luật chung).
2. Load nội dung `agents/<topic>.txt` (Luật riêng).
3. Kết hợp (Concatenate) thành `System Prompt` hoàn chỉnh cho từng luồng xử lý AI.
4. AI trả về kết quả theo Format chuẩn (V3) đã định nghĩa trong `base.txt`.
5. Tổng hợp lại thành Bản tin sáng.

## 4. Trạng Thái
✅ Đã tách file prompt cơ bản.
✅ Đã nâng cấp nội dung chi tiết cho từng Agent (Persona, Rules, Action).
✅ Đã cập nhật Code (`main.py`, `config.py`) để hỗ trợ load dynamic prompt.

---
*Plan này đảm bảo tính mở rộng cao. Muốn thêm chuyên gia khác (ví dụ "Health Coach"), chỉ cần tạo thêm file `health.txt` mà không cần sửa code lõi.*
