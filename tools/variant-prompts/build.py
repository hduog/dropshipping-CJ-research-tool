"""Thống kê variant + tạo đủ 5 prompt (STL_01 → STL_05) cho từng mẫu mã của mỗi sản phẩm CJ.

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
# Chiều kích thước (khác với số lượng / phích cắm / model) -> dùng cho STL_05
SIZE_DIM = re.compile(r"^(size|尺寸|length|specifications?|capacity)$", re.I)
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


def size_tokens(v):
    """'XS and M' -> ['xs', 'm'];  'M3PC' -> ['m'];  'S Charging' -> ['s charging']"""
    v = re.sub(r"\d+\s*pcs?\b", "", v, flags=re.I)
    return [re.sub(r"\s+", " ", x).strip().lower() for x in re.split(r"\band\b", v, flags=re.I) if x.strip()]


def analyse(d, cfg):
    dims = [DIM_ALIAS.get(x.strip(), x.strip()) for x in (d.get("productKeyEn") or "Variant").split("-")]
    variants = d["variants"]
    rows = [split_key(v["variantKey"] or "", len(dims)) for v in variants]
    # chiều nào không đổi mẫu mã: theo tên, hoặc mọi giá trị đều là kích thước
    design_idx, size_idx = [], []
    for i, name in enumerate(dims):
        vals = {r[i] for r in rows if r[i]}
        all_size = bool(vals) and all(SIZE_VALUE.match(x) for x in vals)
        if SIZE_DIM.match(name) or all_size:
            size_idx.append(i)
        if NON_DESIGN_DIM.match(name) or all_size:
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
        g = designs.setdefault(key, {"label": rename.get(key, label), "variants": [], "images": [], "other": [],
                                     "sizes": [], "raw": []})
        for i in size_idx:
            for sz in size_tokens(r[i]):
                if sz not in g["sizes"]:
                    g["sizes"].append(sz)
        for x in raw:
            if x not in g["raw"]:
                g["raw"].append(x)
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


FORMAT = "FORMAT: square 1:1 aspect ratio (e.g. 2048x2048 px); keep every element fully inside the square frame."
STL_NAMES = [("STL_01", "Hero Shot"), ("STL_02", "Lifestyle + chữ"), ("STL_03", "Functional Infographic"),
             ("STL_04", "Exploded View"), ("STL_05", "Size Guide")]


def q(s):
    return '"' + s.replace('"', "'") + '"'


def file_tag(p, g):
    return "%s_%s_STL01.jpg" % (p["sku"], re.sub(r"[^A-Za-z0-9]+", "-", g["label"]).strip("-").upper())


def size_cells(p, g):
    st = p["stl"]
    table = {k.lower().replace(" ", ""): v for k, v in (st.get("sizes") or {}).items()}
    order = list(table)
    cells = []
    for sz in g["sizes"]:
        k = sz.replace(" ", "")
        hit = k if k in table else sz.split(" ")[0] if sz.split(" ")[0] in table else None
        v = table[hit] if hit else {"badge": sz.upper(), "dim": sz if re.search(r"\d\s*[x*]\s*\d", sz) else ""}
        cells.append((order.index(hit) if hit else 99, v))
    for key, v in (st.get("sizesFromLabel") or {}).items():
        if any(key in r.lower() for r in g["raw"]):
            cells.append((len(cells), v))
    out, seen = [], set()
    for _, v in sorted(cells, key=lambda x: x[0]):
        if v["badge"] not in seen:
            seen.add(v["badge"]); out.append(v)
    if not out and st.get("oneSize"):
        out = [{"badge": "One Size", "dim": st["oneSize"]}]
    return out[:6]


def build_prompts(p, g, pet):
    st = p["stl"]
    variant = g["label"]
    img = g["images"][0] if g["images"] else p["bigImage"]
    pet_line = "[Reference Image] = pet: " + PET_URL + pet["file"]
    base_line = "[Base Image] = product variant " + q(variant) + ": " + img
    stl01_line = ("[STL_01 Image] = the STL_01 hero shot you generated for this variant (file " + file_tag(p, g) +
                  "). Attach it as the base image.")
    keep = ("Keep the pet identical to [Reference Image] (breed, fur color, face) and keep the product identical to "
            "[Base Image] (exact colors, pattern, shape and parts of variant " + q(variant) + ").")
    if "random" in variant.lower():
        keep += " CJ ships this item in random colors: use exactly the color shown in [Base Image]."
    facts = "PRODUCT FACTS (CJ data): " + p["nameEn"] + (" | Material: " + ", ".join(p["material"]) if p["material"] else "")
    prod = "the " + p["product"] + " (variant " + q(variant) + ")"
    lock = ("DO NOT change the pet, the product (variant " + q(variant) + ", exact colors and shape), "
            "the composition or the pure white #FFFFFF background of [STL_01 Image].")

    p1 = "\n".join([
        "IMAGES:", pet_line, base_line, "",
        "Place the " + pet["look"] + " from [Reference Image] together with " + prod + " from [Base Image].",
        "Pose: the pet is " + p["action"] + ".",
        "Position: " + p["use"] + ".",
        "The product is captured from a " + p["angle"] + ", with product and pet filling the frame from left to right edges.",
        "", keep, "", facts, "",
        "BACKGROUND: solid pure white #FFFFFF, seamless, no gradient, no vignette, no texture, no floor line. "
        "Shadows: only soft contact shadows directly under and right next to the product and the pet; everything else stays pure #FFFFFF.",
        "", "LIGHTING & STYLE: high-key 3D studio lighting, professional commercial catalog photo, 8k, crisp textures.",
        "", "NO TEXT, no logo, no watermark.", "", FORMAT])

    p2 = "\n".join([
        "IMAGES:", pet_line, base_line, "",
        "SCENE: Place the " + pet["look"] + " from [Reference Image] with " + prod + " from [Base Image], set in " + st["scene"] + ".",
        "Pose: the pet is " + p["action"] + ("" if "pampered" in p["action"] else ", looking pampered") + ".",
        "Position: " + p["use"] + ".",
        "", keep, "",
        "DATA INPUT FOR COPYWRITING (CJ data only):",
        "Overview: " + st["overview"],
        "Product Information: " + st["info"], "",
        "COPYWRITING TASK: Write ONE punchy Title, max 4 words. Write ONE Description line, max 8 words, about the single "
        "strongest benefit. Use only facts from the data above; do not invent features or numbers.", "",
        "TEXT RULES: Only the Title and the Description appear in the image. Short, bold, decisive words. No paragraphs, "
        "no bullet lists, no extra labels, no logo. Spell every word correctly.", "",
        "TYPOGRAPHY: Place the text in the top area of the image, in clean negative space, never over the pet's face. "
        "Bold modern sans-serif, large and highly legible; Title clearly bigger than the Description.", "",
        "STYLE: Professional lifestyle photography, soft natural light, realistic contact shadows, 8k.", "", FORMAT])

    labels = st["labels"][:3]
    p3 = "\n".join([
        "IMAGES:", stl01_line, "",
        "BASE IMAGE: [STL_01 Image] (the hero shot created in STL_01).", "",
        "FUNCTIONAL OVERLAY: Show the product's " + st["func"] + ". Product description (CJ data): " + st["funcDesc"],
        "Add clean, premium infographic graphics: " + st["graphic"] + ". Integrate them naturally on and around the product.", "",
        lock, "",
        "TEXT: Add only these short labels next to the graphics, nothing else: " + ", ".join(q(x) for x in labels) +
        ". Bold sans-serif, large and legible.", "",
        "GOAL: A simple, instantly understandable functional diagram. Clean and premium, lots of white space.", "", FORMAT])

    parts = st.get("parts")
    if parts:
        layered = st.get("partsMode") == "layers"
        n = len(parts)
        lines = []
        for i, name in enumerate(parts):
            where = ("top surface" if i == 0 else "bottom layer" if i == n - 1 else "middle layer") if layered else "part"
            lines.append("%d. %s: %s" % (i + 1, where, q(name)))
        p4 = "\n".join([
            "IMAGES:", stl01_line, "",
            "SCENE: Create a high-end exploded-view diagram of " + prod + " from [STL_01 Image].", "",
            ("LAYERS (top to bottom, from CJ data):" if layered else "PARTS (from CJ data):"), *lines, "",
            "TASK: Show these %d %s " % (n, "layers" if layered else "parts") +
            ("peeled apart and stacked in a clean diagonal 3D arrangement" if layered
             else "separated and floating apart in a clean 3D exploded arrangement") +
            ", each showing its real texture. Keep the product colors of variant " + q(variant) + " accurate.", "",
            "DIAGRAM: One thin leader line per %s, pointing precisely to it." % ("layer" if layered else "part"), "",
            "TEXT RULES: Each %s gets ONE label, exactly the quoted name above (1-3 words). No descriptions, no sentences, "
            "no title, no other text. Bold sans-serif, large and legible." % ("layer" if layered else "part"), "",
            "STYLE: Pure white #FFFFFF studio background, realistic textures, soft technical lighting, 8k, premium catalog look.",
            "", FORMAT])
    else:
        mat = st["materialLabel"]
        p4 = "\n".join([
            "IMAGES:", stl01_line, "",
            "NOTE: CJ data lists no internal layers or separate parts for this product, so this is a material close-up "
            "instead of an exploded view.", "",
            "SCENE: Keep " + prod + " and the pet from [STL_01 Image]. Add one large circular magnified inset beside the "
            "product showing the real surface texture of its material: " + q(mat) + ".", "",
            lock, "",
            "DIAGRAM: One thin leader line from the inset to the product surface.", "",
            "TEXT RULES: ONE label only, exactly " + q(mat) + ". No descriptions, no sentences, no title, no other text. "
            "Bold sans-serif, large and legible.", "",
            "STYLE: Pure white #FFFFFF studio background, realistic textures, soft technical lighting, 8k, premium catalog look.",
            "", FORMAT])

    cells = size_cells(p, g)
    if not cells:
        p5 = None
    else:
        n = len(cells)
        grid = {1: "a single centered panel", 2: "a clean 1x2 row", 3: "a clean 1x3 row", 4: "a clean 2x2 grid"}.get(n, "a clean 2x3 grid")
        has_fit = any(c.get("fit") for c in cells)
        lines = []
        for c in cells:
            line = "One size" if c["badge"] == "One Size" else "Size " + c["badge"]
            if c.get("dim"):
                line += ": " + q(c["dim"])
            if c.get("fit"):
                line += " - " + q(c["fit"])
            lines.append(line)
        items = ([] if cells[0]["badge"] == "One Size" else ["the size badge"]) + (["the dimension"] if any(c.get("dim") for c in cells) else []) + \
                (["the short fit label"] if has_fit else [])
        if n == 1:
            visuals = "Show the product with the pet from [STL_01 Image] and a clean dimension callout line along the product."
        elif has_fit:
            visuals = "In each cell, show the same product with a realistically scaled pet that matches the fit label, so the size difference is obvious."
        else:
            visuals = ("In each cell, show the same product drawn at its true relative scale, with the same pet from "
                       "[STL_01 Image] at the same size in every cell, so the size difference is obvious.")
        p5 = "\n".join([
            "IMAGES:", stl01_line, "",
            "SCENE: Create a size guide infographic for " + prod + " from [STL_01 Image].", "",
            "LAYOUT: " + grid + (", one cell per size: " + ", ".join(c["badge"] for c in cells) if n > 1 else "") + ".", "",
            "SIZE DATA (CJ data):", *lines, "",
            "VISUALS: " + visuals, "",
            "TEXT RULES: " + ("The panel" if n == 1 else "Each cell") + " has only: " + " and ".join(items) + ", exactly as quoted above. No title, no sentences, "
            "no other text. Bold sans-serif, large and legible.", "",
            "STYLE: Pure white #FFFFFF background, consistent studio lighting across all cells, 8k, premium advertising look.",
            "", FORMAT])

    out = []
    for (code, name), text_ in zip(STL_NAMES, [p1, p2, p3, p4, p5]):
        if text_ is None:
            out.append({"stl": code, "name": name, "skip": True,
                        "text": "Không tạo " + code + ": dữ liệu CJ của sản phẩm này không có thông tin kích thước (không tự đoán)."})
        else:
            out.append({"stl": code, "name": name, "text": text_})
    return out


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
            p["stl"] = cfg["stl"]
            for g in designs:
                g["prompts"] = build_prompts(p, g, pet)
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
    L = ["# " + cat["folder"] + " – Variant & prompt STL_01 → STL_05", "",
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
            L += ["", "### " + g["label"], "", "![](%s)" % (g["images"][0] if g["images"] else p["bigImage"])]
            for pr in g["prompts"]:
                L += ["", "#### %s – %s" % (pr["stl"], pr["name"]), ""]
                L += ["> " + pr["text"]] if pr.get("skip") else ["```text", pr["text"], "```"]
    with open(os.path.join(ROOT, cat["folder"], "VARIANT_PROMPTS.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def write_html(data):
    tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    with open(os.path.join(ROOT, "pet-ad-workflow/variant-prompts.html"), "w", encoding="utf-8") as fh:
        fh.write(tpl.replace("/*__DATA__*/null", payload))


if __name__ == "__main__":
    main()
