import type { Catalog, ContactRow, IssueRoute, RepoItem } from "./catalog.js";

function tokenize(value: string): string[] {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((token) => token.length > 1);
}

function scoreText(haystack: string, needles: string[]): number {
  const lower = haystack.toLowerCase();
  let score = 0;

  for (const needle of needles) {
    if (lower.includes(needle)) {
      score += needle.length > 5 ? 3 : 1;
    }
  }

  return score;
}

function routeKeywords(route: IssueRoute): string[] {
  return tokenize(
    [
      route.issue_key,
      route.issue_name,
      route.first_route_type,
      route.possible_eu_layer,
      route.possible_national_layer,
      route.evidence_priority,
      route.notes,
    ].join(" "),
  );
}

function playbookKeywords(playbook: RepoItem): string[] {
  return tokenize(`${playbook.slug} ${playbook.title} ${playbook.summary}`);
}

export function rankIssueMatches(catalog: Catalog, problemDescription: string) {
  const needles = tokenize(problemDescription);
  const routeMatches = catalog.issueRoutes
    .map((route) => ({
      route,
      score: scoreText(routeKeywords(route).join(" "), needles),
    }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);

  const playbookMatches = catalog.playbooks
    .map((playbook) => ({
      playbook,
      score: scoreText(playbookKeywords(playbook).join(" "), needles),
    }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);

  return { routeMatches, playbookMatches };
}

export function filterAuthorities(
  catalog: Catalog,
  country: string,
  issueType?: string,
): ContactRow[] {
  const countryLower = country.toLowerCase();
  const issueLower = issueType?.toLowerCase() ?? "";

  return catalog.nationalAuthorities
    .filter((row) => (row.country || row.member_state || "").toLowerCase() === countryLower)
    .map((row) => ({
      ...row,
      __match_reason: issueLower
        ? `Matched country ${country} with issue context ${issueType}`
        : `Matched country ${country}`,
    }));
}

export function findRelevantContacts(
  catalog: Catalog,
  topic: string,
  audience?: string,
  country?: string,
) {
  const needles = tokenize([topic, audience ?? "", country ?? ""].join(" "));
  const countryLower = country?.toLowerCase();

  return catalog.contactRows
    .map((row) => {
      const searchable = Object.values(row).join(" ").toLowerCase();
      let score = scoreText(searchable, needles);

      if (countryLower && searchable.includes(countryLower)) {
        score += 3;
      }

      return { row, score };
    })
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 10);
}
