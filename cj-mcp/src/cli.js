#!/usr/bin/env node
// Command-line product search: node src/cli.js "keyword" [--country US] [--min 5] [--max 30] ...
import { parseArgs } from "node:util";
import { CJClient, flattenSearchResult } from "./cj-client.js";

const ORDER_BY = { best_match: 0, listed_count: 1, price: 2, newest: 3, inventory: 4 };
const PRODUCT_FLAG = { trending: 0, new: 1, video: 2, slow_moving: 3 };

const { values: o, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    country: { type: "string", short: "c" },
    category: { type: "string" },
    min: { type: "string" },
    max: { type: "string" },
    page: { type: "string", short: "p", default: "1" },
    size: { type: "string", short: "n", default: "20" },
    order: { type: "string", short: "o", default: "best_match" },
    sort: { type: "string", default: "desc" },
    flag: { type: "string" },
    "free-shipping": { type: "boolean" },
    json: { type: "boolean" },
    help: { type: "boolean", short: "h" },
  },
});

if (o.help) {
  console.log(`Usage: node src/cli.js [keyword] [options]

  -c, --country <CC>     ship-from warehouse country (CN, US, DE, TH...)
      --category <id>    category id
      --min / --max <n>  sell price range (USD)
  -o, --order <field>    ${Object.keys(ORDER_BY).join(" | ")}
      --sort <dir>       desc | asc
      --flag <flag>      ${Object.keys(PRODUCT_FLAG).join(" | ")}
      --free-shipping    only free-shipping products
  -p, --page <n>         page (default 1)
  -n, --size <n>         results per page, max 100 (default 20)
      --json             print JSON instead of a table`);
  process.exit(0);
}

const num = (v) => (v === undefined ? undefined : Number(v));

try {
  const data = await new CJClient().searchProducts({
    keyWord: positionals.join(" ") || undefined,
    countryCode: o.country,
    categoryId: o.category,
    startSellPrice: num(o.min),
    endSellPrice: num(o.max),
    page: num(o.page),
    size: num(o.size),
    orderBy: ORDER_BY[o.order] ?? 0,
    sort: o.sort,
    productFlag: o.flag ? PRODUCT_FLAG[o.flag] : undefined,
    addMarkStatus: o["free-shipping"] ? 1 : undefined,
  });
  const result = flattenSearchResult(data);

  if (o.json) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log(
      `Found ${result.totalRecords ?? 0} products — page ${result.page}/${result.totalPages ?? 1}\n`
    );
    console.table(
      result.products.map((p) => ({
        pid: p.pid,
        name: p.name?.length > 50 ? p.name.slice(0, 47) + "..." : p.name,
        price: p.nowPrice || p.sellPrice,
        listed: p.listedNum,
        stock: p.inventory,
        freeShip: p.freeShipping ? "yes" : "",
      }))
    );
  }
} catch (err) {
  console.error(`Error${err.code ? ` (${err.code})` : ""}: ${err.message}`);
  process.exit(1);
}
