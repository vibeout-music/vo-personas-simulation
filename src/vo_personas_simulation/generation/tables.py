"""Reference data used by the persona generator."""

# weight: share of the population; urban: mean urbanicity; temp: annual mean
# and seasonal amplitude in C; south: southern hemisphere; wet: base
# probability of a precipitation condition; second: likely second languages;
# premium: share of paying subscribers; genres: locally popular genres;
# holidays: fixed-date public holidays (MM-DD).
COUNTRIES = {
    "US": dict(weight=14, tz=["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles"],
               lang="en", second={"es": 0.25, "fr": 0.04, "zh": 0.03}, urban=0.8, temp=(13, 11), south=False, wet=0.25,
               premium=0.55, genres=["hip_hop", "pop", "country", "rnb", "rock"],
               holidays=["01-01", "07-04", "11-11", "12-25"]),
    "MX": dict(weight=8, tz=["America/Mexico_City", "America/Tijuana", "America/Cancun"],
               lang="es", second={"en": 0.35}, urban=0.8, temp=(21, 5), south=False, wet=0.25,
               premium=0.3, genres=["regional_mexican", "reggaeton", "latin_pop", "cumbia"],
               holidays=["01-01", "09-16", "11-20", "12-25"]),
    "CO": dict(weight=5, tz=["America/Bogota"],
               lang="es", second={"en": 0.3}, urban=0.8, temp=(22, 1), south=False, wet=0.4,
               premium=0.25, genres=["reggaeton", "salsa", "cumbia", "latin_pop", "vallenato"],
               holidays=["01-01", "07-20", "08-07", "12-25"]),
    "AR": dict(weight=4, tz=["America/Argentina/Buenos_Aires"],
               lang="es", second={"en": 0.35, "it": 0.05}, urban=0.9, temp=(17, 7), south=True, wet=0.25,
               premium=0.25, genres=["cumbia", "rock", "trap", "latin_pop", "tango"],
               holidays=["01-01", "05-25", "07-09", "12-25"]),
    "BR": dict(weight=9, tz=["America/Sao_Paulo", "America/Manaus", "America/Recife"],
               lang="pt", second={"en": 0.3, "es": 0.15}, urban=0.85, temp=(23, 4), south=True, wet=0.35,
               premium=0.3, genres=["sertanejo", "funk", "mpb", "pop"],
               holidays=["01-01", "04-21", "09-07", "11-15", "12-25"]),
    "ES": dict(weight=8, tz=["Europe/Madrid", "Atlantic/Canary"],
               lang="es", second={"en": 0.55, "ca": 0.2, "fr": 0.1}, urban=0.8, temp=(16, 8), south=False, wet=0.18,
               premium=0.45, genres=["reggaeton", "latin_pop", "flamenco", "indie", "pop"],
               holidays=["01-01", "01-06", "08-15", "10-12", "12-08", "12-25"]),
    "GB": dict(weight=6, tz=["Europe/London"],
               lang="en", second={"fr": 0.15, "es": 0.1, "pl": 0.03}, urban=0.84, temp=(11, 6), south=False, wet=0.45,
               premium=0.55, genres=["pop", "indie", "rock", "drum_and_bass", "grime"],
               holidays=["01-01", "12-25", "12-26"]),
    "FR": dict(weight=5, tz=["Europe/Paris"],
               lang="fr", second={"en": 0.5, "es": 0.15, "ar": 0.05}, urban=0.8, temp=(13, 8), south=False, wet=0.3,
               premium=0.45, genres=["french_rap", "pop", "electronic", "chanson"],
               holidays=["01-01", "05-01", "07-14", "08-15", "11-11", "12-25"]),
    "DE": dict(weight=6, tz=["Europe/Berlin"],
               lang="de", second={"en": 0.65, "tr": 0.05, "fr": 0.1}, urban=0.77, temp=(10, 9), south=False, wet=0.35,
               premium=0.5, genres=["techno", "german_rap", "schlager", "rock", "pop"],
               holidays=["01-01", "05-01", "10-03", "12-25", "12-26"]),
    "IT": dict(weight=4, tz=["Europe/Rome"],
               lang="it", second={"en": 0.45, "fr": 0.1}, urban=0.71, temp=(15, 9), south=False, wet=0.25,
               premium=0.4, genres=["italian_pop", "trap", "opera", "pop"],
               holidays=["01-01", "04-25", "06-02", "08-15", "12-25"]),
    "JP": dict(weight=6, tz=["Asia/Tokyo"],
               lang="ja", second={"en": 0.3}, urban=0.92, temp=(16, 10), south=False, wet=0.35,
               premium=0.35, genres=["jpop", "anime", "rock", "city_pop"],
               holidays=["01-01", "05-03", "05-05", "11-03"]),
    "KR": dict(weight=4, tz=["Asia/Seoul"],
               lang="ko", second={"en": 0.4, "ja": 0.05}, urban=0.82, temp=(13, 14), south=False, wet=0.3,
               premium=0.45, genres=["kpop", "khiphop", "ballad", "rnb"],
               holidays=["01-01", "03-01", "08-15", "10-03", "10-09"]),
    "IN": dict(weight=8, tz=["Asia/Kolkata"],
               lang="hi", second={"en": 0.6, "bn": 0.1, "ta": 0.08}, urban=0.36, temp=(26, 6), south=False, wet=0.3,
               premium=0.12, genres=["bollywood", "punjabi", "indie", "devotional"],
               holidays=["01-26", "08-15", "10-02"]),
    "NG": dict(weight=4, tz=["Africa/Lagos"],
               lang="en", second={"yo": 0.3, "ha": 0.25, "ig": 0.2}, urban=0.53, temp=(27, 2), south=False, wet=0.35,
               premium=0.1, genres=["afrobeats", "gospel", "highlife", "hip_hop"],
               holidays=["01-01", "06-12", "10-01", "12-25"]),
    "AU": dict(weight=3, tz=["Australia/Sydney", "Australia/Melbourne", "Australia/Perth", "Australia/Brisbane"],
               lang="en", second={"zh": 0.05, "it": 0.03, "es": 0.04}, urban=0.86, temp=(18, 6), south=True, wet=0.22,
               premium=0.55, genres=["pop", "indie", "rock", "electronic"],
               holidays=["01-01", "01-26", "04-25", "12-25"]),
}

