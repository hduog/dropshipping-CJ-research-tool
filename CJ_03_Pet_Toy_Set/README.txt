CJ_03_Pet_Toy_Set — Dữ liệu CJ Dropshipping (MCP cjdropship)
============================================================
Ngày thu thập : 2026-09-25
Danh mục      : Pet Supplies > Pet Toys > Pet Toy Set (lv3 categoryId 2410110340411608400)

QUY TRÌNH
1) search_products: lv3categoryList=[2410110340411608400], orderBy=1 (listedNum), sort=desc,
   pageSize=100, features=[enable_category, enable_description, enable_video, enable_combine].
   Danh mục có 147 SP / 2 trang -> đã lấy cả 2 trang (100 + 47) vào 00_search_full_category.json.
2) Chọn top 5 theo listedNum (giảm dần).
3) Mỗi SP: get_product_detail (features=enable_combine,enable_video), get_product_inventory,
   get_product_reviews (pageSize=20, lấy đến hết các trang).

TOP 5
 #  SKU             listedNum  Biến thể  Tồn kho tổng (CJ / nhà máy)   Reviews
 1  CJJJCWGY04596   4233       5         116,056 (0 / 116,056)         0
 2  CJGY1548160     2867       1         1,521 (1,521 / 0)             0
 3  CJGY1742809     2460       2         28,200 (3,143 / 25,057)       0
 4  CJGY1757445     2333       4         54,902 (6,701 / 48,201)       21 (TB 4.43★, 2 trang)
 5  CJGY1803656     1806       3         4,184 (4,184 / 0)             0
Toàn bộ tồn kho nằm ở kho Trung Quốc (CN).

CẤU TRÚC
 00_search_full_category.json   Kết quả search_products thô, cả 2 trang
 SUMMARY_top5.csv               1 dòng / sản phẩm (giá, tồn kho, review, NCC, link...)
 VARIANTS_all.csv               1 dòng / biến thể (15 dòng), kèm tồn kho từng biến thể
 REVIEWS_all.csv                1 dòng / đánh giá (21 dòng)
 NN_<SKU>/
   01_search_products.json      Bản ghi của SP trong kết quả search
   02_get_product_detail.json
   03_get_product_inventory.json
   04_get_product_reviews.json  Gồm "pages" (từng trang thô) + "allReviews" (gộp)
   ALL_<SKU>.json               Gộp 4 file trên

GHI CHÚ
- Mỗi file JSON bọc dữ liệu MCP trong "data" kèm "tool"/"params"; "_header" là dòng thông báo
  văn bản tool trả về trước phần JSON.
- CSV mã hoá UTF-8 có BOM (mở thẳng bằng Excel không lỗi font). commentId lưu dạng chuỗi
  để Excel không làm tròn số 19 chữ số.
- Danh mục "Pet Toy Set" của CJ chứa nhiều mặt hàng không phải đồ chơi (dây dắt, cổng chắn,
  bàn chải răng, khăn tắm) — đây là cách CJ phân loại, dữ liệu giữ nguyên.
- Trường combineVariants = null ở mọi biến thể: không SP nào trong top 5 có biến thể combo.
- SP #5 không có video (productVideo = null).
