CJ DROPSHIPPING – PET TRAINING AND EDUCATIONAL TOYS – TOP 5 THEO LISTEDNUM
========================================================================
Thời điểm thu thập (UTC): 2026-09-25T02:46:11+00:00
Nguồn: CJdropshipping MCP (cjdropship)
Danh mục: Pet Supplies > Pet Toys > Pet Training and Educational Toys (lv3 categoryId 2410110340031614900)

QUY TRÌNH
1. search_products: lv3categoryList=[2410110340031614900], orderBy=1 (listedNum), sort=desc, pageSize=100,
   features=[enable_category, enable_description, enable_video, enable_combine]
   -> totalRecords=45, totalPages=1 (1 trang đã đủ toàn bộ danh mục).
2. Sắp xếp lại theo listedNum giảm dần, lấy top 5.
3. Với mỗi sản phẩm: get_product_detail (features=enable_combine,enable_video),
   get_product_inventory (pid), get_product_reviews (pageSize=20, lấy đến hết total).

TOP 5
  #1 CJMY1870790  listedNum=7753  giá=5.56-11.12 USD  variants=3  tồn kho=34140  reviews=3
      Remote Control Interactive Cat Car Toy USB Charging Chasing Automatic Self-moving Remote Smart Control Car Interactive Cat Toy Pet Products
  #2 CJGY1703014  listedNum=4944  giá=1.78-11.23 USD  variants=4  tồn kho=44324  reviews=2
      Dog Chew Toy Dog Bone Type  Dogs Teeth Cleaning Toys Indestructible TPR Bone Chewing Bite Resistant Teething Toys  Pet Products
  #3 CJYD2058496  listedNum=3852  giá=0.58-3.52 USD  variants=10  tồn kho=118337  reviews=1
      Summer Cooling Pet Water Bed Cushion Ice Pad Dog Sleeping Square Mat For Puppy Dogs Cats Pet Kennel Cool Cold
  #4 CJMY1700579  listedNum=3765  giá=3.95 USD  variants=2  tồn kho=24234  reviews=9
      2 In 1 Pet Cat Toy With Feather For Self-play Cat Turntable Pets Supplies Cat Toy Toys Cats Items Products
  #5 CJGY1157230  listedNum=3431  giá=0.51-6.57 USD  variants=1  tồn kho=25351  reviews=0
      Silicone Flying Saucer Funny Pets Dog Cat Toy Dog Game Flying Discs Resistant Chew Puppy Training Interactive Pet Supplies

CẤU TRÚC
  00_search_full_category.json   Toàn bộ response search_products (45 sản phẩm) + tham số gọi
  <rank>_<SKU>/
     01_search_products.json      Bản ghi của sản phẩm trong kết quả search (kèm rank)
     02_get_product_detail.json   Response get_product_detail
     03_get_product_inventory.json Response get_product_inventory
     04_get_product_reviews.json  Tất cả các trang review + all_reviews (gộp)
     ALL_<SKU>.json               Gộp 4 file trên
  SUMMARY_top5.csv                1 dòng/sản phẩm: giá, cân nặng, HS code, tồn kho, video, review…
  VARIANTS_all.csv                1 dòng/biến thể: giá, kích thước, cân nặng, tồn kho theo kho
  REVIEWS_all.csv                 1 dòng/review

GHI CHÚ
  - Mỗi file JSON có khóa 'response' là dữ liệu MCP trả về nguyên vẹn; 'response_message' là dòng
    thông báo văn bản đi kèm trong response của MCP; 'params' là tham số đã gọi.
  - Giá tính bằng USD; cân nặng gram; kích thước biến thể mm.
  - cj_inventory = kho CJ; factory_inventory = kho nhà máy (chưa xác minh). verifiedWarehouse: 1=đã xác minh, 2=chờ xác minh.
  - commentId trong REVIEWS_all.csv lưu dạng chuỗi để tránh Excel làm tròn số 19 chữ số.
  - CSV mã hóa UTF-8 có BOM (mở trực tiếp bằng Excel không lỗi font).
  - CJGY1157230: detail chỉ trả về 1 biến thể (random color-1PC, 0.51 USD) dù sellPrice là 0.51-6.57;
    giữ nguyên như MCP trả về. Sản phẩm này có 0 review.
  - Tổng số review của top 5 đều <= 20 nên mỗi sản phẩm chỉ cần 1 trang.