# (label, min_age, max_age)
LIFE_STAGES = [
    ("teenager", 13, 17),
    ("young_adult", 18, 24),
    ("early_career", 25, 34),
    ("established_adult", 35, 49),
    ("midlife", 50, 64),
    ("senior", 65, 120),
]

# Education is a trajectory: a level can only be completed from a minimum
# age, and a person can only be enrolled in the level right after the highest
# one completed.
EDUCATION_RANK = {"primary": 0, "secondary": 1, "vocational": 2, "bachelor": 3, "master": 4, "doctorate": 5}
EDUCATION_MIN_COMPLETION_AGE = {"primary": 11, "secondary": 16, "vocational": 18, "bachelor": 21, "master": 23, "doctorate": 26}
EDUCATION_NEXT = {
    "primary": ["secondary"],
    "secondary": ["vocational", "bachelor"],
    "vocational": ["bachelor"],
    "bachelor": ["master"],
    "master": ["doctorate"],
    "doctorate": [],
}

# ages: allowed age range; edu: minimum completed education rank; env: work
# environments; listen: mean ability to listen while working; load/stress:
# means; income: mean relative income; loc: context location while working;
# shifts: schedule types; music: whether music at work is usually allowed;
# part_time: suitable as a student job; share: relative prevalence.
OCCUPATIONS = {
    "software_engineer": dict(share=2, ages=(20, 70), edu=2, env=["office", "remote_home", "hybrid"], listen=0.75, load=0.8, stress=0.5, income=0.72, loc="office", shifts=["day", "flexible"], music=True),
    "designer": dict(share=1, ages=(20, 70), edu=2, env=["office", "remote_home", "hybrid"], listen=0.8, load=0.6, stress=0.45, income=0.55, loc="office", shifts=["day", "flexible"], music=True),
    "nurse": dict(share=2, ages=(21, 67), edu=3, env=["hospital"], listen=0.1, load=0.7, stress=0.7, income=0.5, loc="hospital", shifts=["day", "night", "rotating"], music=False),
    "doctor": dict(share=0.8, ages=(25, 72), edu=4, env=["hospital", "clinic"], listen=0.1, load=0.85, stress=0.75, income=0.85, loc="hospital", shifts=["day", "rotating"], music=False),
    "teacher": dict(share=2, ages=(22, 67), edu=3, env=["school"], listen=0.1, load=0.65, stress=0.6, income=0.45, loc="school", shifts=["school_hours"], music=False),
    "researcher": dict(share=0.7, ages=(23, 72), edu=4, env=["office", "lab", "hybrid"], listen=0.55, load=0.85, stress=0.5, income=0.55, loc="office", shifts=["day", "flexible"], music=True),
    "accountant": dict(share=1.5, ages=(21, 67), edu=3, env=["office", "hybrid"], listen=0.5, load=0.7, stress=0.5, income=0.6, loc="office", shifts=["day"], music=True),
    "marketing_specialist": dict(share=1.5, ages=(21, 67), edu=3, env=["office", "hybrid", "remote_home"], listen=0.6, load=0.6, stress=0.55, income=0.55, loc="office", shifts=["day", "flexible"], music=True),
    "office_administrator": dict(share=3, ages=(18, 67), edu=1, env=["office"], listen=0.4, load=0.45, stress=0.45, income=0.4, loc="office", shifts=["day"], music=True),
    "retail_worker": dict(share=3, ages=(16, 67), edu=0, env=["store"], listen=0.15, load=0.35, stress=0.5, income=0.28, loc="store", shifts=["day", "evening", "rotating"], music=False, part_time=True),
    "hospitality_worker": dict(share=2.5, ages=(16, 67), edu=0, env=["restaurant", "hotel"], listen=0.2, load=0.4, stress=0.55, income=0.28, loc="restaurant", shifts=["evening", "rotating"], music=False, part_time=True),
    "chef": dict(share=1, ages=(18, 67), edu=1, env=["restaurant"], listen=0.35, load=0.55, stress=0.65, income=0.38, loc="restaurant", shifts=["evening", "rotating"], music=True),
    "warehouse_worker": dict(share=2, ages=(18, 65), edu=0, env=["warehouse"], listen=0.35, load=0.3, stress=0.5, income=0.32, loc="warehouse", shifts=["day", "night", "rotating"], music=True, part_time=True),
    "construction_worker": dict(share=2, ages=(18, 65), edu=0, env=["construction_site"], listen=0.3, load=0.35, stress=0.5, income=0.38, loc="construction_site", shifts=["day"], music=True),
    "electrician": dict(share=1, ages=(19, 67), edu=2, env=["field"], listen=0.35, load=0.5, stress=0.45, income=0.48, loc="field", shifts=["day"], music=True),
    "driver": dict(share=1.5, ages=(21, 70), edu=0, env=["vehicle"], listen=0.8, load=0.4, stress=0.5, income=0.35, loc="car", shifts=["day", "night", "rotating"], music=True),
    "delivery_rider": dict(share=1, ages=(18, 60), edu=0, env=["street"], listen=0.5, load=0.35, stress=0.55, income=0.25, loc="street", shifts=["evening", "flexible"], music=True, part_time=True),
    "tutor": dict(share=0.5, ages=(17, 70), edu=1, env=["remote_home", "home_visits"], listen=0.1, load=0.55, stress=0.35, income=0.3, loc="home", shifts=["evening", "flexible"], music=False, part_time=True),
    "freelance_creative": dict(share=0.8, ages=(18, 80), edu=1, env=["remote_home", "studio"], listen=0.85, load=0.55, stress=0.5, income=0.4, loc="home", shifts=["flexible"], music=True),
    "musician": dict(share=0.3, ages=(16, 80), edu=0, env=["studio", "remote_home"], listen=0.6, load=0.55, stress=0.5, income=0.35, loc="studio", shifts=["evening", "flexible"], music=True, part_time=True),
    "small_business_owner": dict(share=1.2, ages=(22, 80), edu=1, env=["store", "office"], listen=0.4, load=0.65, stress=0.65, income=0.55, loc="store", shifts=["day", "flexible"], music=True),
}

