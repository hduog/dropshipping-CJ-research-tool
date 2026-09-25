CJ_06_Pet_Mats - CJ Dropshipping MCP export
Created: 2026-09-25 03:50
Category: Pet Supplies > Pet Bedding > Pet Mats (lv3 2410110357391611900)
search_products: orderBy=1 (listedNum) desc, pageSize=100, features=[enable_category, enable_description, enable_video, enable_combine] -> totalRecords=48 (1 page); top 5 by listedNum.
Per product: get_product_detail (features=enable_combine,enable_video), get_product_inventory, get_product_reviews (pageSize=20, all pages).

Each JSON wraps the MCP response as {tool,args,prefix_text,data}; 04_get_product_reviews.json keeps every raw page under "pages".
CSV files are UTF-8 with BOM (open directly in Excel). commentId is stored as text so Excel does not round it.
Inventory is mostly in the China warehouse (CN); US stock: #1 CJJT1006521=8, #2 CJJJCWGY00320=66.

TOP 5:
 #  SKU            listedNum  variants  inventory total (CJ / factory)  reviews
 1  CJJT1006521    7561       25          385,256 (8 / 385,248)         29 (avg 4.59, 2 pages)
 2  CJJJCWGY00320  6398       51          273,203 (354 / 272,849)       5 (avg 5.00, 1 page)
 3  CJJJCWMY00030  3009       31          922,814 (0 / 922,814)         20 (avg 4.65, 1 page)
 4  CJGY2064580    2070       42          497,194 (223 / 496,971)       649 (avg 4.15, 33 pages)
 5  CJGY1942967    1649       40          494,421 (0 / 494,421)         5 (avg 4.20, 1 page)

STATUS:
  #1 CJJT1006521: detail=OK, inventory=OK, reviews=29/29 reviews (COMPLETE)
  #2 CJJJCWGY00320: detail=OK, inventory=OK, reviews=5/5 reviews (COMPLETE)
  #3 CJJJCWMY00030: detail=OK, inventory=OK, reviews=20/20 reviews (COMPLETE)
  #4 CJGY2064580: detail=OK, inventory=OK, reviews=649/649 reviews (COMPLETE)
  #5 CJGY1942967: detail=OK, inventory=OK, reviews=5/5 reviews (COMPLETE)
