import fugashi
from typing import List, Dict, Optional
from jamdict import Jamdict
from processing.gpt_wrapper import GptModel
from functools import lru_cache
from models.FocusInfo import FocusInfo
import logging

logger = logging.getLogger(__name__)


class TokenizerService:
    """Service that performs morphological analysis using Fugashi + UniDic."""

    def __init__(self):
        self.tagger = fugashi.Tagger()

    def tokenize(self, sentence: str) -> List[Dict[str, str]]:
        """
        Tokenize a Japanese sentence using Fugashi.

        Args:
            sentence (str): The sentence to tokenize.

        Returns:
            List[Dict[str, str]]: List of token metadata.
        """
        return [
            {
                "surface": word.surface,
                "lemma": word.feature.lemma,
                "reading": word.feature.kana,
                "pos": word.feature.pos1,
            }
            for word in self.tagger(sentence)
        ]


class WordInfoService:
    """Looks up dictionary and JLPT info using Jamdict."""

    def __init__(self):
        self.jam = Jamdict()

    @lru_cache(maxsize=1024)
    def lookup(self, lemma: str) -> Dict[str, str]:
        result = self.jam.lookup(lemma)
        if not result.entries:
            return {
                "word": lemma,
                "reading": "",
                "meanings": [],
                "jlpt": "Unknown",
                "examples": []
            }

        entry = result.entries[0]
        kanji = entry.kana_forms[0].text if entry.kana_forms else ""
        if entry.senses:
            meanings = [str(g) for g in entry.senses[0].gloss]
        else:
            meanings = []
        tags = getattr(entry, "tags", []) or []
        jlpt = next((tag for tag in tags if "jlpt" in tag), "Unknown")

        return {
            "word": lemma,
            "reading": kanji,
            "meanings": meanings,
            "jlpt": jlpt,
            "examples": []
        }


class GptExplainService:
    """
    Service to generate sentence breakdowns and grammar explanations.
    """

    def __init__(self,
                 gpt_model: Optional[GptModel] = None,
                 gpt_model_kwargs: Dict = {},
                 version: str = "gpt-4.1-mini",):
        # Default system message
        system_msg = """
        You are a Japanese language API that explains the specific nuance of
        specified word(s) in a Japanese sentence.
        Respond concisely in no more than 100 words.
        Specified word(s) MUST be in Japanese
        All other explanation text MUST be in English
        In your response:
        DO NOT OUTPUT the language name or the word 'nuance';
        DO NOT OUTPUT the context sentence ;
        DO NOT OUTPUT romaji/furigana or any notes on pronunciation;
        Conclude with the specific nuance within the context sentence.
        """
        gpt_model_kwargs["system_msg"] = system_msg
        gpt_model_kwargs["version"] = version
        self.model = gpt_model if gpt_model else GptModel(**gpt_model_kwargs)
        self.sys_msg = system_msg
        self.version = version

    def explain(self,
                sentence: str,
                focus: str) -> str:
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
        model = GptModel(self.version, self.sys_msg)
        result = model.request(prompt)
        return result['response']

    def explain_custom(self,
                       sentence: str,
                       focus: str,
                       sysMsg: str,
                       prompt: str) -> Optional[str]:
        """
        Request an explanation from GPT using custom system message and prompt.

        Args:
            sentence (str): The full Japanese sentence.
            focus (str): The target word to explain in context.
            sysMsg (str): ChatGPT's system message
            prompt (str): ChatGPT string prompt with formatters
        Returns:
            str: GPT-generated response
        """
        try:
            prompt = prompt.format(sentence, focus)
        except Exception as e:
            logger.error(f"Couldn't format prompt : {e}")
            return None
        model = GptModel(self.version, sysMsg)
        result = model.request(prompt)
        return result['response']

    def explain_sentence(self, sentence: str) -> str:
        """
        Request a breakdown from GPT for a full sentence,
        without requiring a focus word.

        Args:
            sentence (str): A potentially long or informal Japanese sentence.

        Returns:
            str: A full breakdown explanation from GPT, including structure
                 and nuance.
        """
        prompt = f"Sentence : {sentence}. Word: None, explain the sentence."

        model = GptModel(self.version, self.sys_msg)
        result = model.request(prompt)
        return result['response']

    def explain_sentence_custom(self,
                                sentence: str,
                                sysMsg: str,
                                prompt: str) -> Optional[str]:
        """
        Request an explanation from GPT using custom system message and prompt
        without any focus words.

        Args:
            sentence (str): The full Japanese sentence.
            sysMsg (str): ChatGPT's system message
            prompt (str): ChatGPT string prompt with formatters
        Returns:
            str: GPT-generated response
        """
        try:
            prompt = prompt.format(sentence)
        except Exception as e:
            logger.error(f"Couldn't format prompt : {e}")
            return None
        model = GptModel(self.version, sysMsg)
        result = model.request(prompt)
        return result['response']


class SentenceBreakdownService:
    """
    Combines tokenizer, dictionary, and GPT explanation
    into a full grammar breakdown for a sentence.
    """

    def __init__(self,
                 gpt_version: str = "gpt-4.1-mini",
                 gpt_kwargs: Dict = {}):
        self.tokenizer = TokenizerService()
        self.word_info = WordInfoService()
        self.gpt_explainer = GptExplainService(gpt_model_kwargs=gpt_kwargs,
                                               version=gpt_version)

    def word_lookup(self, sentence: str) -> List[Dict]:
        tokens = self.tokenizer.tokenize(sentence)

        enriched_tokens: List[Dict] = []
        for token in tokens:
            lemma = token.get("lemma") or ""
            info = self.word_info.lookup(lemma)

            enriched_tokens.append({
                "surface": token.get("surface") or "",
                "lemma": lemma,
                # Ensure reading is always a string
                "reading": token.get("reading") or "",
                "pos": token.get("pos") or "",
                # Safely fetch fields from FocusInfo
                "meanings": info.get("meanings", []),
                "jlpt": info.get("jlpt", "Unknown"),
                "examples": info.get("examples", []),
            })
        return enriched_tokens

    def explain(self, sentence: str,
                focus: Optional[str] = None) -> Dict:
        """
        Perform a complete sentence breakdown

        Args:
            sentence (str): The full Japanese sentence to analyze.
            focus (str): The key word to generate deeper explanation for.

        Returns:
            Dict: Includes tokens, word info, and GPT breakdown
        """
        enriched_tokens = self.word_lookup(sentence)

        # Generate GPT breakdown text
        if focus:
            gpt_text = self.gpt_explainer.explain(sentence, focus)
            f_lemma = focus or ""
            try:
                focus_data = self.word_info.lookup(f_lemma)
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

        return {
            "sentence": sentence,
            "focus": focus_data,
            "tokens": enriched_tokens,
            "gpt_explanation": gpt_text,
        }

    def explain_custom(self,
                       sentence: str,
                       sysMsg: str,
                       prompt: str,
                       focus: Optional[str] = None) -> Dict:
        """
        Perform a complete sentence breakdown using custom System Message
        and Prompt

        Args:
            sentence (str): The full Japanese sentence to analyze.
            focus (str): The key word to generate deeper explanation for.
            sysMsg (str): ChatGPT's system message
            prompt (str): ChatGPT prompt, must contain {0} and {1} representing
            sentence and foucus word to be formatted in respectively

        Returns:
            Dict: Includes tokens, word info, and GPT breakdown
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
                focus_data = self.word_info.lookup(f_lemma)
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

        return {
            "sentence": sentence,
            "focus": focus_data,
            "tokens": enriched_tokens,
            "gpt_explanation": gpt_text,
        }