NON_WORKING = {
    "student": dict(env="school", loc="school", income=0.45),
    "unemployed": dict(env="home", loc="home", income=0.15),
    "retired": dict(env="home", loc="home", income=0.45),
    "homemaker": dict(env="home", loc="home", income=0.35),
}

# schedule type -> (start hour, end hour) of the usual working window.
SHIFT_HOURS = {
    "day": [(8, 16), (9, 17), (9, 18)],
    "school_hours": [(8, 15), (8, 14), (9, 15)],
    "evening": [(15, 23), (16, 24), (14, 22)],
    "night": [(22, 6), (23, 7)],
    "flexible": [(10, 18), (11, 19), (9, 15)],
}

SENIORITY = [(0, 2, "Junior"), (3, 9, None), (10, 19, "Senior"), (20, 200, "Lead")]

GENRES = [
    "pop", "rock", "indie", "hip_hop", "rnb", "electronic", "techno", "house", "reggaeton", "latin_pop",
    "salsa", "cumbia", "regional_mexican", "kpop", "jpop", "afrobeats", "funk", "soul", "jazz", "blues",
    "classical", "soundtrack", "ambient", "lofi", "metal", "punk", "folk", "country", "singer_songwriter",
    "flamenco", "mpb", "bollywood", "reggae", "trap", "drum_and_bass", "gospel", "opera", "world",
    "sertanejo", "vallenato", "tango", "grime", "french_rap", "chanson", "german_rap", "schlager",
    "italian_pop", "anime", "city_pop", "khiphop", "ballad", "punjabi", "devotional", "highlife",
]

