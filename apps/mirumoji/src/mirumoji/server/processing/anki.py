"""
Defines stateless helpers for exporting a profile's saved clips as an Anki
deck using `genanki`

Attributes:
  VIDEO_CSS (str): Pre-defined CSS of the cards
  CARD_TEMPLATE (list): Pre-defined template of the cards for `genanki`
  MODEL_FIELDS (list): Pre-defined card model fields
  MODEL_NAME (str): Pre-defined standard model name
  DECK_NAME (str): Pre-defined standard deck name
  VIDEO_TAG (str): HTML `<video>` tag template embedding a bundled clip
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path

import genanki

LOGGER = logging.getLogger(__name__)

VIDEO_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;\
    700&display=swap');
.card {
background: #fdfdfd;
font-family: 'Noto Sans JP', sans-serif;
color: #333;
padding: 20px;
text-align: center;
}
.card h1 {
font-size: 2.2rem;
font-weight: 700;
margin-bottom: 0.5em;
}
.video-container {
margin: 1em auto;
max-width: 320px;
box-shadow: 0 4px 8px rgba(0,0,0,0.1);
border-radius: 8px;
overflow: hidden;
}
.video-container video {
width: 100%;
display: block;
}
.sentence {
font-size: 1.1rem;
margin: 1em 0;
}
.explanation {
font-size: 0.95rem;
color: #555;
line-height: 1.4;
text-align: left;
}
hr {
border: none;
border-top: 1px solid #eee;
margin: 1.5em 0;
}
"""

CARD_TEMPLATE = [
    {
        "name": "Recognition → Recall",
        "qfmt": '<div class="card"><h1>{{Word}}</h1></div>',
        "afmt": """
          {{FrontSide}}
          <hr>
          <div class="card">
            <div class="video-container">
            {{Clip}}
            </div>
            <div class="meanings"><strong>Meaning:</strong>{{Meanings}}</div>
            <div class="sentence"><strong>Sentence:</strong> {{Sentence}}</div>
            <div class="explanation">{{Explanation}}</div>
          </div>
        """,
    },
]

MODEL_FIELDS = [
    {"name": "Clip"},
    {"name": "Word"},
    {"name": "Meanings"},
    {"name": "Sentence"},
    {"name": "Explanation"},
]

MODEL_NAME = "Mirumoji-Anki-V1"

DECK_NAME = MODEL_NAME + " Deck"

VIDEO_TAG = '<video controls><source src="{0}" type="video/webm"/></video>'


@dataclass
class AnkiCard:
    """
    Data for a single Anki card built from a saved clip

    Attributes:
        clip_path (str): Absolute path to the clip file, bundled as card media
        word (str): The focus word shown on the card front
        meanings (str): The word's meanings as a single string
        sentence (str): The sentence the word came from
        explanation (str): The LLM explanation of the sentence
        tags (list[str]): Optional card tags
    """

    clip_path: str
    word: str
    meanings: str
    sentence: str
    explanation: str
    tags: list[str] = field(default_factory=list)


def id_from_string(s: str) -> int:
    """
    Creates a stable, unique genanki model/deck id from a string

    Args:
        s (str): String to derive the id from

    Returns:
        An integer id derived from the string's SHA-1 digest
    """
    return int.from_bytes(hashlib.sha1(s.encode()).digest()[:4], "big")


def build_model() -> genanki.Model:
    """
    Builds the shared `genanki.Model` used for every Mirumoji card

    Returns:
        The configured `genanki.Model`
    """
    return genanki.Model(
        model_id=id_from_string(MODEL_NAME),
        name=MODEL_NAME,
        fields=MODEL_FIELDS,
        templates=CARD_TEMPLATE,
        css=VIDEO_CSS,
    )


def export_deck(cards: list[AnkiCard], output_path: str) -> None:
    """
    Builds a deck from `cards` and writes it (with bundled clip media) to disk

    Each card's `clip_path` is bundled into the package as media and embedded
    in the card via an HTML `<video>` tag referencing the file's base name

    Args:
        cards (list[AnkiCard]): The cards to add to the deck
        output_path (str): Path to write the resulting `.apkg` file to
    """
    model = build_model()
    deck = genanki.Deck(id_from_string(DECK_NAME), DECK_NAME)
    media_files: list[str] = []

    for card in cards:
        filename = Path(card.clip_path).name
        video = VIDEO_TAG.format(filename)
        media_files.append(card.clip_path)
        deck.add_note(
            genanki.Note(
                model=model,
                fields=[
                    video,
                    card.word,
                    card.meanings,
                    card.sentence,
                    card.explanation,
                ],
                tags=card.tags,
            ),
        )

    genanki.Package(deck, media_files).write_to_file(output_path)
    LOGGER.info(
        f"Created Anki Package | "
        f"File -> '{output_path}' | "
        f"#Notes -> '{len(deck.notes)}' | "
        f"#Media -> '{len(media_files)}' | ",
    )
