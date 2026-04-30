from dataclasses import dataclass


@dataclass
class ParsedQuery:
    raw: str
    head: str           # model/app token, lowercased
    kind: str           # "model" | "app" | "empty"
    action: str         # "list" | "search" | "change" | "add" | "index"
    term: str = ""      # search term
    pk: str = ""        # change page pk


def parse(raw: str) -> ParsedQuery:
    q = (raw or "").strip()
    if not q:
        return ParsedQuery(raw="", head="", kind="empty", action="list")

    if q.startswith("@"):
        return ParsedQuery(raw=q, head=q[1:].strip().lower(), kind="app", action="index")

    # Split head from the rest. Accept both "Model rest" and "Model?rest".
    head, sep, rest = q.partition(" ")
    if "?" in head and not sep:
        head, _, rest = q.partition("?")
    rest = rest.strip()

    if not rest:
        return ParsedQuery(raw=q, head=head.lower(), kind="model", action="list")

    if rest == "+":
        return ParsedQuery(raw=q, head=head.lower(), kind="model", action="add")

    if rest.startswith("#"):
        pk = rest[1:].strip()
        if pk:
            return ParsedQuery(raw=q, head=head.lower(), kind="model", action="change", pk=pk)

    # Anything else is a search term. Strip a leading "?" if the user typed "Model?term".
    term = rest[1:].strip() if rest.startswith("?") else rest
    return ParsedQuery(raw=q, head=head.lower(), kind="model", action="search", term=term)
