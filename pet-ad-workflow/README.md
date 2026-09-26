# Quy trình 5 Style quảng cáo thú cưng

Trang: `pet-ad-workflow.html`. Trang này tách biệt với `index.html` và được mở từ nút "📸 Quy trình ảnh QC" trên thanh nav của `index.html`.

Ảnh ví dụ nằm trong `images/`: `pet.jpg`, `variant-blue.jpg`, `variant-grey.jpg`, `stl01-blue.jpg`, `stl02.jpg` … `stl05.jpg`.

Section **⚡ MAKE PROMPT** (`#make-prompt`): nhập tham số cho cả 5 style (trừ hình ảnh), bấm "Tạo prompt" để ra đủ 5 prompt, có nút copy từng prompt hoặc copy cả 5. Dữ liệu nhập được lưu tạm trên trình duyệt (localStorage).

## Prompt theo Variant

Trang: `variant-prompts.html` (nút "🧩 Prompt theo Variant" trên nav). Với mỗi sản phẩm trong `CJ_*`:

- Thống kê tổng số variant, các chiều biến thể (Color, Size…) và số **mẫu mã** thực sự khác nhau.
- Variant chỉ khác size / chiều dài / số lượng / phích cắm được gộp; variant combo/set được liệt kê riêng, không tạo prompt.
- Mỗi mẫu mã có 1 prompt STL_01 (Hero Shot) đã gắn link ảnh variant CJ và link ảnh pet trong `pets/`.

Tạo lại sau khi thêm/sửa dữ liệu CJ: `python3 tools/variant-prompts/build.py`.
Sản phẩm mới cần thêm 1 mục trong `tools/variant-prompts/products.json` (loại sản phẩm, pet, cách tương tác, căn cứ trích từ dữ liệu CJ).
Kết quả cũng được ghi ra `variant-prompts.json` và `CJ_*/VARIANT_PROMPTS.md`.
