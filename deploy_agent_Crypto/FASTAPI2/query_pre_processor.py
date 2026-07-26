import unicodedata
import regex as re
from langdetect import detect, DetectorFactory

# Make langdetect deterministic
DetectorFactory.seed = 0

# Arabic diacritics pattern
ARABIC_DIACRITICS = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')
TATWEEL = "\u0640"

# Emoji + symbol stripping
EMOJI_PATTERN = re.compile(
    r"[\p{So}\p{Sk}\p{Sm}\p{Cn}\p{Cf}\U0001F300-\U0001F6FF"
    r"\U0001F900-\U0001F9FF\U0001FA70-\U0001FAFF]+", 
    flags=re.UNICODE
)

def normalize_arabic(text: str) -> str:
    """Remove diacritics and tatweel"""
    text = ARABIC_DIACRITICS.sub("", text)
    text = text.replace(TATWEEL, "")
    return text

def normalize_arabic_variants(text: str) -> str:
    """Normalize common Arabic script variants without changing letters semantically"""
    # Normalize Alef variants to bare Alef
    text = re.sub(r'[إأآ]', 'ا', text)
    # Normalize Ya variants
    text = re.sub(r'[ى]', 'ي', text)
    # Optional: normalize Ta Marbuta to Heh (or keep it as is)
    # text = re.sub(r'ة', 'ه', text)
    return text

def clean_punctuation_and_spacing(text: str) -> str:
    text = re.sub(r'([؟?!.,])\1+', r'\1', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def strip_emojis_and_symbols(text: str) -> str:
    return EMOJI_PATTERN.sub("", text)

def preprocess_query(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    text = strip_emojis_and_symbols(text)
    try:
        lang = detect(text)
    except:
        lang = "en"  # default to English if detection fails
    if lang == "ar":
        text = normalize_arabic(text)
        text = normalize_arabic_variants(text)   # <-- normalize variants here
    else:
        text = text.lower()
    text = clean_punctuation_and_spacing(text)
    return text

# -------------------------
# Extended examples
# -------------------------
queries = [
    "مـــســاعدۃ  😊؟",
    "Hello!!! HOW are you???",
    "شلونَك؟؟؟؟",
    "كيفــــك 😊😊؟؟",
    "HELLO 😊",
    "مرحبا!! كيفك؟؟؟",
    "why so many spaces           ???",
    "سلامـــــــات",
    "Test!!!🔥🔥🔥",
    "شو رأيك؟؟؟",
    "Hello…",
    "I need help with my account!!!",
    "هذا اختبار للنظام.",
    "Good morning!!! Have a nice day ☀️",
    "هل يمكنك مساعدتي؟؟؟",
    "emoji only 😂😂😂",
    "Mixed content: مرحبا Hello 🙂",
]

# Save results to a text file
output_file = "preprocessed_queries.txt"
with open(output_file, "w", encoding="utf-8") as f:
    for q in queries:
        processed = preprocess_query(q)
        f.write(f"{processed}\n")

print(f"Preprocessed queries saved to {output_file}")
