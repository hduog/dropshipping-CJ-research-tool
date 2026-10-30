#!/usr/bin/env python3
"""Chèn bảng đối chiếu Store (Shopify) ↔ CJ vào product-t10.html.

Nguồn:
  - shopify-products.json: snapshot sản phẩm ACTIVE trên store (title, link, variant, SKU, giá, ảnh variant;
    variant không có ảnh riêng thì dùng ảnh đại diện sản phẩm - featuredImage).
  - product-t10.html: tên, link CJ và SKU từng variant CJ (bảng giá của mỗi sản phẩm).

Mapping theo SKU: SKU variant trên Shopify phải trùng đúng SKU variant CJ trên trang.
Sản phẩm bundle (SKU bắt đầu bằng BUNDLE) map theo BUNDLES bên dưới.

Chạy lại được nhiều lần: khối cũ nằm giữa marker <!--store-map--> ... <!--/store-map--> sẽ bị thay.
  python3 tools/shopify-mapping/build.py
"""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "product-t10.html"
SNAP = Path(__file__).with_name("shopify-products.json")

BOW = ("CJJJCWGX00023-Red", "Red", "Adjustable Pet Bow Tie (Red for Christmas)",
       "https://www.cjdropshipping.com/product/1-piece-adjustable-dog-cat-bow-tie-neck-tie-pet-dog-bow-tie-puppy-bows-pet-bow-tie-different-colors-supply-p-F5C0DF22-C2BD-4500-B93F-39A714A419BE.html")
# SKU bundle trên store -> danh sách SKU CJ cần đặt (món chính + quà tặng)
BUNDLES = {f"BUNDLE-ELK-BOW-{s}": [f"CJJJCWGD00702-Grey-{s}", BOW[0]] for s in ("S", "M", "L", "XL")}
EXTRA_CJ = {BOW[0]: dict(label=BOW[1], img="", name=BOW[2], link=BOW[3], pid=None)}

esc = lambda t: html.escape(str(t), quote=True)
MARK = re.compile(r"<!--store-map-->.*?<!--/store-map-->\n?", re.S)


def parse_page(s):
    arts = list(re.finditer(r'<article class="product" id="(p\d+)">', s))
    prods, sku = {}, {}
    for i, m in enumerate(arts):
        a = s[m.start(): arts[i + 1].start() if i + 1 < len(arts) else s.find("</main>")]
        pid = m.group(1)
        p = dict(id=pid,
                 num=pid[1:],
                 vi=html.unescape(re.search(r"<h2>(.*?)</h2>", a).group(1)),
                 en=html.unescape(re.search(r'<p class="en">(.*?)</p>', a).group(1)),
                 link=re.search(r'href="(https://www\.cjdropshipping\.com/product/[^"]+)"', a).group(1),
                 code=re.search(r'class="num">[^<]*<code>([^<]+)</code>', a).group(1),
                 variants=[])
        for row in re.finditer(r"<tr[^>]*><td>(<img[^>]*>)?</td><td><div class=\"vl\">(.*?)</div><code>([^<]+)</code>", a):
            label = html.unescape(re.sub(r"<[^>]+>", "", row.group(2))).strip()
            v = dict(label=label, img=row.group(1) or "", sku=row.group(3), pid=pid)
            p["variants"].append(v)
            sku[v["sku"]] = v
        prods[pid] = p
    return prods, sku


def cj_cell(v, prods):
    p = prods.get(v["pid"]) if v.get("pid") else None
    name = f'#{p["num"]} {p["en"]}' if p else v["name"]
    return v["label"], v["sku"], name


