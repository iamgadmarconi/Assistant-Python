import os
import asyncio
import geocoder
import spacy

from O365 import Account, MSGraphProtocol
from geopy.geocoders import Nominatim


def getLocation():
    g = geocoder.ip('me').city
    geolocator = Nominatim(user_agent="User")
    location = geolocator.geocode(g)
    return location

def O365Auth(scopes_helper: list[str] = ['basic']):
    protocol = MSGraphProtocol()
    credentials = (os.environ.get("CLIENT_ID"), os.environ.get("CLIENT_SECRET"))
    scopes_graph = protocol.get_scopes_for(scopes_helper)

    try:
        account = Account(credentials, protocol=protocol)

        if not account.is_authenticated:
            account.authenticate(scopes=scopes_graph)

        
        return account
    
    except:
        raise Exception("Failed to authenticate with O365")


def getContext(string: str, tokens: list[str]):
    if not set(tokens).issubset({"TIME", "DATE", "GPE"}):
        raise ValueError("Invalid token; must be one of 'TIME', 'DATE', or 'GPE'")

    nlp = spacy.load("en_core_web_sm")
    doc = nlp(string)

    res = [ent.text for ent in doc.ents if ent.label_ in tokens]

    result = " ".join(res)

    return result

async def confirm_event():
    pass