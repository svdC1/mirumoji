"""
This module defines the `SentenceBreakdownService` class for analysing Japanese
senteces using fugashi and kotobase.

Attributes:
  LOGGER (logging.Logger): Module's Logger object.
"""

import fugashi
from typing import List, Dict, Optional
from kotobase import Kotobase
from kotobase.core.datatypes import (JMDictEntryDTO, JMNeDictEntryDTO)
from processing.gpt_wrapper import GptModel
from functools import lru_cache
from models.FocusInfo import FocusInfo
from models.Token import Token
import logging

LOGGER = logging.getLogger(__name__)


class GptExplainService:
    """
    Wrapper for the `GptModel` class with default sys_msg and utility functions

    Args:
      gpt_model_kwargs (dict): Additional keyword arguments for `GptModel`
      version (str): OpenAI GPT version to use.

    Attributes:
      SYSTEM_MSG (str): Default system message used.
    """

    SYSTEM_MSG = """You are a Japanese language API that explains the specific
nuance of specified word(s) in a Japanese sentence.
Respond concisely in no more than 100 words.
Specified word(s) MUST be in Japanese
All other explanation text MUST be in English
In your response:
  DO NOT OUTPUT the language name or the word 'nuance';
  DO NOT OUTPUT the context sentence ;
  DO NOT OUTPUT romaji/furigana or any notes on pronunciation;
  Conclude with the specific nuance within the context sentence.
        """

    def __init__(self,
                 gpt_model_kwargs: Dict = {},
                 version: str = "gpt-4.1-mini"
                 ) -> None:

        if "system_msg" not in gpt_model_kwargs.keys():
            gpt_model_kwargs["system_msg"] = GptExplainService.SYSTEM_MSG
        if "version" not in gpt_model_kwargs.keys():
            gpt_model_kwargs["version"] = version
        if "ApiKey" not in gpt_model_kwargs.keys():
            gpt_model_kwargs["version"] = None
        if "from_dotenv" not in gpt_model_kwargs.keys():
            gpt_model_kwargs['from_dotenv'] = True
        if "max_context" not in gpt_model_kwargs.keys():
            gpt_model_kwargs["max_context"] = 100000

        self.model_kwargs = gpt_model_kwargs

    def explain(self,
                sentence: str,
                focus: str
                ) -> str:
        """
        Request an explanation from GPT using default system message
        and prompt.

        Args:
          sentence (str): The full Japanese sentence.
          focus (str): The target word to explain in context.

        Returns:
          str: GPT-generated explanation with structure, particles,
               and nuance.
        """
        prompt = f"{sentence}. Explain usage of word : {focus}"
        model = GptModel(**self.model_kwargs)
        result = model.request(prompt)
        return result['response']

    def explain_custom(self,
                       sentence: str,
                       focus: str,
                       sysMsg: str,
                       prompt: str
                       ) -> Optional[str]:
        """
        Request an explanation from GPT using custom system message and prompt.

        Args:
          sentence (str): The full Japanese sentence.
          focus (str): The target word to explain in context.
          sysMsg (str): GPT's system message
          prompt (str): GPT's string prompt containing formatters
                        `{0}` = `sentence` and `{1}` = `focus`

        Returns:
          str: GPT-generated response
        """

        try:
            prompt = prompt.format(sentence, focus)
        except Exception as e:
            LOGGER.error(f"Couldn't format prompt : {e}")
            return None
        model = GptModel(self.model_kwargs["version"],
                         sysMsg,
                         self.model_kwargs["from_dotenv"],
                         self.model_kwargs["ApiKey"],
                         self.model_kwargs["max_context"]
                         )
        result = model.request(prompt)
        return result['response']

    def explain_sentence(self, sentence: str) -> str:
        """
        Request from GPT for a full sentence without requiring a focus word.

        Args:
          sentence (str): A potentially long or informal Japanese sentence.

        Returns:
          str: A full breakdown explanation from GPT, including structure
               and nuance.
        """
        prompt = f"Sentence : {sentence}. Word: None, explain the sentence."

        model = GptModel(**self.model_kwargs)
        result = model.request(prompt)
        return result['response']

    def explain_sentence_custom(self,
                                sentence: str,
                                sysMsg: str,
                                prompt: str
                                ) -> Optional[str]:
        """
        Request an explanation from GPT using custom system message and prompt
        without any focus words.

        Args:
          sentence (str): The full Japanese sentence.
          sysMsg (str): ChatGPT's system message
          prompt (str): GPT's string prompt containing formatters
                        `{0}` = `sentence`

        Returns:
            str: GPT-generated response
        """
        try:
            prompt = prompt.format(sentence)
        except Exception as e:
            LOGGER.error(f"Couldn't format prompt : {e}")
            return None
        model = GptModel(self.model_kwargs["version"],
                         sysMsg,
                         self.model_kwargs["from_dotenv"],
                         self.model_kwargs["ApiKey"],
                         self.model_kwargs["max_context"]
                         )
        result = model.request(prompt)
        return result['response']


