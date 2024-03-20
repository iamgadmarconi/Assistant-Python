import spacy


def get_context(string: str, tokens: list[str]):
    if not set(tokens).issubset({"TIME", "DATE", "GPE"}):
        raise ValueError("Invalid token; must be one of 'TIME', 'DATE', or 'GPE'")

    nlp = spacy.load("en_core_web_sm")
    doc = nlp(string)

    res = [ent.text for ent in doc.ents if ent.label_ in tokens]

    result = " ".join(res)

    return result

