import re

TOKEN_REGEX = [
    ("FORALL", r"forall"),
    ("EXISTS", r"exists"),
    ("NOT", r"not"),
    ("AND", r"and"),
    ("OR", r"or"),
    ("IMPLIES", r"->"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("DOT", r"\."),
    ("COMMA", r","),
    ("IDENT", r"[A-Za-z][A-Za-z0-9_]*"),
    ("SKIP", r"\s+"),
]

def tokenize(text: str):
    tokens = []
    pos = 0

    while pos < len(text):
        match = None
        for token_type, regex in TOKEN_REGEX:
            pattern = re.compile(regex)
            match = pattern.match(text, pos)
            if match:
                value = match.group(0)
                if token_type != "SKIP":
                    tokens.append((token_type, value))
                pos = match.end()
                break

        if not match:
            raise SyntaxError(f"Unexpected character: {text[pos]}")

    return tokens