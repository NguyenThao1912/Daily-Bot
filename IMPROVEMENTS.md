# Daily-Bot Improvements

Danh sách này tập trung vào các việc có tác động rõ ràng tới độ ổn định, chất lượng báo cáo và khả năng vận hành của `Daily-Bot`.

## 1. Ổn định dữ liệu đầu vào

- Tách riêng lớp fetch dữ liệu với lớp parse dữ liệu để dễ debug từng nguồn.
- Thêm cache cục bộ cho các nguồn chậm hoặc hay lỗi mạng như `cophieu68`, Google News, CafeF.
- Gắn `status/source/error` rõ ràng cho từng block dữ liệu thay vì chỉ trả text fallback.
- Chuẩn hóa log cho từng nguồn: thời gian fetch, số bản ghi, nguồn nào fail, nguồn nào degraded.

## 2. Cải thiện phân tích VN30

- Sắp xếp bảng VN30 theo `% Change`, `Volume spike`, hoặc `RSI` để đọc nhanh hơn.
- Loại bỏ các dòng dữ liệu bất thường như ngày `00000000` ngay ở tầng parse.
- Thêm các chỉ báo đơn giản nhưng hữu ích như:
  - khối lượng so với trung bình 20 phiên
  - khoảng cách giá hiện tại so với `MA20` và `MA50`
  - phân loại nhanh `mạnh / trung tính / yếu`
- Tách riêng phần `Top tăng`, `Top giảm`, `Top volume` thay vì chỉ một khối chung.

## 3. Cải thiện chất lượng báo cáo

- Chuẩn hóa output HTML từ các agent bằng schema đơn giản để giảm lỗi render PDF.
- Thêm fallback khi model trả HTML xấu hoặc thiếu section bắt buộc.
- Giảm độ dài các block ít quan trọng khi báo cáo quá dài, ưu tiên giữ finance/news/weather.
- Thêm một phần `Executive Summary` ở đầu báo cáo PDF: 5 dòng ngắn cho tín hiệu quan trọng nhất.

## 4. Cải thiện PDF

- Render thử với bộ dữ liệu mẫu cố định để tránh lỗi trang trắng hoặc overflow tái diễn.
- Tạo bộ template PDF theo 2 mode:
  - `brief`: đọc nhanh trên Telegram/PDF ngắn
  - `full`: bản phân tích đầy đủ
- Giới hạn chiều cao chart và kiểm soát page-break tốt hơn cho bảng dài.
- Thêm mục lục hoặc nhãn section rõ hơn nếu báo cáo dài nhiều trang.

## 5. Vận hành và CI

- Sinh `uv.lock` để workflow ổn định hơn giữa các lần chạy.
- Thêm job CI tối thiểu:
  - `compileall`
  - test lunar
  - smoke test parse stock/news
- Tách secret/config bắt buộc và optional để log startup rõ hơn.
- Gắn timeout riêng cho từng nguồn dữ liệu để một nguồn lỗi không kéo chậm toàn bộ pipeline.

## 6. Chất lượng mã nguồn

- Tách `main.py` thành các bước rõ hơn:
  - load config
  - fetch data
  - build prompt data
  - run AI
  - render/send report
- Đưa các hằng số lớn như danh sách VN30, query Google News, mapping prompt vào module riêng.
- Bổ sung kiểu dữ liệu rõ hơn bằng `TypedDict` hoặc `dataclass` cho các payload chính.
- Viết test cho parser `cophieu68`, nhất là case header bị dính dòng đầu.

## 7. Gợi ý ưu tiên làm trước

Nếu muốn tối ưu theo hiệu quả/chi phí, nên làm theo thứ tự này:

1. Thêm test + harden parser `cophieu68`
2. Chuẩn hóa log và status cho từng nguồn dữ liệu
3. Sinh `uv.lock` + CI smoke test
4. Cải thiện bảng/phân loại VN30
5. Tối ưu PDF và executive summary
