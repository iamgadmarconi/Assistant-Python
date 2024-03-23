import spacy
from bs4 import BeautifulSoup


def get_context(string: str, tokens: list[str]):
    if not set(tokens).issubset({"TIME", "DATE", "GPE"}):
        raise ValueError("Invalid token; must be one of 'TIME', 'DATE', or 'GPE'")

    nlp = spacy.load("en_core_web_sm")

    try:
        doc = nlp(string)

        res = [ent.text for ent in doc.ents if ent.label_ in tokens]

        result = " ".join(res)

        return result
    
    except:
        return ""

def html_to_text(html: str, ignore_script_and_style: bool = True):
    soup = BeautifulSoup(html, "html.parser")
    
    # Optional: Remove script and style elements
    if ignore_script_and_style:
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
    
    # Get text
    text = soup.get_text()
    
    # Break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # Drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    return text