# Genre -> (year it reached a global audience, {country: earlier local year}).
# Approximate; used so that nobody grows up with a genre that had not reached
# them yet, and so that artists are not older than their genre.
GENRE_ORIGIN = {
    "pop": (1955, {}), "rock": (1956, {}), "indie": (1985, {}), "hip_hop": (1995, {"US": 1979}),
    "rnb": (1960, {}), "electronic": (1980, {}), "techno": (1990, {"US": 1986, "DE": 1988}),
    "house": (1990, {"US": 1985, "GB": 1987}), "reggaeton": (2004, {"MX": 1998, "CO": 1998, "AR": 2000, "ES": 2000, "US": 2000}),
    "latin_pop": (1990, {"MX": 1970, "CO": 1970, "AR": 1970, "ES": 1970}), "salsa": (1985, {"CO": 1970, "MX": 1975, "US": 1968}),
    "cumbia": (1995, {"CO": 1950, "MX": 1970, "AR": 1990}), "regional_mexican": (2020, {"MX": 1950, "US": 1990}),
    "kpop": (2012, {"KR": 1992, "JP": 2005}), "jpop": (2010, {"JP": 1990, "KR": 2000}), "afrobeats": (2017, {"NG": 2005, "GB": 2012}),
    "funk": (1970, {}), "soul": (1960, {}), "jazz": (1920, {}), "blues": (1920, {}), "classical": (1700, {}),
    "soundtrack": (1950, {}), "ambient": (1978, {}), "lofi": (2016, {}), "metal": (1972, {}), "punk": (1977, {}),
    "folk": (1950, {}), "country": (1990, {"US": 1940, "AU": 1970}), "singer_songwriter": (1965, {}),
    "flamenco": (1990, {"ES": 1950}), "mpb": (2000, {"BR": 1965}), "bollywood": (2005, {"IN": 1950}), "reggae": (1975, {}),
    "trap": (2015, {"US": 2005}), "drum_and_bass": (1998, {"GB": 1993}), "gospel": (1960, {"US": 1940, "NG": 1970}),
    "opera": (1700, {}), "world": (1985, {}), "sertanejo": (2015, {"BR": 1980}), "vallenato": (2000, {"CO": 1960}),
    "tango": (1930, {"AR": 1920}), "grime": (2015, {"GB": 2003}), "french_rap": (2000, {"FR": 1990}),
    "chanson": (1950, {"FR": 1930}), "german_rap": (2005, {"DE": 1995}), "schlager": (1990, {"DE": 1960}),
    "italian_pop": (1990, {"IT": 1960}), "anime": (2008, {"JP": 1980}), "city_pop": (2018, {"JP": 1978}),
    "khiphop": (2012, {"KR": 2000}), "ballad": (2010, {"KR": 1985}), "punjabi": (2018, {"IN": 1990}),
    "devotional": (2000, {"IN": 1950}), "highlife": (2000, {"NG": 1950}),
}


def genre_arrival(genre: str, country: str) -> int:
    """Year a genre became part of the musical landscape in a country."""
    global_year, local = GENRE_ORIGIN[genre]
    return local.get(country, global_year)


def genre_birth(genre: str) -> int:
    """Earliest year the genre existed anywhere."""
    global_year, local = GENRE_ORIGIN[genre]
    return min([global_year, *local.values()])


# Genres with a broad international audience.
MAINSTREAM_GENRES = {
    "pop", "rock", "hip_hop", "rnb", "electronic", "soul", "jazz", "classical", "soundtrack", "metal", "reggae", "funk",
    "house", "indie", "singer_songwriter", "folk", "blues", "punk", "techno", "trap", "lofi", "ambient", "latin_pop",
    "reggaeton", "kpop", "afrobeats",
}


def genre_reach(genre: str, country: str, language: str) -> float:
    """How present a genre is in a country's everyday listening (relative weight)."""
    _, local = GENRE_ORIGIN[genre]
    if country in local or country in COUNTRIES and genre in COUNTRIES[country]["genres"]:
        return 4.0
    if GENRE_LANGUAGE.get(genre) == language:
        return 1.5  # e.g. Latin genres in Spain, French rap in other French-speaking markets
    if genre in MAINSTREAM_GENRES:
        return 1.5
    if local:
        return 0.2  # another country's regional genre: rare, but some people find it
    return 0.6


