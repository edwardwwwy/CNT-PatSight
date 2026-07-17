import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const packageDir = process.argv[2];
if (!packageDir) {
  throw new Error("usage: node build_eight_table_workbook.mjs <package-dir>");
}

const tables = [
  "source_master",
  "source_run",
  "catalyst_system",
  "reactor_process_gas",
  "yield_quality",
  "cost_scale_review",
  "evidence_index",
  "review_issue_log",
];

let workbook = null;
for (const [index, table] of tables.entries()) {
  const csvText = await fs.readFile(path.join(packageDir, `${table}.csv`), "utf8");
  if (index === 0) {
    workbook = await Workbook.fromCSV(csvText, { sheetName: table });
  } else {
    await workbook.fromCSV(csvText, { sheetName: table });
  }
}

for (const table of tables) {
  const sheet = workbook.worksheets.getItem(table);
  const used = sheet.getUsedRange(true);
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  used.format.font = { name: "Aptos", size: 10, color: "#172033" };
  used.format.verticalAlignment = "top";
  used.format.wrapText = true;
  used.format.borders = {
    insideHorizontal: { style: "thin", color: "#D9E1E8" },
    bottom: { style: "thin", color: "#B8C4CE" },
  };
  const header = used.getRow(0);
  header.format = {
    fill: "#174A5B",
    font: { name: "Aptos", size: 10, bold: true, color: "#FFFFFF" },
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "outside", style: "thin", color: "#103742" },
  };
  header.format.rowHeight = 34;
  used.format.autofitColumns();
  used.format.autofitRows();
  const columnCount = used.columnCount;
  for (let column = 0; column < columnCount; column += 1) {
    const columnRange = used.getColumn(column);
    if (columnRange.format.columnWidth > 34) {
      columnRange.format.columnWidth = 34;
    }
    if (columnRange.format.columnWidth < 11) {
      columnRange.format.columnWidth = 11;
    }
  }
}

const outputPath = path.join(packageDir, "extraction_workbook.xlsx");
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);

const previewDir = path.join(packageDir, "_workbook_preview");
await fs.mkdir(previewDir, { recursive: true });
for (const table of tables) {
  const preview = await workbook.render({
    sheetName: table,
    autoCrop: "all",
    scale: 0.7,
    format: "png",
  });
  await fs.writeFile(
    path.join(previewDir, `${table}.png`),
    new Uint8Array(await preview.arrayBuffer()),
  );
}

const inspect = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 5000,
  tableMaxRows: 4,
  tableMaxCols: 8,
  tableMaxCellChars: 80,
});
await fs.writeFile(
  path.join(packageDir, "_workbook_inspect.ndjson"),
  inspect.ndjson,
  "utf8",
);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
await fs.writeFile(
  path.join(packageDir, "_workbook_formula_errors.ndjson"),
  errors.ndjson,
  "utf8",
);

console.log(outputPath);
