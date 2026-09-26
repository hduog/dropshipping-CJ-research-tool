"""Thống kê variant + tạo prompt STL_01 (Hero Shot) cho từng mẫu mã của mỗi sản phẩm CJ.

Nguồn dữ liệu: CJ_*/<rank>_<SKU>/02_get_product_detail.json (dữ liệu MCP CJdropshipping trả về).
Variant chỉ khác size / chiều dài / số lượng / loại phích cắm được gộp lại; variant combo/set được
liệt kê riêng và không tạo prompt.

Chạy:  python3 tools/variant-prompts/build.py
Ra:    pet-ad-workflow/variant-prompts.json
       pet-ad-workflow/variant-prompts.html
       CJ_*/VARIANT_PROMPTS.md
"""
import glob, html, json, os, re

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
HERE = os.path.dirname(__file__)
PAGES = "https://hduog.github.io/dropshipping-CJ-research-tool/"
PET_URL = PAGES + "pet-ad-workflow/pets/"

# Chiều biến thể không đổi mẫu mã (tên chiều trong productKeyEn)
NON_DESIGN_DIM = re.compile(r"^(size|尺寸|length|specifications?|quantity|数量|electrical outlet|model|capacity)$", re.I)
# Giá trị trông như kích thước
SIZE_VALUE = re.compile(
    r"^(\d*x{0,2}[sml]|xs|x{1,3}l|\d+xl|free size|\d+(\.\d+)?\s*(m|cm|mm|l|ml)"
    r"|\d+(\.\d+)?\s*[x*×]\s*\d+(\.\d+)?\s*(cm|mm)?|[a-z0-9]+\s*\d+(\.\d+)?\s*[x*×]\s*\d+(\.\d+)?\s*(cm|mm)?)$", re.I)
DIM_ALIAS = {"颜色": "Color", "尺寸": "Size", "数量": "Quantity"}

# Phần chữ trong giá trị mẫu mã chỉ nói về số lượng / dung tích / kích cỡ -> bỏ đi
STRIP = [
    (re.compile(r"\s*\d+\s*pcs?\b", re.I), ""),          # Blue 2pcs, Green3pcs
    (re.compile(r"\s*\d+(\.\d+)?\s*L\b"), ""),            # Pink 2L (dung tích)
    (re.compile(r"\s*\d+\s*cm\b", re.I), ""),            # Shark Pirate Ship 65cm
    (re.compile(r"\b(large|small)(\s+size)?\b", re.I), ""),  # Small Black Licking Pad, Ice pad large size
    (re.compile(r"\d+\.$"), ""),                          # Orange sports car2.
]
MULTI = re.compile(r"\d\s*pcs?\b|\band\b", re.I)  # "S 2PC", "XS and M" (nhiều món trong 1 variant)
BUNDLE = [
    re.compile(r"set\d*$", re.I),                         # Set, Set3, Blue set1, redset, Whiteset
    re.compile(r"\bset\d*\b", re.I),                      # 5pcs set2
    re.compile(r"^\d+[a-z]+\d+[a-z]+$", re.I),            # 2Blue1Grey
    re.compile(r"^\d+\s*pcs?$", re.I),                    # 3Pcs
]


def load_detail(path):
    j = json.load(open(path, encoding="utf-8"))
    if "variants" in j:
        return j
    for k in ("data", "response"):
        if isinstance(j.get(k), dict):
            return j[k]
    raise ValueError(path)


