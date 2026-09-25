TOP 5 SẢN PHẨM - CJdropshipping - Pet Hair Removers & Combs
Danh mục: Pet Supplies > Pet Groomings > Pet Hair Removers & Combs (categoryId 2410110354491625800)
Ngày lấy dữ liệu: 24/09/2026. Xếp hạng theo listedNum (số shop đã list sản phẩm), cao xuống thấp.

CẤU TRÚC FILE
- SUMMARY_top5.csv   : bảng tóm tắt 5 sản phẩm (mở bằng Excel/Google Sheets)
- VARIANTS_all.csv   : toàn bộ 94 biến thể (giá sỉ, giá bán gợi ý, cân nặng, kích thước, tồn kho CN/US)
- REVIEWS_all.csv    : toàn bộ 80 đánh giá của 5 sản phẩm
- 00_search_full_category_43_products.json : kết quả search_products thô cho cả 43 sản phẩm trong danh mục
- Mỗi thư mục 01_..05_ chứa dữ liệu MCP trả về của 1 sản phẩm:
    01_search_products.json      (search_products, có description, videoList, category...)
    02_get_product_detail.json   (get_product_detail: ảnh, biến thể, HS code, chất liệu, đóng gói...)
    03_get_product_inventory.json(get_product_inventory: tồn kho theo kho / theo biến thể / stockId)
    04_get_product_reviews.json  (get_product_reviews: tất cả các trang đã được gộp)
    ALL_<SKU>.json               (4 phần trên gộp chung)

GHI CHÚ
- Giá tính bằng USD, trọng lượng tính bằng gram, kích thước tính bằng mm (theo CJ).
- Trong 02_get_product_detail, các trường có giá trị null và các chuỗi JSON lặp lại (productImage dạng chuỗi,
  materialName...) được giữ ở dạng mảng (…Set). variantNameEn được dựng lại từ tên sản phẩm + variantKey.
- productImage giữ theo thứ tự gốc; productImageSet (cùng các ảnh, khác thứ tự) không lặp lại.
- Tồn kho của SP #1 có 1 vid (1436180228056682496) không xuất hiện trong danh sách biến thể; giữ nguyên như MCP trả về.
- listedNum KHÔNG phải số đơn bán ra, chỉ là số shop đã list sản phẩm.