# Genre -> lyric language when it is strongly tied to one.
GENRE_LANGUAGE = {
    "reggaeton": "es", "latin_pop": "es", "salsa": "es", "cumbia": "es", "regional_mexican": "es",
    "flamenco": "es", "vallenato": "es", "tango": "es", "kpop": "ko", "khiphop": "ko", "ballad": "ko",
    "jpop": "ja", "anime": "ja", "city_pop": "ja", "mpb": "pt", "sertanejo": "pt", "funk": "pt",
    "bollywood": "hi", "punjabi": "pa", "french_rap": "fr", "chanson": "fr", "german_rap": "de",
    "schlager": "de", "italian_pop": "it", "opera": "it", "grime": "en", "country": "en",
}

INSTRUMENTAL_GENRES = {"classical", "ambient", "lofi", "techno", "house", "soundtrack", "drum_and_bass", "electronic", "jazz"}

# Genre -> weights over the MUSIC model dimensions (Rentfrow et al.).
GENRE_STYLE = {
    "mellow": {"rnb", "soul", "ambient", "lofi", "ballad", "singer_songwriter", "city_pop", "chanson", "soundtrack"},
    "unpretentious": {"country", "folk", "pop", "schlager", "sertanejo", "regional_mexican", "vallenato", "gospel", "devotional", "italian_pop"},
    "sophisticated": {"jazz", "classical", "opera", "blues", "world", "tango", "flamenco", "mpb"},
    "intense": {"rock", "metal", "punk", "drum_and_bass", "grime", "techno"},
    "contemporary": {"hip_hop", "trap", "reggaeton", "afrobeats", "kpop", "jpop", "latin_pop", "house", "electronic",
                     "funk", "french_rap", "german_rap", "khiphop", "punjabi", "bollywood", "highlife", "anime", "reggae",
                     "indie", "salsa", "cumbia"},
}

# Genre -> typical tempo in BPM.
GENRE_TEMPO = {
    "ambient": 70, "lofi": 80, "classical": 90, "ballad": 72, "rnb": 90, "soul": 95, "hip_hop": 92, "trap": 140,
    "reggaeton": 95, "house": 124, "techno": 132, "drum_and_bass": 174, "metal": 150, "punk": 170, "rock": 120,
    "pop": 115, "kpop": 120, "electronic": 125, "jazz": 110, "salsa": 180, "cumbia": 95, "afrobeats": 105,
}

ARCHETYPES = [
    "emotion_regulator", "mood_matcher", "music_explorer", "loyal_fan", "routine_listener",
    "socially_expressive", "trend_follower", "playlist_curator", "passive_listener", "privacy_conscious",
]

# Archetype -> mean shifts applied to music-behaviour traits.
ARCHETYPE_BIAS = {
    "emotion_regulator": {"emotion_regulation": 0.3, "emotion_processing": 0.3, "musical_sensitivity": 0.2},
    "mood_matcher": {"emotion_processing": 0.25, "musical_sensitivity": 0.2, "skip_rate": 0.1, "iso": 0.3},
    "music_explorer": {"novelty": 0.35, "taste_breadth": 0.35, "popularity": -0.3, "habituation": 0.15},
    "loyal_fan": {"repeat": 0.3, "obsessive_replay": 0.3, "novelty": -0.25, "identity": 0.25, "loyalty": 0.35},
    "routine_listener": {"background": 0.3, "daily_listening": 0.2, "novelty": -0.15, "skip_rate": -0.1, "routine": 0.3},
    "socially_expressive": {"social": 0.35, "identity": 0.2, "like_rate": 0.15, "sharing": 0.35},
    "trend_follower": {"popularity": 0.35, "novelty": 0.1, "social": 0.15, "trend": 0.4},
    "playlist_curator": {"identity": 0.3, "like_rate": 0.25, "taste_breadth": 0.2, "sophistication": 0.15, "active": 0.35},
    "passive_listener": {"background": 0.3, "like_rate": -0.2, "skip_rate": -0.15, "identity": -0.25, "active": -0.35, "autoplay": 0.3},
    "privacy_conscious": {"social": -0.35, "like_rate": -0.1, "sharing": -0.4},
}

AMBITIONS = ["career", "family", "health", "financial_security", "creativity", "education", "travel", "community", "spirituality", "recognition"]
CONCERNS = ["relationships", "health", "meaning", "money", "career", "loneliness", "appearance", "family", "future", "failure"]
GOALS_BY_AMBITION = {
    "career": ["get_promoted", "change_jobs", "start_a_business"],
    "family": ["spend_more_time_with_family", "start_a_family"],
    "health": ["exercise_regularly", "sleep_better", "eat_better"],
    "financial_security": ["save_money", "pay_off_debt", "buy_a_home"],
    "creativity": ["finish_a_creative_project", "learn_an_instrument"],
    "education": ["finish_degree", "learn_a_language", "pass_exams"],
    "travel": ["travel_abroad", "move_to_another_city"],
    "community": ["volunteer", "make_new_friends"],
    "spirituality": ["practice_mindfulness", "find_purpose"],
    "recognition": ["grow_an_audience", "win_a_competition"],
}

