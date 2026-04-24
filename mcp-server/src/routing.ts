import type { Catalog, ContactRow, IssueRoute, RepoItem } from "./catalog.js";

function tokenize(value: string): string[] {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((token) => token.length > 1);
}

function normalizeCountry(value: string): string {
  const normalized = value
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  const aliases: Record<string, string> = {
    "czech republic": "czechia",
    "republic of north macedonia": "north macedonia",
    "fyrom": "north macedonia",
    "united kingdom": "uk",
    "great britain": "uk",
  };

  return aliases[normalized] ?? normalized;
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
  const topicNeedles = tokenize(topic);
  const audienceNeedles = tokenize(audience ?? "");
  const normalizedCountry = country ? normalizeCountry(country) : undefined;
  const countryFields = [
    "country",
    "country_name",
    "country_or_label",
    "jurisdiction",
  ];

  const ranked = catalog.contactRows
    .map((row) => {
      const searchable = Object.values(row).join(" ").toLowerCase();
      const countryValues = countryFields
        .map((field) => row[field] ?? "")
        .filter(Boolean);
      const exactCountryMatch = normalizedCountry
        ? countryValues.some((value) => normalizeCountry(value) === normalizedCountry)
        : false;
      const topicScore = scoreText(searchable, topicNeedles);
      const audienceScore = audienceNeedles.length > 0 ? scoreText(searchable, audienceNeedles) : 0;
      let score = topicScore + (audienceScore > 0 ? 1 : 0);

      if (exactCountryMatch) {
        score += 5;
      } else if (normalizedCountry && searchable.includes(normalizedCountry)) {
        score += 2;
      }

      return {
        row: {
          ...row,
          __country_match: exactCountryMatch ? "exact" : "none",
          __country_values: countryValues.join(" | "),
        },
        score,
        topicScore,
        exactCountryMatch,
      };
    })
    .filter((item) => item.topicScore > 0 || item.exactCountryMatch)
    .sort((a, b) => {
      const aCountryAndTopic = a.exactCountryMatch && a.topicScore > 0;
      const bCountryAndTopic = b.exactCountryMatch && b.topicScore > 0;
      if (aCountryAndTopic !== bCountryAndTopic) {
        return aCountryAndTopic ? -1 : 1;
      }
      if (a.topicScore !== b.topicScore) {
        return b.topicScore - a.topicScore;
      }
      if (a.exactCountryMatch !== b.exactCountryMatch) {
        return a.exactCountryMatch ? -1 : 1;
      }
      return b.score - a.score;
    });

  const countryMatchesFound = ranked.filter((item) => item.exactCountryMatch).length;
  const matches = ranked.slice(0, 10);

  return {
    matches,
    countryMatchesFound,
    fallbackStrategy:
      country && countryMatchesFound === 0
        ? "No country-specific matches were indexed for this query; broader EU-level or cross-border results were returned."
        : null,
  };
}
