"""
This module defines the `AnkiExporter` class for creating an
Anki deck from the user's saved clips using `genanki`

Attributes:
  LOGGER (logging.Logger): Module's logger.
  VIDEO_CSS (str): Pre-defined CSS of the cards
  CARD_TEMPLATE (list): Pre-defined template of the cards for `genanki`
  MODEL_FIELDS (list): Pre-defined card model fields.
  MODEL_NAME (str): Pre-defined standard deck name.
"""

import hashlib
import logging
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


class AnkiExporter:
    """
    Exports saved clips as an Anki Deck.

    Args:
      model_name (str, optional): Model name for genanki
      deck_name (str, optional): Deck name for genanki
      model_fields (list, optional): Model fields for genanki
      css (str, optional): Card CSS for genanki
      card_template (list, optional): Card template for genanki.

    """

    def __init__(
        self,
        model_name: str | None = MODEL_NAME,
        deck_name: str | None = MODEL_NAME + " Deck",
        model_fields: list | None = MODEL_FIELDS,
        css: str | None = VIDEO_CSS,
        card_template: list | None = CARD_TEMPLATE,
    ) -> None:

        self.model_name = model_name
        self.model_id = __class__.id_from_string(model_name)
        self.css = css
        self.card_template = card_template
        self.model = genanki.Model(
            model_id=self.model_id,
            name=model_name,
            fields=model_fields,
            templates=card_template,
            css=css,
        )

        self.deck_name = deck_name
        self.deck_id = __class__.id_from_string(deck_name)
        self.deck = genanki.Deck(self.deck_id, self.deck_name)
        self.media_files: list[str] = []
        self.video_tag = '<video controls><source src="{0}"\
            type="video/webm"/></video>'

    @staticmethod
    def id_from_string(s: str) -> int:
        """
        Create a unique anki deck ID from string

        Args:
          s (str): String to create ID from

        Returns:
          int: ID generated using hashlib.
        """
        return int.from_bytes(hashlib.sha1(s.encode()).digest()[:4], "big")

    def add_card(
        self,
        clip_path: str,
        word: str,
        meanings: str,
        sentence: str,
        explanation: str,
        tags: list[str] | None = None,
    ) -> None:
        """
        Add one card to the deck, `clip_path` will be bundled as media.

        Args:
          clip_path (str): Path to the clip
          word (str): Card word
          meanings (str): Word meanings in string form.
          sentence (str): Sentence the word came from.
          explanation (str): GPT explanation of the sentence.
          tags (list, optional): Optional card tags.
        """
        filename = Path(clip_path).name
        video = self.video_tag.format(filename)
        self.media_files.append(clip_path)

        note = genanki.Note(
            model=self.model,
            fields=[video, word, meanings, sentence, explanation],
            tags=tags or [],
        )
        self.deck.add_note(note)

    def export(self, output_path: str) -> None:
        """
        Write .apkg (deck + all media) to output_path.

        Args:
          output_path (str): Path to save the Anki Deck.
        """
        pkg = genanki.Package(self.deck, self.media_files)
        pkg.write_to_file(output_path)
        _notes = f"#Notes -> '{len(self.deck.notes)}';"
        _media = f"#Media -> '{len(self.media_files)}';"
        LOGGER.info(f"Anki Package -> '{output_path}';{_notes}{_media}")
