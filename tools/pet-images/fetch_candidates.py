"""Download candidate pet photos from Wikimedia Commons (free licenses only).

Writes pet-ad-workflow/pets/_candidates/<pet_id>/NN.jpg + candidates.json (source page,
author, license) so the best photo per pet can be picked by hand.
"""
import json, os, re, sys, urllib.parse, urllib.request

PETS = {
    "golden-retriever-puppy": ["golden retriever puppy", "golden retriever puppy portrait"],
    "corgi": ["pembroke welsh corgi puppy", "pembroke welsh corgi portrait"],
    "pomeranian": ["pomeranian puppy", "pomeranian dog portrait"],
    "shiba-inu": ["shiba inu puppy", "shiba inu portrait"],
    "samoyed": ["samoyed puppy", "samoyed dog portrait"],
    "french-bulldog": ["french bulldog puppy", "french bulldog portrait"],
    "british-shorthair": ["british shorthair kitten", "british shorthair cat portrait"],
    "ragdoll": ["ragdoll kitten", "ragdoll cat portrait"],
    "orange-tabby-kitten": ["orange tabby kitten", "ginger kitten"],
    "scottish-fold": ["scottish fold kitten", "scottish fold cat"],
}
LICENSE_RANK = [("cc0", 0), ("public domain", 0), ("pd", 0), ("cc by-sa", 2), ("cc by", 1)]
API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "dropshipping-cj-research-tool/1.0 (https://github.com/hduog/dropshipping-CJ-research-tool)"}
OUT = "pet-ad-workflow/pets/_candidates"
PER_PET = int(os.environ.get("PER_PET", "8"))


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def strip(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def lic_rank(name):
    n = name.lower()
    for key, rank in LICENSE_RANK:
        if n.startswith(key):
            return rank
    return None


def search(q):
    params = {
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
        "gsrsearch": q + " filetype:bitmap", "gsrlimit": 40, "prop": "imageinfo",
        "iiprop": "url|size|extmetadata|mime", "iiurlwidth": 1024,
    }
    data = json.loads(get(API + "?" + urllib.parse.urlencode(params)))
    for page in (data.get("query") or {}).get("pages", {}).values():
        ii = (page.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata") or {}
        lic = strip((meta.get("LicenseShortName") or {}).get("value"))
        rank = lic_rank(lic)
        if rank is None or ii.get("mime") != "image/jpeg" or min(ii.get("width", 0), ii.get("height", 0)) < 900:
            continue
        yield {
            "title": page["title"], "rank": rank, "index": page.get("index", 99),
            "license": lic, "licenseUrl": strip((meta.get("LicenseUrl") or {}).get("value")),
            "author": strip((meta.get("Artist") or {}).get("value")),
            "sourcePage": ii.get("descriptionurl"), "thumb": ii.get("thumburl"),
            "width": ii.get("width"), "height": ii.get("height"),
        }


def main():
    only = set(sys.argv[1:])
    for pet, queries in PETS.items():
        if only and pet not in only:
            continue
        seen, found = set(), []
        for q in queries:
            for c in search(q):
                if c["title"] not in seen:
                    seen.add(c["title"]); found.append(c)
        found.sort(key=lambda c: (c["rank"], c["index"]))
        d = os.path.join(OUT, pet); os.makedirs(d, exist_ok=True)
        kept = []
        for c in found:
            if len(kept) >= PER_PET:
                break
            name = "%02d.jpg" % (len(kept) + 1)
            try:
                open(os.path.join(d, name), "wb").write(get(c["thumb"]))
            except Exception as e:
                print("skip", c["title"], e); continue
            c["file"] = name; kept.append(c)
        json.dump(kept, open(os.path.join(d, "candidates.json"), "w"), indent=2, ensure_ascii=False)
        print(pet, len(found), "found,", len(kept), "saved")


if __name__ == "__main__":
    main()
