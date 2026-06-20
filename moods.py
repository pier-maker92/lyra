"""
20 mood categories for lyric embedding annotation.

Each mood has a keyword-dense prompt designed for embedding similarity matching.
Prompts are intentionally repetitive and keyword-heavy so the model maps them
into a stable region of the embedding space.

Genre affinities are multipliers applied to cosine similarity scores before
mood assignment. 1.0 = neutral, >1.0 = boost, <1.0 = suppress.
"""

MOODS: dict[str, dict] = {
    # ── emotional pain ──────────────────────────────────────────────────────
    "heartbreak": {
        "alias": "Heartbreak",
        "description": "Loss, tears, and the ache of a broken heart",
        "keywords": (
            "broken heart tears crying pain loss sadness alone missing you gone "
            "hurt empty grief sorrow heartbreak sad crying alone pain broken"
        ),
    },
    "melancholy": {
        "alias": "Blue",
        "description": "Soft sadness, bittersweet longing, quiet drifting emotion",
        "keywords": (
            "gray sky drift quiet longing fade wistful soft sorrow still ache "
            "gentle sadness twilight bittersweet longing quiet fading gray melancholy"
        ),
    },
    "lonely_isolated": {
        "alias": "Alone",
        "description": "Total solitude, invisible, cold, disconnected from everyone",
        "keywords": (
            "alone silence empty cold no one hollow disconnected invisible room "
            "isolation solitude dark quiet abandoned lonely isolated empty alone"
        ),
    },
    "anger_rebellion": {
        "alias": "Rage",
        "description": "Raw rage and defiance burning against rules and enemies",
        "keywords": (
            "rage fight rebel hate fire fury destroy enemy scream burn break rules "
            "anger protest defiance explosive rebel rage hate fight fury burn"
        ),
    },
    # ── love & desire ────────────────────────────────────────────────────────
    "romantic_love": {
        "alias": "Love",
        "description": "Tender devotion, kisses, forever, deep heartfelt affection",
        "keywords": (
            "love together forever kiss hold heart devotion tender sweet darling "
            "romance affection intimate longing love kiss forever hold tender"
        ),
    },
    "desire_sensuality": {
        "alias": "Desire",
        "description": "Lust, body heat, attraction, and electric closeness",
        "keywords": (
            "body heat skin lust touch attraction pull close want night desire "
            "sensual electric magnetic hunger desire heat body skin close touch"
        ),
    },
    # ── energy & celebration ─────────────────────────────────────────────────
    "party_hype": {
        "alias": "Party",
        "description": "Dance floor energy, loud nightlife, hype and celebration",
        "keywords": (
            "dance club night energy crowd loud turn up celebrate move bass "
            "hype party dance move loud energy night crowd celebrate"
        ),
    },
    "euphoria_dance": {
        "alias": "Euphoria",
        "description": "Electric peak rush, weightless pulse, trance drop high",
        "keywords": (
            "electric rush pulse high float glow peak alive surge weightless "
            "euphoria trance drop beat lift soar electric pulse rush glow alive"
        ),
    },
    "summer_good_times": {
        "alias": "Summer",
        "description": "Sun, beach, friends, warm carefree seasonal joy",
        "keywords": (
            "sun beach hot waves summer sand fun friends warm bright vibes "
            "sunshine good times summer hot beach wave warm sun bright"
        ),
    },
    # ── identity & power ─────────────────────────────────────────────────────
    "confidence_flex": {
        "alias": "Flex",
        "description": "Boss swagger, dominance, power, and winning",
        "keywords": (
            "boss power win crown rich fly swag top elite leader dominant "
            "confidence flex king queen power boss win swag top dominant fly"
        ),
    },
    "wealth_luxury": {
        "alias": "Luxury",
        "description": "Money, gold, diamonds, mansions, designer lavish lifestyle",
        "keywords": (
            "money gold diamond jet mansion designer rich expensive lavish chains "
            "luxury wealth cash drip expensive gold rich diamond mansion"
        ),
    },
    "motivation_grind": {
        "alias": "Grind",
        "description": "Push hard, hustle, climb, never quit, chase dreams",
        "keywords": (
            "hustle work rise dream push never quit grind strong climb achieve "
            "motivation hustle rise grind work push dream strong climb achieve"
        ),
    },
    # ── introspection & darkness ─────────────────────────────────────────────
    "dark_introspective": {
        "alias": "Dark",
        "description": "Inner demons, shadow, existential void, fear and doubt",
        "keywords": (
            "shadow void ghost demons silence black fear lost deep dark inner "
            "struggle existential darkness shadow void ghost fear demons inner dark"
        ),
    },
    "nostalgia_memory": {
        "alias": "Nostalgia",
        "description": "Old days, faded memories, longing for the past",
        "keywords": (
            "remember old days past back then used to faded childhood miss time "
            "gone nostalgia memory remember past old faded childhood longing back"
        ),
    },
    # ── resilience & spirit ──────────────────────────────────────────────────
    "resilience_comeback": {
        "alias": "Rise",
        "description": "Survived and rose stronger, warrior healed and rebuilt",
        "keywords": (
            "survive stronger rise overcome warrior fight back won healed rebuilt "
            "resilience comeback survive rise stronger overcome warrior won healed"
        ),
    },
    "spiritual_faith": {
        "alias": "Faith",
        "description": "God, prayer, soul, divine hope, heaven and belief",
        "keywords": (
            "God pray soul light heaven faith bless sacred hope believe divine "
            "spirit prayer faith God soul hope heaven bless believe sacred light"
        ),
    },
    # ── atmosphere & lifestyle ───────────────────────────────────────────────
    "freedom_adventure": {
        "alias": "Freedom",
        "description": "Open road, wild wind, horizon, escaping and roaming free",
        "keywords": (
            "road wind sky free open escape journey wild horizon wander explore "
            "freedom adventure road wind open sky escape wild free horizon"
        ),
    },
    "chill_relaxed": {
        "alias": "Chill",
        "description": "Smooth, mellow, calm, drifting, slow easy breath",
        "keywords": (
            "smooth easy slow breathe cool drift mellow calm sunset float "
            "relaxed chill smooth easy slow calm mellow drift breathe cool"
        ),
    },
    "street_hustle": {
        "alias": "Street",
        "description": "City grind, trap, hood, concrete survival, real streets",
        "keywords": (
            "trap hood money city survive real concrete grind respect street "
            "street life hustle trap city hood concrete survive real grind"
        ),
    },
    "holiday_festive": {
        "alias": "Holiday",
        "description": "Christmas, snow, bells, family, winter celebration and cheer",
        "keywords": (
            "Christmas snow bells family winter gifts joy celebrate holiday cheer "
            "festive holiday Christmas snow winter bells family joy celebrate cheer"
        ),
    },
}

