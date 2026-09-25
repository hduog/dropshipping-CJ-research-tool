#!/usr/bin/env node
// MCP server exposing CJ Dropshipping product search tools over stdio.
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { CJClient, flattenSearchResult } from "./cj-client.js";

const cj = new CJClient();
const server = new McpServer({ name: "cj-dropshipping", version: "1.0.0" });

const ok = (data) => ({ content: [{ type: "text", text: JSON.stringify(data, null, 2) }] });
const fail = (err) => ({
  isError: true,
  content: [
    {
      type: "text",
      text: `CJ API error${err.code ? ` (${err.code})` : ""}: ${err.message}${
        err.requestId ? ` [requestId ${err.requestId}]` : ""
      }`,
    },
  ],
});
const handle = (fn) => async (args) => {
  try {
    return ok(await fn(args));
  } catch (err) {
    return fail(err);
  }
};

const ORDER_BY = { best_match: 0, listed_count: 1, price: 2, newest: 3, inventory: 4 };
const PRODUCT_FLAG = { trending: 0, new: 1, video: 2, slow_moving: 3 };

server.registerTool(
  "cj_search_products",
  {
    title: "Search CJ products",
    description:
      "Search the CJ Dropshipping catalog (listV2). Filter by keyword, category, price range, ship-from country, " +
      "inventory, free shipping and trending/new flags. Returns a flattened product list with pid, price, " +
      "listed count (how many stores list it — a popularity signal), inventory and image.",
    inputSchema: {
      keyword: z.string().optional().describe("Search keyword, e.g. 'pet hair remover'"),
      page: z.number().int().min(1).max(1000).default(1),
      size: z.number().int().min(1).max(100).default(20),
      categoryId: z.string().optional().describe("Category id from cj_get_categories"),
      countryCode: z
        .string()
        .optional()
        .describe("Ship-from warehouse country, e.g. CN, US, DE, TH. See cj_list_warehouses"),
      minPrice: z.number().optional().describe("Minimum sell price (USD)"),
      maxPrice: z.number().optional().describe("Maximum sell price (USD)"),
      freeShipping: z.boolean().optional(),
      minInventory: z.number().int().optional(),
      maxInventory: z.number().int().optional(),
      verifiedWarehouse: z.boolean().optional().describe("Only products with verified warehouse inventory"),
      flag: z.enum(Object.keys(PRODUCT_FLAG)).optional().describe("trending | new | video | slow_moving"),
      orderBy: z.enum(Object.keys(ORDER_BY)).default("best_match"),
      sort: z.enum(["desc", "asc"]).default("desc"),
      createdAfter: z.string().optional().describe("ISO date; only products created after this"),
      createdBefore: z.string().optional().describe("ISO date; only products created before this"),
      raw: z.boolean().default(false).describe("Return the raw CJ response instead of the flattened list"),
    },
  },
  handle(async (a) => {
    const data = await cj.searchProducts({
      keyWord: a.keyword,
      page: a.page,
      size: a.size,
      categoryId: a.categoryId,
      countryCode: a.countryCode,
      startSellPrice: a.minPrice,
      endSellPrice: a.maxPrice,
      addMarkStatus: a.freeShipping === undefined ? undefined : a.freeShipping ? 1 : 0,
      startWarehouseInventory: a.minInventory,
      endWarehouseInventory: a.maxInventory,
      verifiedWarehouse: a.verifiedWarehouse ? 1 : undefined,
      productFlag: a.flag ? PRODUCT_FLAG[a.flag] : undefined,
      orderBy: ORDER_BY[a.orderBy],
      sort: a.sort,
      timeStart: a.createdAfter ? Date.parse(a.createdAfter) : undefined,
      timeEnd: a.createdBefore ? Date.parse(a.createdBefore) : undefined,
    });
    return a.raw ? data : flattenSearchResult(data);
  })
);