THEMES = ["love", "heartbreak", "empowerment", "party", "social_issues", "nostalgia", "spirituality", "struggle", "introspection"]

EXERCISE_TYPES = ["gym", "running", "cycling", "yoga", "team_sports", "swimming", "walking", "dance", "martial_arts"]

# activity -> locations, devices, audio outputs. None = decided elsewhere.
ACTIVITIES = {
    "sleeping": dict(loc=["home"], dev=["phone"], out=["none"]),
    "waking_up": dict(loc=["home"], dev=["phone", "smart_speaker"], out=["phone_speaker", "smart_speaker", "earbuds"]),
    "commuting": dict(loc=None, dev=["phone", "wearable"], out=None),
    "working": dict(loc=None, dev=None, out=None),
    "studying": dict(loc=["home", "library", "school"], dev=["laptop", "phone", "tablet"], out=["headphones", "earbuds"]),
    "exercising": dict(loc=["gym", "outdoors", "home"], dev=["phone", "wearable"], out=["earbuds", "headphones"]),
    "cooking": dict(loc=["home"], dev=["phone", "smart_speaker"], out=["smart_speaker", "phone_speaker", "home_speakers"]),
    "household_chores": dict(loc=["home"], dev=["phone", "smart_speaker"], out=["smart_speaker", "earbuds", "home_speakers"]),
    "eating": dict(loc=["home", "restaurant"], dev=["phone"], out=["phone_speaker", "home_speakers", "none"]),
    "running_errands": dict(loc=["store", "street"], dev=["phone"], out=["earbuds", "none"]),
    "socializing": dict(loc=["friend_home", "bar", "restaurant", "home"], dev=["phone"], out=["venue_speakers", "home_speakers", "none"]),
    "relaxing": dict(loc=["home", "home", "home", "outdoors"], dev=["phone", "laptop", "tv", "tablet"], out=["headphones", "home_speakers", "earbuds"]),
    "gaming": dict(loc=["home"], dev=["console", "desktop"], out=["headphones", "home_speakers"]),
    "winding_down": dict(loc=["home"], dev=["phone", "smart_speaker"], out=["headphones", "smart_speaker", "earbuds"]),
    "childcare": dict(loc=["home", "outdoors"], dev=["phone", "smart_speaker"], out=["smart_speaker", "phone_speaker", "none"]),
}

# How suitable an activity is for listening and which function it serves.
ACTIVITY_LISTENING = {
    "sleeping": (0.03, "relaxation"), "waking_up": (0.45, "background"), "commuting": (0.85, "killing_time"),
    "working": (0.5, "focus"), "studying": (0.6, "focus"), "exercising": (0.9, "exercise"),
    "cooking": (0.6, "background"), "household_chores": (0.65, "background"), "eating": (0.3, "background"),
    "running_errands": (0.45, "killing_time"), "socializing": (0.35, "social_connection"),
    "relaxing": (0.6, "relaxation"), "gaming": (0.35, "background"), "winding_down": (0.55, "relaxation"),
    "childcare": (0.3, "background"),
}

WEATHER_CONDITIONS = ["clear", "partly_cloudy", "cloudy", "fog", "drizzle", "rain", "storm", "snow"]
PRECIPITATING = {"drizzle", "rain", "storm", "snow"}

# Life events: min age, max age, valence impact, intensity, and a predicate
# name checked by the life section (see sections/life.py).
LIFE_EVENTS = {
    "exam_period": dict(ages=(13, 60), valence=-0.3, requires="enrolled"),
    "started_new_school_year": dict(ages=(13, 30), valence=0.1, requires="enrolled"),
    "graduation_approaching": dict(ages=(17, 40), valence=0.4, requires="enrolled"),
    "first_love": dict(ages=(13, 22), valence=0.6, requires="dating"),
    "breakup": dict(ages=(14, 80), valence=-0.7, requires="single"),
    "new_relationship": dict(ages=(15, 85), valence=0.6, requires="dating"),
    "wedding_planning": dict(ages=(20, 70), valence=0.4, requires="engaged_possible"),
    "divorce_process": dict(ages=(22, 85), valence=-0.7, requires="divorced"),
    "new_baby": dict(ages=(18, 55), valence=0.5, requires="baby"),
    "new_job": dict(ages=(16, 70), valence=0.4, requires="employed"),
    "promotion": dict(ages=(22, 70), valence=0.5, requires="employed"),
    "job_loss": dict(ages=(18, 67), valence=-0.7, requires="unemployed"),
    "work_overload": dict(ages=(18, 70), valence=-0.4, requires="employed"),
    "recent_retirement": dict(ages=(55, 75), valence=0.1, requires="retired"),
    "moving_house": dict(ages=(18, 85), valence=0.1, requires=None),
    "moved_out_of_parents_home": dict(ages=(18, 30), valence=0.3, requires="not_with_parents"),
    "bereavement": dict(ages=(13, 100), valence=-0.8, requires=None),
    "illness": dict(ages=(13, 100), valence=-0.5, requires=None),
    "financial_trouble": dict(ages=(18, 100), valence=-0.5, requires="financial_pressure"),
    "family_conflict": dict(ages=(13, 100), valence=-0.4, requires=None),
    "started_new_hobby": dict(ages=(13, 100), valence=0.4, requires=None),
}