# ── genre → mood affinity multipliers ─────────────────────────────────────────
# Only non-neutral values listed; missing moods default to 1.0.
GENRE_MOOD_AFFINITY: dict[str, dict[str, float]] = {
    "Hip-Hop/Rap": {
        "confidence_flex": 1.8,
        "street_hustle": 1.9,
        "wealth_luxury": 1.7,
        "party_hype": 1.5,
        "motivation_grind": 1.4,
        "dark_introspective": 1.2,
        "anger_rebellion": 1.3,
        "desire_sensuality": 1.2,
        "romantic_love": 0.7,
        "spiritual_faith": 0.6,
        "holiday_festive": 0.4,
        "melancholy": 0.7,
        "freedom_adventure": 0.8,
    },
    "Rap": {
        "confidence_flex": 1.8,
        "street_hustle": 1.9,
        "wealth_luxury": 1.7,
        "party_hype": 1.5,
        "motivation_grind": 1.4,
        "dark_introspective": 1.2,
        "anger_rebellion": 1.3,
        "desire_sensuality": 1.2,
        "romantic_love": 0.7,
        "holiday_festive": 0.4,
    },
    "Pop": {
        "romantic_love": 1.6,
        "party_hype": 1.4,
        "summer_good_times": 1.5,
        "heartbreak": 1.5,
        "euphoria_dance": 1.3,
        "confidence_flex": 1.2,
        "resilience_comeback": 1.2,
        "street_hustle": 0.4,
        "anger_rebellion": 0.5,
        "dark_introspective": 0.6,
        "wealth_luxury": 0.7,
    },
    "Rock": {
        "anger_rebellion": 1.8,
        "freedom_adventure": 1.6,
        "motivation_grind": 1.4,
        "dark_introspective": 1.3,
        "resilience_comeback": 1.3,
        "confidence_flex": 1.2,
        "melancholy": 1.1,
        "street_hustle": 0.4,
        "wealth_luxury": 0.5,
        "holiday_festive": 0.5,
        "desire_sensuality": 0.7,
        "summer_good_times": 0.8,
    },
    "Heavy Metal": {
        "anger_rebellion": 2.0,
        "dark_introspective": 1.9,
        "freedom_adventure": 1.4,
        "motivation_grind": 1.3,
        "lonely_isolated": 1.2,
        "romantic_love": 0.5,
        "holiday_festive": 0.3,
        "summer_good_times": 0.4,
        "wealth_luxury": 0.4,
        "street_hustle": 0.4,
        "party_hype": 0.5,
    },
    "Hard Rock": {
        "anger_rebellion": 1.8,
        "dark_introspective": 1.5,
        "freedom_adventure": 1.4,
        "motivation_grind": 1.4,
        "confidence_flex": 1.3,
        "romantic_love": 0.6,
        "holiday_festive": 0.4,
        "street_hustle": 0.4,
        "wealth_luxury": 0.5,
    },
    "Alternative": {
        "dark_introspective": 1.6,
        "melancholy": 1.5,
        "lonely_isolated": 1.5,
        "freedom_adventure": 1.3,
        "nostalgia_memory": 1.3,
        "anger_rebellion": 1.2,
        "heartbreak": 1.2,
        "street_hustle": 0.3,
        "wealth_luxury": 0.3,
        "holiday_festive": 0.5,
        "party_hype": 0.6,
        "confidence_flex": 0.6,
    },
    "Indie Rock": {
        "dark_introspective": 1.5,
        "melancholy": 1.5,
        "lonely_isolated": 1.4,
        "nostalgia_memory": 1.4,
        "freedom_adventure": 1.2,
        "heartbreak": 1.2,
        "street_hustle": 0.3,
        "wealth_luxury": 0.3,
        "holiday_festive": 0.5,
        "party_hype": 0.6,
    },
    "Indie Pop": {
        "romantic_love": 1.3,
        "melancholy": 1.4,
        "nostalgia_memory": 1.3,
        "chill_relaxed": 1.3,
        "summer_good_times": 1.2,
        "street_hustle": 0.3,
        "wealth_luxury": 0.3,
        "anger_rebellion": 0.6,
    },
    "Pop Punk": {
        "anger_rebellion": 1.6,
        "heartbreak": 1.5,
        "freedom_adventure": 1.4,
        "lonely_isolated": 1.3,
        "resilience_comeback": 1.2,
        "party_hype": 1.2,
        "wealth_luxury": 0.3,
        "street_hustle": 0.4,
        "holiday_festive": 0.5,
    },
    "R&B/Soul": {
        "desire_sensuality": 1.8,
        "romantic_love": 1.7,
        "heartbreak": 1.5,
        "spiritual_faith": 1.3,
        "resilience_comeback": 1.3,
        "chill_relaxed": 1.2,
        "anger_rebellion": 0.5,
        "street_hustle": 0.6,
        "dark_introspective": 0.7,
        "holiday_festive": 0.6,
    },
    "Contemporary R&B": {
        "desire_sensuality": 1.8,
        "romantic_love": 1.7,
        "heartbreak": 1.5,
        "party_hype": 1.3,
        "chill_relaxed": 1.3,
        "confidence_flex": 1.2,
        "anger_rebellion": 0.5,
        "holiday_festive": 0.6,
    },
    "Soul": {
        "spiritual_faith": 1.6,
        "romantic_love": 1.5,
        "resilience_comeback": 1.5,
        "heartbreak": 1.4,
        "melancholy": 1.2,
        "anger_rebellion": 0.5,
        "wealth_luxury": 0.4,
        "street_hustle": 0.5,
    },
    "Funk": {
        "party_hype": 1.6,
        "desire_sensuality": 1.5,
        "confidence_flex": 1.4,
        "chill_relaxed": 1.2,
        "anger_rebellion": 0.6,
        "dark_introspective": 0.5,
        "holiday_festive": 0.6,
    },
    "Disco": {
        "party_hype": 1.9,
        "euphoria_dance": 1.7,
        "desire_sensuality": 1.5,
        "summer_good_times": 1.3,
        "dark_introspective": 0.3,
        "anger_rebellion": 0.4,
        "melancholy": 0.5,
    },
    "Country": {
        "nostalgia_memory": 1.7,
        "freedom_adventure": 1.6,
        "romantic_love": 1.5,
        "resilience_comeback": 1.4,
        "summer_good_times": 1.3,
        "heartbreak": 1.4,
        "spiritual_faith": 1.2,
        "street_hustle": 0.3,
        "wealth_luxury": 0.5,
        "dark_introspective": 0.6,
        "anger_rebellion": 0.6,
        "euphoria_dance": 0.5,
    },
    "Traditional Country": {
        "nostalgia_memory": 1.8,
        "romantic_love": 1.6,
        "freedom_adventure": 1.5,
        "heartbreak": 1.5,
        "spiritual_faith": 1.3,
        "resilience_comeback": 1.3,
        "street_hustle": 0.2,
        "wealth_luxury": 0.4,
        "anger_rebellion": 0.5,
        "euphoria_dance": 0.4,
    },
    "Contemporary Country": {
        "nostalgia_memory": 1.6,
        "summer_good_times": 1.5,
        "romantic_love": 1.5,
        "freedom_adventure": 1.4,
        "party_hype": 1.2,
        "heartbreak": 1.3,
        "street_hustle": 0.3,
        "wealth_luxury": 0.5,
        "dark_introspective": 0.6,
    },
    "Dance": {
        "euphoria_dance": 1.9,
        "party_hype": 1.8,
        "summer_good_times": 1.4,
        "chill_relaxed": 1.2,
        "desire_sensuality": 1.3,
        "dark_introspective": 0.4,
        "anger_rebellion": 0.4,
        "spiritual_faith": 0.4,
        "nostalgia_memory": 0.5,
        "street_hustle": 0.4,
    },
    "House": {
        "euphoria_dance": 2.0,
        "party_hype": 1.8,
        "desire_sensuality": 1.4,
        "summer_good_times": 1.3,
        "chill_relaxed": 1.2,
        "dark_introspective": 0.4,
        "anger_rebellion": 0.3,
        "nostalgia_memory": 0.4,
    },
    "Electronic": {
        "euphoria_dance": 1.7,
        "dark_introspective": 1.4,
        "chill_relaxed": 1.4,
        "party_hype": 1.4,
        "lonely_isolated": 1.2,
        "melancholy": 1.2,
        "anger_rebellion": 0.5,
        "street_hustle": 0.3,
        "holiday_festive": 0.4,
    },
    "Downtempo": {
        "chill_relaxed": 1.9,
        "melancholy": 1.6,
        "dark_introspective": 1.4,
        "lonely_isolated": 1.3,
        "nostalgia_memory": 1.2,
        "party_hype": 0.3,
        "anger_rebellion": 0.3,
        "holiday_festive": 0.3,
        "street_hustle": 0.3,
    },
    "Electronica": {
        "dark_introspective": 1.5,
        "chill_relaxed": 1.4,
        "melancholy": 1.3,
        "euphoria_dance": 1.3,
        "lonely_isolated": 1.2,
        "party_hype": 0.6,
        "street_hustle": 0.3,
        "holiday_festive": 0.3,
    },
    "Latin": {
        "desire_sensuality": 1.7,
        "romantic_love": 1.6,
        "party_hype": 1.5,
        "summer_good_times": 1.5,
        "freedom_adventure": 1.2,
        "dark_introspective": 0.5,
        "anger_rebellion": 0.5,
        "holiday_festive": 0.6,
        "street_hustle": 0.7,
    },
    "Latin Urban": {
        "desire_sensuality": 1.6,
        "confidence_flex": 1.5,
        "party_hype": 1.5,
        "street_hustle": 1.4,
        "romantic_love": 1.3,
        "dark_introspective": 0.6,
        "melancholy": 0.6,
    },
    "Singer/Songwriter": {
        "melancholy": 1.7,
        "nostalgia_memory": 1.6,
        "lonely_isolated": 1.5,
        "heartbreak": 1.5,
        "romantic_love": 1.4,
        "dark_introspective": 1.3,
        "freedom_adventure": 1.2,
        "party_hype": 0.3,
        "wealth_luxury": 0.2,
        "street_hustle": 0.2,
        "confidence_flex": 0.4,
        "euphoria_dance": 0.4,
    },
    "Folk-Rock": {
        "nostalgia_memory": 1.7,
        "freedom_adventure": 1.5,
        "melancholy": 1.4,
        "spiritual_faith": 1.2,
        "dark_introspective": 1.2,
        "heartbreak": 1.2,
        "party_hype": 0.4,
        "wealth_luxury": 0.2,
        "street_hustle": 0.2,
    },
    "Folk": {
        "nostalgia_memory": 1.8,
        "freedom_adventure": 1.6,
        "spiritual_faith": 1.4,
        "melancholy": 1.4,
        "resilience_comeback": 1.2,
        "heartbreak": 1.2,
        "party_hype": 0.3,
        "wealth_luxury": 0.2,
        "street_hustle": 0.2,
        "confidence_flex": 0.4,
    },
    "Jazz": {
        "chill_relaxed": 1.8,
        "desire_sensuality": 1.5,
        "melancholy": 1.4,
        "nostalgia_memory": 1.3,
        "dark_introspective": 1.2,
        "romantic_love": 1.2,
        "party_hype": 0.6,
        "anger_rebellion": 0.4,
        "street_hustle": 0.4,
        "holiday_festive": 0.7,
    },
    "Reggae": {
        "freedom_adventure": 1.8,
        "chill_relaxed": 1.7,
        "spiritual_faith": 1.6,
        "summer_good_times": 1.6,
        "romantic_love": 1.2,
        "resilience_comeback": 1.2,
        "anger_rebellion": 0.7,
        "wealth_luxury": 0.5,
        "dark_introspective": 0.6,
        "party_hype": 0.8,
    },
    "Christian & Gospel": {
        "spiritual_faith": 2.0,
        "resilience_comeback": 1.6,
        "motivation_grind": 1.3,
        "romantic_love": 0.9,
        "desire_sensuality": 0.2,
        "street_hustle": 0.2,
        "wealth_luxury": 0.3,
        "anger_rebellion": 0.3,
        "party_hype": 0.5,
        "dark_introspective": 0.7,
    },
    "Christian Rap": {
        "spiritual_faith": 1.9,
        "motivation_grind": 1.5,
        "resilience_comeback": 1.5,
        "confidence_flex": 1.2,
        "desire_sensuality": 0.2,
        "street_hustle": 0.5,
        "wealth_luxury": 0.4,
        "anger_rebellion": 0.4,
    },
    "K-Pop": {
        "party_hype": 1.6,
        "summer_good_times": 1.5,
        "romantic_love": 1.5,
        "confidence_flex": 1.4,
        "euphoria_dance": 1.4,
        "heartbreak": 1.3,
        "dark_introspective": 0.5,
        "anger_rebellion": 0.5,
        "street_hustle": 0.4,
        "spiritual_faith": 0.5,
    },
    "Holiday": {
        "holiday_festive": 2.5,
        "nostalgia_memory": 1.4,
        "romantic_love": 1.2,
        "anger_rebellion": 0.1,
        "street_hustle": 0.1,
        "desire_sensuality": 0.2,
        "dark_introspective": 0.2,
        "confidence_flex": 0.3,
        "wealth_luxury": 0.3,
    },
    "Christmas": {
        "holiday_festive": 2.5,
        "nostalgia_memory": 1.5,
        "romantic_love": 1.2,
        "anger_rebellion": 0.1,
        "street_hustle": 0.1,
    },
    "Soundtrack": {
        "dark_introspective": 1.3,
        "freedom_adventure": 1.3,
        "melancholy": 1.2,
        "motivation_grind": 1.2,
        "romantic_love": 1.1,
        "euphoria_dance": 1.1,
        "street_hustle": 0.5,
        "wealth_luxury": 0.5,
    },
    "Comedy": {
        "summer_good_times": 1.6,
        "party_hype": 1.5,
        "confidence_flex": 1.3,
        "dark_introspective": 0.2,
        "melancholy": 0.2,
        "lonely_isolated": 0.3,
        "anger_rebellion": 0.5,
        "spiritual_faith": 0.5,
    },
    "Classical": {
        "melancholy": 1.5,
        "dark_introspective": 1.4,
        "nostalgia_memory": 1.4,
        "chill_relaxed": 1.3,
        "romantic_love": 1.2,
        "party_hype": 0.3,
        "street_hustle": 0.1,
        "wealth_luxury": 0.3,
        "anger_rebellion": 0.4,
    },
}