server.registerTool(
  "cj_get_product",
  {
    title: "Get CJ product details",
    description:
      "Get full details of one product (description, weight, images, all variants with vid/SKU/price). " +
      "Provide one of pid, productSku or variantSku.",
    inputSchema: {
      pid: z.string().optional(),
      productSku: z.string().optional(),
      variantSku: z.string().optional(),
      countryCode: z.string().optional(),
      includeDescription: z.boolean().default(false).describe("Include the (long HTML) description"),
    },
  },
  handle(async ({ includeDescription, ...a }) => {
    if (!a.pid && !a.productSku && !a.variantSku) {
      throw new Error("Provide pid, productSku or variantSku");
    }
    const p = await cj.getProduct(a);
    if (!includeDescription && p) delete p.description;
    return p;
  })
);

server.registerTool(
  "cj_get_categories",
  {
    title: "List CJ categories",
    description: "Full 3-level CJ category tree. Use categoryId values with cj_search_products.",
    inputSchema: {
      filter: z.string().optional().describe("Only return branches whose names contain this text"),
    },
  },
  handle(async ({ filter }) => {
    const tree = await cj.getCategories();
    if (!filter) return tree;
    const f = filter.toLowerCase();
    const hit = (s) => s?.toLowerCase().includes(f);
    return tree
      .map((l1) => {
        if (hit(l1.categoryFirstName)) return l1;
        const l2s = (l1.categoryFirstList ?? [])
          .map((l2) => {
            if (hit(l2.categorySecondName)) return l2;
            const l3s = (l2.categorySecondList ?? []).filter((l3) => hit(l3.categoryName));
            return l3s.length ? { ...l2, categorySecondList: l3s } : null;
          })
          .filter(Boolean);
        return l2s.length ? { ...l1, categoryFirstList: l2s } : null;
      })
      .filter(Boolean);
  })
);

server.registerTool(
  "cj_get_variants",
  {
    title: "Get CJ product variants",
    description: "List all variants (vid, SKU, price, dimensions) of a product.",
    inputSchema: { pid: z.string(), countryCode: z.string().optional() },
  },
  handle((a) => cj.getVariants(a))
);

server.registerTool(
  "cj_get_inventory",
  {
    title: "Get CJ inventory",
    description: "Inventory of a product per warehouse/country and per variant.",
    inputSchema: { pid: z.string() },
  },
  handle(({ pid }) => cj.getInventoryByPid(pid))
);

server.registerTool(
  "cj_get_reviews",
  {
    title: "Get CJ product reviews",
    description: "Customer reviews (rating, comment, images) for a product.",
    inputSchema: {
      pid: z.string(),
      page: z.number().int().min(1).default(1),
      size: z.number().int().min(1).max(100).default(20),
    },
  },
  handle((a) => cj.getReviews(a))
);

server.registerTool(
  "cj_search_by_image",
  {
    title: "Search CJ by image",
    description: "Find CJ products visually similar to a public image URL (e.g. a competitor's product photo).",
    inputSchema: { imageUrl: z.string().url() },
  },
  handle(({ imageUrl }) => cj.searchByImage(imageUrl))
);

server.registerTool(
  "cj_calculate_freight",
  {
    title: "Calculate CJ shipping cost",
    description:
      "Shipping options, cost (USD) and delivery time for variants from one country to another. " +
      "Get vid values from cj_get_product or cj_get_variants.",
    inputSchema: {
      startCountryCode: z.string().default("CN").describe("Ship-from country, e.g. CN, US"),
      endCountryCode: z.string().describe("Destination country, e.g. US, VN, DE"),
      products: z
        .array(z.object({ vid: z.string(), quantity: z.number().int().min(1).default(1) }))
        .min(1),
      zip: z.string().optional(),
    },
  },
  handle(async (a) => {
    const options = await cj.calculateFreight(a);
    return (options ?? []).sort((x, y) => (x.logisticPrice ?? 0) - (y.logisticPrice ?? 0));
  })
);

server.registerTool(
  "cj_list_warehouses",
  {
    title: "List CJ warehouses",
    description: "Global CJ warehouses and their country codes (for countryCode filters).",
    inputSchema: {},
  },
  handle(() => cj.getWarehouses())
);

await server.connect(new StdioServerTransport());
