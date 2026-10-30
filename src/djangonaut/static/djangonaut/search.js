export function parseQuery(raw) {
  const query = raw.trim();
  const match = /^(\S+?)(?:\s*#([\s\S]*)|\s+([\s\S]*))?$/.exec(query);
  if (!match) return { head: "", action: "list", value: "" };

  const [, head, pk, rest] = match;
  if (pk !== undefined) return { head, action: "change", value: pk.trim() };
  const value = (rest || "").trim();
  if (value === "+") return { head, action: "add", value: "" };
  return { head, action: value ? "search" : "list", value };
}

function normalize(text) {
  return text.normalize("NFKD").replace(/\p{M}/gu, "").toLowerCase();
}

function score(query, candidate) {
  const text = normalize(candidate);
  if (!query) return 1;
  if (text === query) return 100;
  if (text.startsWith(query)) return 80 + query.length / text.length;
  if (text.includes(query)) return 60;

  let position = -1;
  let gaps = 0;
  for (const char of query) {
    const next = text.indexOf(char, position + 1);
    if (next === -1) return 0;
    gaps += next - position - 1;
    position = next;
  }
  return 40 / (1 + gaps);
}

function matchModels({ head, action, value }, catalog) {
  const query = normalize(head);

  return catalog.models.flatMap((model) => {
    const names = query.includes(".")
      ? [model.key]
      : [model.name, ...model.keywords];
    const rank = Math.max(...names.map((word) => score(query, word)));
    if (!rank) return [];

    let url = {
      list: model.list_url,
      search: model.searchable ? model.list_url : null,
      change: model.change_url,
      add: model.add_url,
    }[action];
    if (!url) return [];

    let detail = catalog.labels[action];
    if (action === "search") {
      const params = new URLSearchParams({ q: value });
      url = `${url}${url.includes("?") ? "&" : "?"}${params}`;
    } else if (action === "change") {
      // Django admin quoting must precede URI encoding, including for string primary keys.
      const pk = Array.from(
        value,
        (char) => catalog.quote_map[char] ?? char,
      ).join("");
      url = value
        ? url.replace(
            catalog.pk_placeholder,
            encodeURIComponent(pk.toWellFormed()),
          )
        : null;
      if (!value) detail = catalog.labels.record_id;
    }

    return [
      {
        label: model.name,
        key: model.key,
        detail: detail.replace("%(value)s", () =>
          action === "add" ? model.singular : value,
        ),
        url,
        rank,
      },
    ];
  });
}

export function getResults(raw, catalog) {
  const query = parseQuery(raw);
  const results = matchModels(query, catalog);
  if (query.action === "search") {
    const modelNames = matchModels(
      { head: raw.trim(), action: "list", value: "" },
      catalog,
    );
    for (const result of modelNames) result.rank += 100;
    results.push(...modelNames);
  }
  return results.sort(
    (a, b) =>
      b.rank - a.rank ||
      a.label.localeCompare(b.label) ||
      a.key.localeCompare(b.key),
  );
}