def text(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = html.unescape(s).replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def as_list(v):
    if isinstance(v, list):
        return v
    if isinstance(v, str) and v.startswith("["):
        try:
            return json.loads(v)
        except ValueError:
            pass
    return [v] if v else []


def split_key(key, n):
    parts = key.rsplit("-", n - 1) if n > 1 else [key]
    if len(parts) != n:
        parts = (parts + [""] * n)[:n]
    return [p.strip() for p in parts]


def clean_value(v):
    for rx, rep in STRIP:
        v = rx.sub(rep, v)
    return re.sub(r"\s+", " ", v).strip(" -")


def is_bundle(v):
    return any(rx.search(v) for rx in BUNDLE)


def analyse(d, cfg):
    dims = [DIM_ALIAS.get(x.strip(), x.strip()) for x in (d.get("productKeyEn") or "Variant").split("-")]
    variants = d["variants"]
    rows = [split_key(v["variantKey"] or "", len(dims)) for v in variants]
    # chiều nào không đổi mẫu mã: theo tên, hoặc mọi giá trị đều là kích thước
    design_idx = []
    for i, name in enumerate(dims):
        vals = {r[i] for r in rows if r[i]}
        if NON_DESIGN_DIM.match(name) or (vals and all(SIZE_VALUE.match(x) for x in vals)):
            continue
        design_idx.append(i)

    exclude = {k.lower(): why for k, why in (cfg.get("excludeDesigns") or {}).items()}
    set_is_design = cfg.get("setIsDesign", False)
    rename = {k.lower(): v for k, v in (cfg.get("rename") or {}).items()}
    designs, bundles, excluded = {}, [], []
    for v, r in zip(variants, rows):
        raw = [r[i] for i in design_idx]
        other = " / ".join(r[i] for i in range(len(dims)) if i not in design_idx and r[i])
        if not set_is_design and any(is_bundle(x) for x in raw):
            bundles.append({"variantKey": v["variantKey"], "sku": v["variantSku"], "image": v.get("variantImage")})
            continue
        vals = [clean_value(x) for x in raw]
        label = " / ".join(x for x in vals if x) or "Default"
        key = label.lower()
        if key in exclude:
            excluded.append({"variantKey": v["variantKey"], "sku": v["variantSku"], "reason": exclude[key]})
            continue
        g = designs.setdefault(key, {"label": rename.get(key, label), "variants": [], "images": [], "other": []})
        # ưu tiên ảnh của variant "đơn": không bị cắt số lượng/kích cỡ, không phải combo nhiều size
        plain = vals == raw and not MULTI.search(other)
        g["variants"].append({"variantKey": v["variantKey"], "sku": v["variantSku"], "image": v.get("variantImage")})
        img = v.get("variantImage")
        if img and img not in g["images"]:
            if plain and not g.get("plain"):
                g["images"].insert(0, img)
                g["plain"] = True
            else:
                g["images"].append(img)
        if other and other not in g["other"]:
            g["other"].append(other)
    for g in designs.values():
        g.pop("plain", None)
    return dims, design_idx, list(designs.values()), bundles, excluded


def build_prompt(p, g, pet):
    random_color = "random" in g["label"].lower()
    variant = g["label"]
    img = g["images"][0] if g["images"] else p["bigImage"]
    lines = [
        "IMAGES:",
        "[Reference Image] = pet: " + PET_URL + pet["file"],
        "[Base Image] = product variant \"" + variant + "\": " + img,
        "",
        "Place the " + pet["look"] + " from [Reference Image] together with the " + p["product"] +
        " (variant \"" + variant + "\") from [Base Image].",
        "Pose: the pet is " + p["action"] + ".",
        "Position: " + p["use"] + ".",
        "The product is captured from a " + p["angle"] + ", with product and pet filling the frame from left to right edges.",
        "",
        "Keep the pet identical to [Reference Image] (breed, fur color, face) and keep the product identical to "
        "[Base Image] (exact colors, pattern, shape and parts of variant \"" + variant + "\").",
    ]
    if random_color:
        lines.append("CJ ships this item in random colors: use exactly the color shown in [Base Image].")
    facts = "PRODUCT FACTS (CJ data): " + p["nameEn"]
    if p["material"]:
        facts += " | Material: " + ", ".join(p["material"])
    lines += [
        "",
        facts,
        "",
        "BACKGROUND: solid pure white #FFFFFF, seamless, no gradient, no vignette, no texture, no floor line. "
        "Shadows: only soft contact shadows directly under and right next to the product and the pet; everything else stays pure #FFFFFF.",
        "",
        "LIGHTING & STYLE: high-key 3D studio lighting, professional commercial catalog photo, 8k, crisp textures.",
        "",
        "NO TEXT, no logo, no watermark.",
        "",
        "FORMAT: square 1:1 aspect ratio (e.g. 2048x2048 px); keep every element fully inside the square frame.",
    ]
    return "\n".join(lines)


def main():
    cfg_all = json.load(open(os.path.join(HERE, "products.json"), encoding="utf-8"))
    pets = {p["id"]: p for p in json.load(open(os.path.join(ROOT, "pet-ad-workflow/pets/pets.json"), encoding="utf-8"))}
    categories = []
    for cat_dir in sorted(glob.glob(os.path.join(ROOT, "CJ_[0-9]*"))):
        if not os.path.isdir(cat_dir):
            continue
        cat = {"folder": os.path.basename(cat_dir), "products": []}
        for f in sorted(glob.glob(os.path.join(cat_dir, "[0-9]*_*", "02_get_product_detail.json"))):
            d = load_detail(f)
            sku = d["productSku"]
            cfg = cfg_all.get(sku)
            if not cfg:
                raise SystemExit("Thiếu cấu hình cho SKU %s trong products.json" % sku)
            pet = pets[cfg["pet"]]
            dims, design_idx, designs, bundles, excluded = analyse(d, cfg)
            p = {
                "rank": os.path.basename(os.path.dirname(f)).split("_")[0],
                "sku": sku, "pid": d["pid"], "nameEn": text(d["productNameEn"]),
                "category": d.get("categoryName"), "url": d.get("productUrl"), "bigImage": d.get("bigImage"),
                "material": [m for m in as_list(d.get("materialNameEnSet") or d.get("materialNameEn")) if m],
                "product": cfg["product"], "use": cfg["use"], "action": cfg["action"], "angle": cfg["angle"],
                "basis": cfg["basis"], "pet": pet["id"],
                "dims": [{"name": n, "design": i in design_idx} for i, n in enumerate(dims)],
                "totalVariants": len(d["variants"]),
                "bundles": bundles, "excluded": excluded,
            }
            for g in designs:
                g["prompt"] = build_prompt(p, g, pet)
            p["designs"] = designs
            cat["products"].append(p)
        if cat["products"]:
            categories.append(cat)

    out = {"petBaseUrl": PET_URL, "pets": list(pets.values()), "categories": categories}
    with open(os.path.join(ROOT, "pet-ad-workflow/variant-prompts.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    for cat in categories:
        write_md(cat, pets)
    write_html(out)
    for cat in categories:
        for p in cat["products"]:
            print("%-32s %-14s variants=%3d designs=%2d bundles=%2d" % (
                cat["folder"][:32], p["sku"], p["totalVariants"], len(p["designs"]), len(p["bundles"])))


def write_md(cat, pets):
    L = ["# " + cat["folder"] + " – Variant & prompt STL_01", "",
         "Tự tạo bởi `tools/variant-prompts/build.py` từ `02_get_product_detail.json`. "
         "Xem bản có nút copy: [variant-prompts.html](" + PAGES + "pet-ad-workflow/variant-prompts.html).", "",
         "| # | SKU | Tổng variant | Chiều biến thể | Mẫu mã (có prompt) | Combo/Set (bỏ qua) | Pet |",
         "|---|---|---|---|---|---|---|"]
    for p in cat["products"]:
        dims = ", ".join(x["name"] + ("" if x["design"] else " (bỏ)") for x in p["dims"])
        L.append("| %s | %s | %d | %s | %d | %d | %s |" % (
            p["rank"], p["sku"], p["totalVariants"], dims, len(p["designs"]), len(p["bundles"]), pets[p["pet"]]["name"]))
    for p in cat["products"]:
        L += ["", "## %s · %s" % (p["rank"], p["sku"]), "", p["nameEn"], "",
              "- Pet: **%s** · căn cứ: %s" % (pets[p["pet"]]["name"], p["basis"]),
              "- Mẫu mã: " + ", ".join("`%s` (%d variant)" % (g["label"], len(g["variants"])) for g in p["designs"])]
        if p["bundles"]:
            L.append("- Combo/Set bỏ qua: " + ", ".join("`%s`" % b["variantKey"] for b in p["bundles"]))
        for e in p["excluded"]:
            L.append("- Bỏ `%s`: %s" % (e["variantKey"], e["reason"]))
        for g in p["designs"]:
            L += ["", "### " + g["label"], "", "![](%s)" % (g["images"][0] if g["images"] else p["bigImage"]), "",
                  "```text", g["prompt"], "```"]
    with open(os.path.join(ROOT, cat["folder"], "VARIANT_PROMPTS.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def write_html(data):
    tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    with open(os.path.join(ROOT, "pet-ad-workflow/variant-prompts.html"), "w", encoding="utf-8") as fh:
        fh.write(tpl.replace("/*__DATA__*/null", payload))


if __name__ == "__main__":
    main()
