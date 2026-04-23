import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";

export type RepoItem = {
  slug: string;
  title: string;
  path: string;
  category: string;
  summary: string;
  body: string;
};

export type DatasetSummary = {
  slug: string;
  title: string;
  path: string;
  rows: number;
  columns: string[];
  sample: Record<string, string>[];
};

export type IssueRoute = {
  issue_key: string;
  issue_name: string;
  first_route_type: string;
  possible_eu_layer: string;
  possible_national_layer: string;
  evidence_priority: string;
  notes: string;
};

export type AuthorityRow = Record<string, string>;

export type ContactRow = Record<string, string>;

export type Catalog = {
  repoRoot: string;
  playbooks: RepoItem[];
  templates: RepoItem[];
  emailTemplates: RepoItem[];
  datasets: DatasetSummary[];
  issueRoutes: IssueRoute[];
  nationalAuthorities: AuthorityRow[];
  contactRows: ContactRow[];
};

function slugFromFilename(filePath: string): string {
  return path.basename(filePath, path.extname(filePath));
}

function readText(filePath: string): string {
  return readFileSync(filePath, "utf8");
}

function firstMarkdownHeading(text: string): string {
  const match = text.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : "";
}

function firstParagraph(text: string): string {
  const normalized = text.replace(/\r/g, "");
  const withoutHeading = normalized.replace(/^#.*$/m, "").trim();
  const blocks = withoutHeading
    .split(/\n\s*\n/)
    .map((block) => block.trim().replace(/\n+/g, " "))
    .filter(Boolean);
  return blocks[0] ?? "";
}

function loadMarkdownItems(
  repoRoot: string,
  relativeDir: string,
  category: string,
  options?: { include?: (name: string) => boolean },
): RepoItem[] {
  const absoluteDir = path.join(repoRoot, relativeDir);
  const names = readdirSync(absoluteDir)
    .filter((name: string) => name.endsWith(".md"))
    .filter((name: string) => (options?.include ? options.include(name) : true))
    .sort();

  return names.map((name: string) => {
    const absolutePath = path.join(absoluteDir, name);
    const body = readText(absolutePath);
    return {
      slug: slugFromFilename(name),
      title: firstMarkdownHeading(body) || slugFromFilename(name),
      path: absolutePath,
      category,
      summary: firstParagraph(body),
      body,
    };
  });
}

function parseCsv(text: string): Record<string, string>[] {
  const lines = text.replace(/\r/g, "").split("\n").filter(Boolean);
  if (lines.length === 0) {
    return [];
  }

  const rows: string[][] = [];
  let current = "";
  let row: string[] = [];
  let inQuotes = false;

  const pushCell = () => {
    row.push(current);
    current = "";
  };

  const pushRow = () => {
    rows.push(row);
    row = [];
  };

  const full = text.replace(/\r/g, "");
  for (let i = 0; i < full.length; i += 1) {
    const char = full[i];
    const next = full[i + 1];

    if (char === "\"") {
      if (inQuotes && next === "\"") {
        current += "\"";
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (char === "," && !inQuotes) {
      pushCell();
      continue;
    }

    if (char === "\n" && !inQuotes) {
      pushCell();
      pushRow();
      continue;
    }

    current += char;
  }

  if (current.length > 0 || row.length > 0) {
    pushCell();
    pushRow();
  }

  const [header, ...dataRows] = rows;
  return dataRows
    .filter((cells) => cells.some((cell) => cell.trim() !== ""))
    .map((cells) => {
      const record: Record<string, string> = {};
      for (let index = 0; index < header.length; index += 1) {
        record[header[index]] = cells[index] ?? "";
      }
      return record;
    });
}

export function readCsvFile(filePath: string): Record<string, string>[] {
  return parseCsv(readText(filePath));
}

function csvTitleFromSlug(slug: string): string {
  return slug
    .split("-")
    .map((part) => (part ? part[0].toUpperCase() + part.slice(1) : part))
    .join(" ");
}

function loadDatasets(repoRoot: string): DatasetSummary[] {
  const sections = readdirSync(path.join(repoRoot, "data"), {
    withFileTypes: true,
  }).filter((entry: { isDirectory(): boolean }) => entry.isDirectory());

  const output: DatasetSummary[] = [];

  for (const section of sections) {
    const sectionDir = path.join(repoRoot, "data", section.name);
    const csvNames = readdirSync(sectionDir)
      .filter((name: string) => name.endsWith(".csv"))
      .sort();

    for (const csvName of csvNames) {
      const absolutePath = path.join(sectionDir, csvName);
      const rows = readCsvFile(absolutePath);
      const columns = rows[0] ? Object.keys(rows[0]) : [];
      output.push({
        slug: slugFromFilename(csvName),
        title: csvTitleFromSlug(slugFromFilename(csvName)),
        path: absolutePath,
        rows: rows.length,
        columns,
        sample: rows.slice(0, 3),
      });
    }
  }

  return output.sort((a, b) => a.slug.localeCompare(b.slug));
}

function loadIssueRoutes(repoRoot: string): IssueRoute[] {
  const rows = parseCsv(
    readText(path.join(repoRoot, "data", "national-authorities", "issue-router.csv")),
  );
  return rows as IssueRoute[];
}

function loadNationalAuthorities(repoRoot: string): AuthorityRow[] {
  return parseCsv(
    readText(
      path.join(
        repoRoot,
        "data",
        "national-authorities",
        "national-digital-authorities.csv",
      ),
    ),
  );
}

function loadContactRows(repoRoot: string): ContactRow[] {
  const contactFiles = [
    path.join(
      repoRoot,
      "data",
      "community-contacts",
      "eu-digital-rights-and-media-contacts.csv",
    ),
    path.join(
      repoRoot,
      "data",
      "community-contacts",
      "national-digital-rights-organisations.csv",
    ),
    path.join(
      repoRoot,
      "data",
      "community-contacts",
      "womens-rights-and-gender-equality-contacts.csv",
    ),
    path.join(
      repoRoot,
      "data",
      "commission-reference",
      "commission-spp-contacts.csv",
    ),
    path.join(
      repoRoot,
      "data",
      "commission-reference",
      "commission-cabinet-contacts.csv",
    ),
    path.join(
      repoRoot,
      "data",
      "institutional-contacts",
      "institutional-contacts.csv",
    ),
  ];

  return contactFiles.flatMap((filePath) =>
    readCsvFile(filePath).map((row) => ({
      ...row,
      __source_path: filePath,
    })),
  );
}

export function buildCatalog(repoRoot: string): Catalog {
  return {
    repoRoot,
    playbooks: loadMarkdownItems(repoRoot, "docs/digital-issues", "playbook", {
      include: (name) => name !== "README.md",
    }),
    templates: [
      ...loadMarkdownItems(repoRoot, "templates/level-0-public-comment", "template", {
        include: (name) => name !== "README.md",
      }),
      ...loadMarkdownItems(repoRoot, "templates/level-1-administrative", "template", {
        include: (name) => name !== "README.md",
      }),
    ].sort((a, b) => a.slug.localeCompare(b.slug)),
    emailTemplates: loadMarkdownItems(
      repoRoot,
      "docs/digital-issues/email-templates",
      "email-template",
      { include: (name) => name !== "README.md" },
    ),
    datasets: loadDatasets(repoRoot),
    issueRoutes: loadIssueRoutes(repoRoot),
    nationalAuthorities: loadNationalAuthorities(repoRoot),
    contactRows: loadContactRows(repoRoot),
  };
}

export function getItemBySlug(items: RepoItem[], slug: string): RepoItem | undefined {
  return items.find((item) => item.slug === slug);
}

export function getDatasetBySlug(
  datasets: DatasetSummary[],
  slug: string,
): DatasetSummary | undefined {
  return datasets.find((dataset) => dataset.slug === slug);
}
