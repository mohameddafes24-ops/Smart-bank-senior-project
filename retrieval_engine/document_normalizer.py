import unicodedata
import regex as re

# -------------------------
# Arabic normalization
# -------------------------
ARABIC_DIACRITICS = re.compile(
    r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]'
)
TATWEEL = "\u0640"

def normalize_arabic(text: str) -> str:
    text = ARABIC_DIACRITICS.sub("", text)
    text = text.replace(TATWEEL, "")
    return text

def normalize_arabic_variants(text: str) -> str:
    # Safe, meaning-preserving normalizations
    text = re.sub(r'[إأآ]', 'ا', text)
    text = re.sub(r'[ؤ]', 'و', text)
    text = re.sub(r'[ئ]', 'ي', text)
    text = re.sub(r'[ى]', 'ي', text)
    return text

# -------------------------
# Invisible junk removal
# -------------------------
INVISIBLE_JUNK = {
    "\u200b",  # zero width space
    "\u200c",  # zero width non-joiner
    "\u200d",  # zero width joiner
    "\ufeff",  # BOM
}

def strip_invisible(text: str) -> str:
    return "".join(ch for ch in text if ch not in INVISIBLE_JUNK)

# -------------------------
# Whitespace normalization
# -------------------------
def normalize_whitespace(text: str) -> str:
    # Collapse excessive whitespace but preserve paragraph breaks
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# -------------------------
# Document-safe normalization
# -------------------------
def normalize_document(text: str) -> str:
    if not text:
        return ""

    # Canonical Unicode form
    text = unicodedata.normalize("NFC", text)

    # Remove invisible junk only
    text = strip_invisible(text)

    # Arabic script normalization (script-aware)
    if re.search(r'[\u0600-\u06FF]', text):
        text = normalize_arabic(text)
        text = normalize_arabic_variants(text)

    # Whitespace cleanup
    text = normalize_whitespace(text)

    return text