@lru_cache(maxsize=1024)
def _query_kotobase(word: str) -> Dict:
    """
    Wrapper for `kotobase.Kotobase.lookup` with lru cache and result
    processing.

    Args:
        word (str): Word for query.

    Returns:
        dict: Extracted word information.
    """
    l_result = Kotobase().lookup(word=word,
                                 wildcard=False,
                                 include_names=True,
                                 sentence_limit=5
                                 )
    jlpt = (
        f"N{l_result.jlpt_vocab.level}" if l_result.jlpt_vocab else "Unknown"
        )
    examples = (
        [st.text for st in l_result.examples] if l_result.examples else []
        )
    if l_result.entries:
        entry = l_result.entries[0]
        if isinstance(entry, JMDictEntryDTO):
            meanings = (
                [s["gloss"] for s in entry.senses] if entry.senses else []
                )
            reading = ",".join(entry.kana) if entry.kana else ""
        elif isinstance(entry, JMNeDictEntryDTO):
            meanings = (
                [entry.translation_type] if entry.translation_type else []
                )
            reading = ",".join(entry.kana) if entry.kana else ""
    else:
        meanings = []
        reading = ""
        jlpt = "Unknown"
        examples = []

    return {
        "result": l_result,
        "meanings": meanings,
        "reading": reading,
        "jlpt": jlpt,
        "examples": examples
        }