# ── genre name normalisation ───────────────────────────────────────────────────
# Maps the extended names from the dataset to the keys above.
_GENRE_ALIASES: dict[str, str] = {
    "Hip-Hop/Rap": "Hip-Hop/Rap",
    "Hip Hop/Rap / Rap": "Rap",
    "Hip Hop/Rap / Dirty South": "Hip-Hop/Rap",
    "Hip Hop/Rap / Alternative Rap": "Alternative",
    "Hip Hop/Rap / West Coast Rap": "Hip-Hop/Rap",
    "Hip Hop/Rap / East Coast Rap": "Hip-Hop/Rap",
    "Hip Hop/Rap / Hardcore Rap": "Hip-Hop/Rap",
    "Hip Hop/Rap / Hip-Hop": "Hip-Hop/Rap",
    "Hip Hop/Rap / Gangsta Rap": "Hip-Hop/Rap",
    "Hip Hop/Rap / Underground Rap": "Hip-Hop/Rap",
    "Pop": "Pop",
    "Pop / Pop/Rock": "Pop",
    "Pop / Teen Pop": "Pop",
    "Pop / Soft Rock": "Pop",
    "Pop / K-Pop": "K-Pop",
    "Rock": "Rock",
    "Rock / Adult Alternative": "Alternative",
    "Rock / Heavy Metal": "Heavy Metal",
    "Rock / Hard Rock": "Hard Rock",
    "Rock / American Trad Rock": "Rock",
    "Rock / Arena Rock": "Rock",
    "Alternative": "Alternative",
    "Alternative / Indie Rock": "Indie Rock",
    "Alternative / Indie Pop": "Indie Pop",
    "Alternative / Pop Punk": "Pop Punk",
    "Alternative / New Wave": "Alternative",
    "Alternative / Punk": "Alternative",
    "R&B/Soul": "R&B/Soul",
    "R&B/Soul / Contemporary R&B": "Contemporary R&B",
    "R&B/Soul / Funk": "Funk",
    "R&B/Soul / Soul": "Soul",
    "R&B/Soul / Disco": "Disco",
    "Country": "Country",
    "Country / Traditional Country": "Traditional Country",
    "Country / Contemporary Country": "Contemporary Country",
    "Country / Honky Tonk": "Country",
    "Country / Urban Cowboy": "Country",
    "Dance": "Dance",
    "Dance / House": "House",
    "Electronic": "Electronic",
    "Electronic / Downtempo": "Downtempo",
    "Electronic / Electronica": "Electronica",
    "Latin": "Latin",
    "Latin / Latin Urban": "Latin Urban",
    "Latin / Pop in Spanish": "Latin",
    "Singer/Songwriter": "Singer/Songwriter",
    "Singer/Songwriter / Contemporary Singer/Songwriter": "Singer/Songwriter",
    "Singer/Songwriter / Folk-Rock": "Folk-Rock",
    "Folk": "Folk",
    "Jazz": "Jazz",
    "Reggae": "Reggae",
    "Holiday": "Holiday",
    "Holiday / Christmas": "Christmas",
    "Christian & Gospel / Christian Rap": "Christian Rap",
    "Christian & Gospel": "Christian & Gospel",
    "Soundtrack": "Soundtrack",
    "Comedy": "Comedy",
    "Classical": "Classical",
    "Classical / Electronic": "Electronic",
    "World / Asia": "K-Pop",
    "Children's Music": "Holiday",
    "Vocal": "Jazz",
}


