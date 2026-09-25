// Minimal client for CJ Dropshipping API 2.0
// Docs: https://developers.cjdropshipping.com/en/api/introduction.html
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const BASE_URL = "https://developers.cjdropshipping.com/api2.0/v1";
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TOKEN_FILE = path.join(ROOT, ".cj-token.json");

// Load KEY=VALUE pairs from cj-mcp/.env without overriding real env vars.
function loadDotEnv() {
  const file = path.join(ROOT, ".env");
  if (!fs.existsSync(file)) return;
  for (const line of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/);
    if (!m || line.trim().startsWith("#")) continue;
    const value = m[2].replace(/^["']|["']$/g, "");
    if (process.env[m[1]] === undefined) process.env[m[1]] = value;
  }
}
loadDotEnv();

export class CJError extends Error {
  constructor(message, { code, requestId } = {}) {
    super(message);
    this.code = code;
    this.requestId = requestId;
  }
}

export class CJClient {
  constructor({
    apiKey = process.env.CJ_API_KEY,
    minIntervalMs = Number(process.env.CJ_MIN_INTERVAL_MS ?? 1100),
  } = {}) {
    this.apiKey = apiKey;
    // Free accounts are limited to 1 request/second, so calls are serialized.
    this.minIntervalMs = minIntervalMs;
    this.queue = Promise.resolve();
    this.lastCallAt = 0;
    this.token = this.#readTokenCache();
  }

  #readTokenCache() {
    try {
      return JSON.parse(fs.readFileSync(TOKEN_FILE, "utf8"));
    } catch {
      return null;
    }
  }

  #writeTokenCache(token) {
    this.token = token;
    try {
      fs.writeFileSync(TOKEN_FILE, JSON.stringify(token, null, 2));
    } catch {
      // Cache is an optimization; ignore write failures.
    }
  }

  #isValid(dateStr, marginMs = 60 * 60 * 1000) {
    if (!dateStr) return false;
    const t = Date.parse(dateStr);
    return Number.isFinite(t) && t - marginMs > Date.now();
  }

  // Serialize every HTTP call and keep them at least minIntervalMs apart.
  #throttle(fn) {
    const run = this.queue.then(async () => {
      const wait = this.lastCallAt + this.minIntervalMs - Date.now();
      if (wait > 0) await new Promise((r) => setTimeout(r, wait));
      try {
        return await fn();
      } finally {
        this.lastCallAt = Date.now();
      }
    });
    this.queue = run.catch(() => {});
    return run;
  }

  async #rawRequest(method, endpoint, { query, body, token } = {}) {
    const url = new URL(BASE_URL + endpoint);
    for (const [k, v] of Object.entries(query ?? {})) {
      if (v === undefined || v === null || v === "") continue;
      url.searchParams.set(k, Array.isArray(v) ? v.join(",") : String(v));
    }
    const headers = { "Content-Type": "application/json" };
    if (token) headers["CJ-Access-Token"] = token;

    const res = await this.#throttle(() =>
      fetch(url, { method, headers, body: body ? JSON.stringify(body) : undefined })
    );
    const text = await res.text();
    let json;
    try {
      json = JSON.parse(text);
    } catch {
      throw new CJError(`HTTP ${res.status}: ${text.slice(0, 300)}`, { code: res.status });
    }
    if (!res.ok || json.result === false || (json.code && json.code !== 200)) {
      throw new CJError(json.message || `HTTP ${res.status}`, {
        code: json.code ?? res.status,
        requestId: json.requestId,
      });
    }
    return json.data;
  }

  async #authenticate() {
    if (!this.apiKey) {
      throw new CJError(
        "Missing CJ_API_KEY. Get it at CJ Dropshipping > My CJ > Authorization > API, then put it in cj-mcp/.env"
      );
    }
    const data = await this.#rawRequest("POST", "/authentication/getAccessToken", {
      body: { apiKey: this.apiKey },
    });
    this.#writeTokenCache(data);
    return data.accessToken;
  }

  async #refresh() {
    const data = await this.#rawRequest("POST", "/authentication/refreshAccessToken", {
      body: { refreshToken: this.token.refreshToken },
    });
    this.#writeTokenCache({ ...this.token, ...data });
    return data.accessToken;
  }

  async getAccessToken({ force = false } = {}) {
    const t = this.token;
    if (!force && t?.accessToken && this.#isValid(t.accessTokenExpiryDate)) return t.accessToken;
    if (t?.refreshToken && this.#isValid(t.refreshTokenExpiryDate)) {
      try {
        return await this.#refresh();
      } catch {
        // Fall through to a fresh login.
      }
    }
    return this.#authenticate();
  }

  async request(method, endpoint, opts = {}) {
    const token = await this.getAccessToken();
    try {
      return await this.#rawRequest(method, endpoint, { ...opts, token });
    } catch (err) {
      // Token revoked or expired server-side: log in again once and retry.
      if (/token/i.test(err.message)) {
        const fresh = await this.getAccessToken({ force: true });
        return this.#rawRequest(method, endpoint, { ...opts, token: fresh });
      }
      throw err;
    }
  }

  get(endpoint, query) {
    return this.request("GET", endpoint, { query });
  }

  post(endpoint, body) {
    return this.request("POST", endpoint, { body });
  }

  // ---- Product endpoints -------------------------------------------------

  searchProducts(params) {
    return this.get("/product/listV2", params);
  }

  getProduct({ pid, productSku, variantSku, countryCode }) {
    return this.get("/product/query", { pid, productSku, variantSku, countryCode });
  }

  getCategories() {
    return this.get("/product/getCategory");
  }

  getVariants({ pid, countryCode }) {
    return this.get("/product/getAllVariants", { pid, countryCode });
  }

  getInventoryByPid(pid) {
    return this.get("/product/inventory/pid", { pid });
  }

  getReviews({ pid, page, size }) {
    return this.get("/product/comments", { pid, page, size });
  }

  searchByImage(imageUrl) {
    return this.post("/product/queryProductsByImage", { imageUrl });
  }

  getWarehouses() {
    return this.get("/product/globalWarehouseList");
  }

  // ---- Logistics ---------------------------------------------------------

  calculateFreight({ startCountryCode, endCountryCode, products, zip }) {
    return this.post("/logistic/freightCalculate", {
      startCountryCode,
      endCountryCode,
      products,
      zip,
    });
  }
}

// listV2 nests results as data.content[].productList[]; flatten and keep the useful fields.
export function flattenSearchResult(data) {
  const products = (data?.content ?? []).flatMap((c) => c.productList ?? []);
  return {
    page: data?.pageNumber,
    pageSize: data?.pageSize,
    totalRecords: data?.totalRecords,
    totalPages: data?.totalPages,
    products: products.map((p) => ({
      pid: p.id,
      name: p.nameEn,
      sku: p.sku,
      sellPrice: p.sellPrice,
      nowPrice: p.nowPrice,
      discountPrice: p.discountPrice,
      listedNum: p.listedNum,
      category: [p.oneCategoryName, p.twoCategoryName, p.threeCategoryName]
        .filter(Boolean)
        .join(" > "),
      categoryId: p.categoryId,
      inventory: p.warehouseInventoryNum,
      verifiedInventory: p.totalVerifiedInventory,
      freeShipping: p.addMarkStatus === 1,
      hasVideo: Boolean(p.isVideo),
      supplier: p.supplierName,
      deliveryCycle: p.deliveryCycle,
      createAt: p.createAt,
      image: p.bigImage,
      url: p.id ? `https://cjdropshipping.com/product/-p-${p.id}.html` : undefined,
    })),
  };
}