# Daily events: valence, arousal, description, requirement.
DAILY_EVENTS = {
    "good_news": (0.5, 0.3, "Received some unexpectedly good news.", None),
    "compliment": (0.4, 0.2, "Someone paid them a sincere compliment.", None),
    "argument_with_partner": (-0.5, 0.5, "Had an argument with their partner.", "partner"),
    "argument_with_family": (-0.4, 0.4, "Had a tense moment with family.", "family"),
    "work_deadline": (-0.3, 0.5, "Facing a deadline at work.", "employed"),
    "praised_at_work": (0.5, 0.3, "Their work was praised.", "employed"),
    "exam_today": (-0.3, 0.6, "Has an exam today.", "enrolled"),
    "good_grade": (0.5, 0.3, "Got a good grade.", "enrolled"),
    "bad_night_sleep": (-0.3, -0.4, "Slept badly last night.", None),
    "traffic_jam": (-0.3, 0.3, "Stuck in heavy traffic.", "car"),
    "missed_transport": (-0.3, 0.4, "Missed their bus or train.", "transit"),
    "plans_cancelled": (-0.3, -0.1, "Plans with friends were cancelled.", None),
    "caught_up_with_friend": (0.5, 0.2, "Caught up with an old friend.", None),
    "kid_was_sick": (-0.3, 0.3, "One of their children was unwell.", "young_child"),
    "unexpected_expense": (-0.4, 0.3, "Had an unexpected expense.", "adult"),
    "finished_a_task": (0.3, 0.1, "Finished something they had been putting off.", None),
    "great_workout": (0.4, 0.4, "Had a great workout.", "exerciser"),
}

SYLLABLES = ["ka", "lo", "mi", "ra", "ne", "so", "ti", "va", "du", "el", "an", "ri", "to", "sa", "le", "mo",
             "ju", "ha", "ni", "ze", "po", "ya", "ke", "li", "ma", "ro", "si", "ta", "no", "be", "ca", "di"]


# --- Music catalogue ----------------------------------------------------------

# Our genre -> Spotify genre terms used to search the catalogue.
SPOTIFY_QUERIES = {
    "pop": ["pop", "dance pop"], "rock": ["rock", "classic rock"], "indie": ["indie", "indie rock"],
    "hip_hop": ["hip hop", "rap"], "rnb": ["r&b"], "electronic": ["electronic", "edm"], "techno": ["techno"],
    "house": ["house"], "reggaeton": ["reggaeton"], "latin_pop": ["latin pop"], "salsa": ["salsa"],
    "cumbia": ["cumbia"], "regional_mexican": ["regional mexican", "corridos"], "kpop": ["k-pop"], "jpop": ["j-pop"],
    "afrobeats": ["afrobeats"], "funk": ["funk"], "soul": ["soul"], "jazz": ["jazz"], "blues": ["blues"],
    "classical": ["classical"], "soundtrack": ["soundtrack"], "ambient": ["ambient"], "lofi": ["lo-fi"],
    "metal": ["metal"], "punk": ["punk"], "folk": ["folk"], "country": ["country"],
    "singer_songwriter": ["singer-songwriter"], "flamenco": ["flamenco"], "mpb": ["mpb"],
    "bollywood": ["bollywood", "filmi"], "reggae": ["reggae"], "trap": ["trap"], "drum_and_bass": ["drum and bass"],
    "gospel": ["gospel"], "opera": ["opera"], "world": ["world"], "sertanejo": ["sertanejo"],
    "vallenato": ["vallenato"], "tango": ["tango"], "grime": ["grime"], "french_rap": ["french hip hop"],
    "chanson": ["chanson"], "german_rap": ["german hip hop"], "schlager": ["schlager"], "italian_pop": ["italian pop"],
    "anime": ["anime"], "city_pop": ["city pop"], "khiphop": ["k-rap"], "ballad": ["k-ballad"],
    "punjabi": ["punjabi pop", "bhangra"], "devotional": ["devotional"], "highlife": ["highlife"],
}