def get_genre_affinity(genre_extended: str) -> dict[str, float]:
    """Return mood multipliers for the given genre (extended name from dataset)."""
    key = _GENRE_ALIASES.get(genre_extended, genre_extended)
    return GENRE_MOOD_AFFINITY.get(key, {})


def apply_affinity(scores: dict[str, float], genre: str) -> dict[str, float]:
    """Multiply cosine similarity scores by genre-mood affinity weights."""
    affinity = get_genre_affinity(genre)
    return {mood: score * affinity.get(mood, 1.0) for mood, score in scores.items()}


def top_mood(scores: dict[str, float]) -> str:
    return max(scores, key=lambda k: scores[k])


# ── legacy compat for retrieve.py / embedding.py ──────────────────────────────

DEFAULT_QUERY_PROMPT = ""

DOCUMENT_PROMPT = ""


def get_query_prompt(mood: str | None) -> str:
    if not mood:
        return DEFAULT_QUERY_PROMPT
    key = mood.lower().strip()
    if key in MOODS:
        return (
            f"Retrieve song lyrics that match this visual scene. "
            f"Prioritize lyrics with a {key.replace('_', ' ')} mood: {MOODS[key]['keywords']}"
        )
    return f"Retrieve song lyrics that match this visual scene with a {mood} emotional tone."


def format_document(text: str) -> str:
    return text


def format_query(user_text: str, mood: str | None = None) -> str:
    return f""