def build():
    s = MARK.sub("", PAGE.read_text())
    prods, sku = parse_page(s)
    sku.update({k: dict(v, sku=k) for k, v in EXTRA_CJ.items()})
    snap = json.loads(SNAP.read_text())
    date = snap["fetched_at"]

    blocks, overview, errors = {}, [], []
    for sp in snap["products"]:
        rows, pids = [], []
        for v in sp["variants"]["nodes"]:
            cj_skus = BUNDLES.get(v["sku"], [v["sku"]])
            cjv = []
            for k in cj_skus:
                if k not in sku:
                    errors.append(f'{sp["title"]}: SKU {k} không có trên trang CJ')
                    continue
                cjv.append(sku[k])
                if sku[k].get("pid") and sku[k]["pid"] not in pids:
                    pids.append(sku[k]["pid"])
            rows.append((v, cjv))
        if not pids:
            errors.append(f'{sp["title"]}: không map được sản phẩm CJ nào')
            continue
        main = prods[pids[0]]
        bundle = any(v["sku"] in BUNDLES for v, _ in rows)
        used = {c["sku"] for _, cs in rows for c in cs}
        missing = [x for x in main["variants"] if x["sku"] not in used]

        cj_names = f'<a href="{esc(main["link"])}" target="_blank" rel="noopener">{esc(main["en"])}</a> <code>{esc(main["code"])}</code>'
        if bundle:
            cj_names += f'<br>+ quà tặng: <a href="{esc(BOW[3])}" target="_blank" rel="noopener">{esc(BOW[2])}</a> <code>{esc(BOW[0])}</code>'
        body = []
        for i, (v, cs) in enumerate(rows, 1):
            img = cs[0]["img"] if cs and cs[0]["img"] else ""
            simg_url = v.get("image") or sp.get("featuredImage")
            simg = (f'<img loading="lazy" src="{esc(simg_url + ("&" if "?" in simg_url else "?") + "width=160")}" alt="">'
                    if simg_url else "")
            cj_lbl = "<br>".join(f'<div class="vl">{esc(c["label"])}</div><code>{esc(c["sku"])}</code>' for c in cs) or '<span class="warn">Không tìm thấy trên CJ</span>'
            body.append(f'<tr><td class="n muted">{i}</td><td><div class="vl">{esc(v["title"])}</div><code>{esc(v["sku"])}</code></td>'
                        f'<td class="n price">${esc(v["price"])}</td><td>{simg}</td><td>{img}</td><td>{cj_lbl}</td></tr>')
        miss = ""
        if missing:
            miss = (f'<p class="small muted" style="margin-top:8px">{len(missing)} variant CJ chưa đăng lên store: '
                    + ", ".join(f'<code>{esc(x["label"])}</code>' for x in missing) + "</p>")
        note = ('<p class="small muted" style="margin:0 0 8px">Sản phẩm bundle: SKU trên store là SKU riêng; mỗi đơn đặt 1 áo len theo cỡ + 1 nơ đỏ trên CJ.</p>'
                if bundle else "")
        ok = sum(1 for _, cs in rows if cs)
        blocks.setdefault(main["id"], []).append(
            f'<!--store-map--><details class="sec storemap" open><summary><span>🛒 Store ↔ CJ · {ok}/{len(rows)} variant khớp SKU</span>'
            f'<span class="muted small">Store {date}</span></summary><div class="secbody">'
            f'<div class="maphead"><div><h3>Trên store (Shopify)</h3><a href="{esc(sp["onlineStoreUrl"])}" target="_blank" rel="noopener"><b>{esc(sp["title"])}</b> ↗</a></div>'
            f'<div><h3>Trên CJ</h3>{cj_names}</div></div>{note}'
            f'<div class="table-wrap"><table><thead><tr><th class="n">#</th><th>Variant trên store / SKU</th><th class="n">Giá store</th><th>Ảnh store</th><th>Ảnh CJ</th><th>Variant CJ / SKU</th></tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>{miss}</div></details><!--/store-map-->\n')
        overview.append((int(main["num"]), sp, main, ok, len(rows), len(main["variants"]), bundle))

    if errors:
        sys.exit("Lỗi mapping:\n" + "\n".join(errors))

    # chèn bảng vào từng sản phẩm, ngay sau phần đầu (.phead)
    for pid, bl in blocks.items():
        i = s.find(f'<article class="product" id="{pid}">')
        j = s.find('<div class="cols">', i)
        s = s[:j] + "".join(bl) + s[j:]

    overview.sort(key=lambda x: x[0])
    on_store = {o[2]["id"] for o in overview}
    off = [p for p in prods.values() if p["id"] not in on_store]
    trs = "".join(
        f'<tr><td class="n"><a href="#{m["id"]}">#{n}</a></td>'
        f'<td><a href="{esc(sp["onlineStoreUrl"])}" target="_blank" rel="noopener">{esc(sp["title"])}</a></td>'
        f'<td><a href="{esc(m["link"])}" target="_blank" rel="noopener">{esc(m["en"])}</a>{" + nơ đỏ" if b else ""}<br><code>{esc(m["code"])}</code></td>'
        f'<td class="n">{ok}/{tot}</td><td class="n muted">{cjn}</td></tr>'
        for n, sp, m, ok, tot, cjn, b in overview)
    off_html = ("<p class=\"small muted\" style=\"margin-top:8px\">Chưa đăng lên store: "
                + ", ".join(f'<a href="#{p["id"]}">#{p["num"]} {esc(p["vi"])}</a>' for p in off) + "</p>") if off else ""
    total_v = sum(o[4] for o in overview)
    summary = (f'<!--store-map--><section class="storeov" id="store"><div class="catsep" style="margin-top:20px"><div class="eyebrow">Store mypetiny.com ↔ CJ</div>'
               f'<h2>{len(overview)} sản phẩm đang bán trên store, {total_v} variant</h2>'
               f'<p class="small muted">Lấy từ Shopify ngày {date} (sản phẩm Active, đã publish). Mapping theo SKU variant: SKU trên store trùng đúng SKU variant CJ. '
               f'Bảng chi tiết từng variant nằm trong mỗi sản phẩm (mục 🛒).</p></div>'
               f'<div class="table-wrap"><table><thead><tr><th class="n">#</th><th>Tên trên store</th><th>Tên trên CJ</th><th class="n">Variant khớp</th><th class="n">Variant CJ</th></tr></thead>'
               f"<tbody>{trs}</tbody></table></div>{off_html}</section><!--/store-map-->\n")
    k = s.find("<main><div class=\"wrap\">") + len("<main><div class=\"wrap\">")
    s = s[:k] + "\n" + summary + s[k:]

    nav = '<!--store-map--><a href="#store" class="catlink">🛒 Store ↔ CJ</a><!--/store-map-->'
    s = s.replace('<nav class="toc"><div class="wrap">', '<nav class="toc"><div class="wrap">' + nav, 1)
    css = ('<!--store-map--><style>.maphead{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:10px}'
           '.maphead>div{background:var(--surface-2);border-radius:10px;padding:10px 12px;min-width:0;overflow-wrap:anywhere}'
           'details.storemap{border-color:var(--good)}details.storemap>summary span:first-child{color:var(--good)}'
           '.warn{color:var(--warm);font-weight:600}@media (max-width:720px){.maphead{grid-template-columns:1fr}}</style><!--/store-map-->\n')
    s = s.replace("</head>", css + "</head>", 1)
    PAGE.write_text(s)
    print(f"OK: {len(overview)} sản phẩm, {total_v} variant; chưa đăng: {[p['id'] for p in off]}")


if __name__ == "__main__":
    build()