# Our genre -> typical (energy, valence, danceability, acousticness, instrumentalness).
# Spotify no longer serves audio features to new apps, so track features are
# estimated from these genre means (see catalog/features.py).
GENRE_AUDIO = {
    "pop": (0.65, 0.6, 0.68, 0.2, 0.02), "rock": (0.75, 0.5, 0.5, 0.15, 0.05), "indie": (0.6, 0.45, 0.55, 0.3, 0.1),
    "hip_hop": (0.65, 0.5, 0.75, 0.12, 0.02), "rnb": (0.55, 0.5, 0.68, 0.25, 0.02), "electronic": (0.75, 0.45, 0.65, 0.08, 0.45),
    "techno": (0.85, 0.3, 0.7, 0.03, 0.8), "house": (0.8, 0.55, 0.78, 0.05, 0.5), "reggaeton": (0.78, 0.65, 0.8, 0.12, 0.01),
    "latin_pop": (0.7, 0.65, 0.72, 0.2, 0.01), "salsa": (0.75, 0.8, 0.72, 0.3, 0.05), "cumbia": (0.72, 0.8, 0.75, 0.3, 0.05),
    "regional_mexican": (0.6, 0.6, 0.62, 0.4, 0.02), "kpop": (0.78, 0.6, 0.7, 0.1, 0.01), "jpop": (0.75, 0.6, 0.6, 0.15, 0.02),
    "afrobeats": (0.7, 0.7, 0.8, 0.2, 0.02), "funk": (0.75, 0.7, 0.78, 0.15, 0.1), "soul": (0.5, 0.6, 0.6, 0.45, 0.03),
    "jazz": (0.4, 0.55, 0.55, 0.7, 0.5), "blues": (0.5, 0.45, 0.52, 0.55, 0.1), "classical": (0.2, 0.35, 0.3, 0.92, 0.9),
    "soundtrack": (0.35, 0.3, 0.3, 0.6, 0.8), "ambient": (0.15, 0.3, 0.25, 0.75, 0.9), "lofi": (0.3, 0.45, 0.65, 0.6, 0.85),
    "metal": (0.92, 0.3, 0.4, 0.03, 0.2), "punk": (0.9, 0.5, 0.45, 0.05, 0.03), "folk": (0.35, 0.5, 0.5, 0.8, 0.05),
    "country": (0.6, 0.6, 0.58, 0.4, 0.01), "singer_songwriter": (0.35, 0.4, 0.5, 0.7, 0.02), "flamenco": (0.6, 0.5, 0.55, 0.75, 0.1),
    "mpb": (0.45, 0.6, 0.6, 0.65, 0.05), "bollywood": (0.65, 0.6, 0.65, 0.35, 0.02), "reggae": (0.55, 0.75, 0.75, 0.3, 0.05),
    "trap": (0.68, 0.4, 0.75, 0.1, 0.02), "drum_and_bass": (0.9, 0.4, 0.55, 0.03, 0.5), "gospel": (0.55, 0.65, 0.5, 0.45, 0.02),
    "opera": (0.35, 0.35, 0.25, 0.9, 0.1), "world": (0.55, 0.6, 0.6, 0.55, 0.2), "sertanejo": (0.65, 0.65, 0.62, 0.35, 0.01),
    "vallenato": (0.7, 0.7, 0.7, 0.35, 0.02), "tango": (0.45, 0.4, 0.55, 0.7, 0.35), "grime": (0.8, 0.4, 0.72, 0.05, 0.02),
    "french_rap": (0.65, 0.45, 0.72, 0.12, 0.02), "chanson": (0.35, 0.45, 0.5, 0.75, 0.03), "german_rap": (0.7, 0.45, 0.72, 0.1, 0.02),
    "schlager": (0.7, 0.75, 0.65, 0.25, 0.01), "italian_pop": (0.62, 0.55, 0.6, 0.3, 0.01), "anime": (0.82, 0.55, 0.55, 0.1, 0.02),
    "city_pop": (0.6, 0.7, 0.7, 0.3, 0.05), "khiphop": (0.68, 0.5, 0.75, 0.1, 0.02), "ballad": (0.35, 0.3, 0.45, 0.55, 0.02),
    "punjabi": (0.8, 0.7, 0.78, 0.15, 0.02), "devotional": (0.35, 0.5, 0.45, 0.6, 0.1), "highlife": (0.65, 0.8, 0.75, 0.35, 0.05),
}
