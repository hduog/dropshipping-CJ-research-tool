// Build a self-contained HTML viewer from a CJ export folder.
// Usage: node tools/cj-viewer/build.js <folder> [<folder> ...]
// Writes <folder>/<folderName>_viewer.html
const fs = require('fs');
const path = require('path');

const readJson = f => JSON.parse(fs.readFileSync(f, 'utf8').replace(/^﻿/, ''));
// Exports may wrap each MCP response, e.g. {tool, args, data} or {tool, params, response} or {tool, ..., product}.
const unwrap = o => {
  if (!o || typeof o !== 'object' || !('tool' in o)) return o;
  for (const k of ['data', 'response', 'product']) if (o[k] && typeof o[k] === 'object') return o[k];
  return o;
};
const parseMaybe = v => { if (typeof v !== 'string') return v; try { return JSON.parse(v); } catch { return v; } };

function normReviews(rv) {
  rv = unwrap(rv) || {};
  if (Array.isArray(rv.pages) || Array.isArray(rv.all_reviews)) {
    const list = Array.isArray(rv.all_reviews) ? rv.all_reviews : rv.pages.flatMap(p => p.list || []);
    return { total: rv.total ?? list.length, list, complete: rv.complete !== false && list.length >= (rv.total ?? 0) };
  }
  const list = rv.list || [];
  return { ...rv, total: rv.total ?? list.length, list, complete: list.length >= (rv.total ?? list.length) };
}

function normDetail(d) {
  d = unwrap(d) || {};
  const img = parseMaybe(d.productImage);
  d.productImage = Array.isArray(img) ? img : (d.productImageSet || []);
  for (const k of ['materialNameEn', 'packingNameEn', 'productProEn', 'productKeyEn', 'productName'])
    if (!Array.isArray(d[k + 'Set'])) { const v = parseMaybe(d[k]); if (Array.isArray(v)) d[k + 'Set'] = v; }
  return d;
}

function loadProduct(root, dir) {
  const sku = dir.slice(3);
  const all = path.join(root, dir, `ALL_${sku}.json`);
  const src = fs.existsSync(all) ? readJson(all) : {
    search_products: readJson(path.join(root, dir, '01_search_products.json')),
    get_product_detail: readJson(path.join(root, dir, '02_get_product_detail.json')),
    get_product_inventory: readJson(path.join(root, dir, '03_get_product_inventory.json')),
    get_product_reviews: readJson(path.join(root, dir, '04_get_product_reviews.json')),
  };
  return {
    rank: +dir.slice(0, 2), folder: dir,
    search_products: unwrap(src.search_products),
    get_product_detail: normDetail(src.get_product_detail),
    get_product_inventory: unwrap(src.get_product_inventory),
    get_product_reviews: normReviews(src.get_product_reviews),
  };
}

function build(root) {
  root = path.resolve(root);
  const name = path.basename(root);
  const dirs = fs.readdirSync(root).filter(d => /^0[1-9]_/.test(d) && fs.statSync(path.join(root, d)).isDirectory()).sort();
  const products = dirs.map(d => loadProduct(root, d));
  const bad = products.filter(p => !p.get_product_detail.productSku || !Array.isArray(p.get_product_detail.variants));
  if (bad.length) throw new Error(`Không đọc được get_product_detail của ${bad.map(p => p.folder).join(', ')} — định dạng JSON mới, cần cập nhật unwrap() trong build.js`);

  const catFile = fs.readdirSync(root).find(f => /^00_search.*\.json$/.test(f));
  // Collect every productList anywhere in the file (single page, pages[].data, ...), de-duplicated by id.
  const found = [], seen = new Set();
  (function walk(o) {
    if (Array.isArray(o)) return o.forEach(walk);
    if (!o || typeof o !== 'object') return;
    if (Array.isArray(o.productList)) for (const p of o.productList) if (!seen.has(p.id)) { seen.add(p.id); found.push(p); }
    Object.values(o).forEach(walk);
  })(catFile ? readJson(path.join(root, catFile)) : null);
  const catList = found.sort((a, b) => (b.listedNum ?? 0) - (a.listedNum ?? 0)).map(p => ({
    id: p.id, sku: p.sku, nameEn: p.nameEn, listedNum: p.listedNum, sellPrice: p.sellPrice,
    bigImage: p.bigImage, inv: p.warehouseInventoryNum, verified: p.totalVerifiedInventory,
    video: p.isVideo || p.isVedio, url: p.productUrl,
  }));

  const readme = fs.existsSync(path.join(root, 'README.txt')) ? fs.readFileSync(path.join(root, 'README.txt'), 'utf8') : '';
  const dm = readme.match(/(\d{4})-(\d{2})-(\d{2})/) || readme.match(/(\d{2})\/(\d{2})\/(\d{4})/);
  const generated = !dm ? null : dm[1].length === 4 ? `${dm[1]}-${dm[2]}-${dm[3]}` : `${dm[3]}-${dm[2]}-${dm[1]}`;
  const categoryPath = products[0]?.get_product_detail.categoryName || '';
  const category = categoryPath.split(/\s[>/]\s/).pop().trim() || name;

  const DATA = { title: `CJ Top ${products.length} · ${category}`, categoryPath, products, catList, generated };
  const tpl = fs.readFileSync(path.join(__dirname, 'template.html'), 'utf8');
  const json = JSON.stringify(DATA).replace(/</g, '\\u003c');
  const out = tpl.replace('/*__DATA__*/null', () => json).replace('<title>CJ Viewer</title>', () => `<title>${DATA.title.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</title>`);
  const file = path.join(root, `${name}_viewer.html`);
  fs.writeFileSync(file, out);
  console.log(`${file}: ${products.length} products, ${catList.length} category items, ${out.length} bytes`);
}

const args = process.argv.slice(2);
if (!args.length) { console.error('Usage: node build.js <folder> [...]'); process.exit(1); }
args.forEach(build);
