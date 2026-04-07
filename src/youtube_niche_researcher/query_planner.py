from __future__ import annotations


DEFAULT_EXPANSIONS = [
    "{seed}",
    "{seed} documentary",
    "{seed} explained",
    "dark {seed}",
    "{seed} story",
]


def build_queries(seed: str, *, expand: bool = False, custom_queries: list[str] | None = None) -> list[str]:
    seed = seed.strip()
    queries: list[str] = []
    if custom_queries:
        queries.extend(query.strip() for query in custom_queries if query.strip())
    if expand:
        queries.extend(template.format(seed=seed) for template in DEFAULT_EXPANSIONS)
    else:
        queries.append(seed)
    return list(dict.fromkeys(queries))