class SentenceBreakdownService:
    """
    Provides utlities for analyzing Japanese sentences.

    Args:
      gpt_version (str): OpenAI GPT version to use.
      gpt_kwargs (dict): Additional keyword arguments for `GptModel`
    """

    def __init__(self,
                 gpt_version: str = "gpt-4.1-mini",
                 gpt_kwargs: Dict = {}
                 ) -> None:

        self.gpt_explainer = GptExplainService(gpt_model_kwargs=gpt_kwargs,
                                               version=gpt_version
                                               )
        # Check if Fugashi is available
        try:
            self.tagger = fugashi.Tagger()
            self.tagger("試しに")
        except Exception as e:
            LOGGER.exception("Failed to start fugashi.")
            raise e

        # Check if Kotobase is available
        try:
            self.kb = Kotobase()
            self.kb.lookup("試し",
                           wildcard=False,
                           sentence_limit=1)
        except Exception as e:
            LOGGER.exception("Failed to start kotobase.")
            raise e

    def tokenize(self, sentence: str) -> List[Dict]:
        """
        Tokenize a Japanese sentence using fugashi and extract
        token information.

        Args:
          sentence (str): Sentence to tokenize

        Returns:
          list: List of dictionaries containing token information.
        """

        return [{
            "surface": tok.surface,
            "kana": tok.feature.kana,
            "pos": tok.feature.pos1,
            "lemma": tok.feature.lemma,
            "cType": tok.feature.cType,
            "cForm": tok.feature.cForm,
            "pos_lst": tok.pos.split(",")
            } for tok in self.tagger(sentence)
                ]

    def word_lookup(self, sentence: str) -> List[Dict]:
        """
        Tokenize every word in a Japanese sentence, extract information and
        lookup every token with kotobase.

        Args:
          sentence (str): Japanese sentence to tokenize.

        Returns:
          list: List of dictionaries containing token information.
        """

        tokens = self.tokenize(sentence)
        lookups = [_query_kotobase(word=tok["surface"]) for tok in tokens]
        e_tokens = [{
                "surface": tok["surface"],
                "lemma": tok["lemma"],
                "reading": tok["kana"],
                "pos": tok["pos"],
                "meanings": lu["meanings"],
                "jlpt": lu["jlpt"],
                "examples": lu["examples"]
            } for tok, lu in zip(tokens, lookups)]
        return e_tokens

    def explain(self,
                sentence: str,
                focus: Optional[str] = None) -> Dict:
        """
        Perform a complete Japanese sentence breakdown.

        Args:
          sentence (str): The full Japanese sentence to analyze.
          focus (str): The key word to generate deeper explanation for.

        Returns:
          dict: Includes tokens, word info, and GPT breakdown
        """
        enriched_tokens = self.word_lookup(sentence)

        # Generate GPT breakdown text
        if focus:
            gpt_text = self.gpt_explainer.explain(sentence, focus)
            f_lemma = focus or ""
            try:
                info = _query_kotobase(word=f_lemma)
                focus_data = FocusInfo(word=f_lemma,
                                       reading=info["reading"],
                                       meanings=info["meanings"],
                                       jlpt=info["jlpt"],
                                       examples=info["examples"]
                                       )
            except ValueError:
                focus_data = FocusInfo(
                    word=f_lemma,
                    reading="",
                    meanings=[],
                    jlpt="",
                    examples=[],
                )
        else:
            gpt_text = self.gpt_explainer.explain_sentence(sentence)
            focus_data = FocusInfo(
                word="",
                reading="",
                meanings=[],
                jlpt="",
                examples=[],
            )

        # Create Token Models
        tokens = [Token(surface=t["surface"],
                        lemma=t["lemma"],
                        reading=t["reading"],
                        pos=t["pos"]
                        ) for t in enriched_tokens
                  ]
        return {
            "sentence": sentence,
            "focus": focus_data,
            "tokens": tokens,
            "gpt_explanation": gpt_text,
        }

    def explain_custom(self,
                       sentence: str,
                       sysMsg: str,
                       prompt: str,
                       focus: Optional[str] = None) -> Dict:
        """
        Perform a complete sentence breakdown using custom sys_msg and prompt

        Args:
          sentence (str): The full Japanese sentence to analyze.
          focus (str): The key word to generate deeper explanation for.
          sysMsg (str): ChatGPT's system message
          prompt (str): GPT's string prompt containing formatters
                        `{0}` = `sentence` and `{1}` = `focus`

        Returns:
          dict: Includes tokens, word info, and GPT breakdown
        """
        enriched_tokens = self.word_lookup(sentence)

        # Generate GPT breakdown text
        if focus:
            gpt_text = self.gpt_explainer.explain_custom(sentence,
                                                         focus,
                                                         sysMsg,
                                                         prompt)
            f_lemma = focus or ""
            try:
                info = _query_kotobase(word=f_lemma)
                focus_data = FocusInfo(word=f_lemma,
                                       reading=info["reading"],
                                       meanings=info["meanings"],
                                       jlpt=info["jlpt"],
                                       examples=info["examples"]
                                       )
            except ValueError:
                focus_data = FocusInfo(
                    word=f_lemma,
                    reading="",
                    meanings=[],
                    jlpt="",
                    examples=[],
                )
        else:
            gpt_text = self.gpt_explainer.explain_sentence_custom(sentence,
                                                                  sysMsg,
                                                                  prompt)
            focus_data = FocusInfo(
                word="",
                reading="",
                meanings=[],
                jlpt="",
                examples=[],
            )

        # Create Token Models
        tokens = [Token(surface=t["surface"],
                        lemma=t["lemma"],
                        reading=t["reading"],
                        pos=t["pos"]
                        ) for t in enriched_tokens
                  ]
        return {
            "sentence": sentence,
            "focus": focus_data,
            "tokens": tokens,
            "gpt_explanation": gpt_text,
        }
