"""
This module defines the `GptModel` class for sending requests to OpenAI's API.

Attributes:
  LOGGER (logging.Logger): Module's logger object
"""
from __future__ import annotations
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
from dotenv import dotenv_values, load_dotenv
import logging
import os
from typing import Optional, Dict, Generator, Any
import json

LOGGER = logging.getLogger(__name__)


class GptModel:
    """
    Send requests to OpenAI's API and manage sessions.

    Args:
      version (str): Which GPT model version to use.
      system_msg (str): The System Message to use for the model.
      from_dotenv (bool): Wether to get the OpenAI API key through a .env file.
      ApiKey (str, optional): Option to pass the OpenAI API key directly.
      max_context (int): The session's context limit in tokens.

    Attributes:
      info (dict): Dictionary containing all object information.
    """
    MODEL_VERSIONS = [
        'gpt-4.1',
        'gpt-4o-mini',
        'gpt-4o',
        'gpt-4.1-mini'
        ]
    FRMAP = {'stop': 0,
             'length': 1,
             'function_call': 2,
             'content_filter': 3,
             'null': 4,
             }

    FRCODEDICT = {
        0: 'Success,Complete Message',
        1: 'Token Limit or parameter "max_token" exceeded,Incomplete Message',
        2: 'The model decided to call a function,Incomplete Message',
        3: "Content flagged and stopped by model's content filter, \
            Incomplete Message",
        4: "API Response is still in progress,Incomplete Message"
        }

    def __init__(self,
                 version: str,
                 system_msg: str = 'default',
                 from_dotenv: bool = True,
                 ApiKey: Optional[str] = None,
                 max_context: int = 100000
                 ) -> None:
        try:
            # Store Session Info
            self.info = {}

            if from_dotenv:
                # Get API Key from .env
                load_dotenv()
                try:
                    key = dotenv_values('.env')['OPENAI_API_KEY']
                except Exception:
                    try:
                        key = os.environ["OPENAI_API_KEY"]
                    except Exception as e:
                        LOGGER.error("OpenAI key not found")
                        raise e

            elif ApiKey is not None:
                key = ApiKey

            else:
                LOGGER.error(
                    "Must provide ApiKey or enable from_dotenv to create \
                        client"
                    )
                raise Exception(
                    "Must provide ApiKey or enable from_dotenv to create \
                        client")

            self.client = OpenAI(api_key=key)

            if version not in GptModel.MODEL_VERSIONS:
                LOGGER.error(
                    f"Model version provided is not supported, got {version};\
                        Expected one of {GptModel.MODEL_VERSIONS}"
                    )
                raise Exception(
                    f"Model version provided is not supported, got {version};\
                        Expected one of {GptModel.MODEL_VERSIONS}")
            else:
                model = version
            if system_msg == 'default':
                system_message = "You are a helpful assistant."
            else:
                system_message = system_msg

            sys_msg = {"role": "system", "content": system_message}

            self.info["client"] = self.client
            self.info["ApiKey"] = key
            self.info["model"] = model
            self.info["sys_msg"] = sys_msg
            self.info["raw_sys_msg"] = system_message
            self.info["from_dotenv"] = from_dotenv
            self.info["raw_ApiKey"] = ApiKey
            self.info["window_token_limit"] = max_context
            self.info["messages"] = [sys_msg]
            self.info["outputs"] = []
            self.info["inputs"] = []
            self.info["total_tokens"] = None
            self.info["input_tokens"] = None
            self.info["request_count"] = 0
            self.info["output_tokens"] = None
            self.info["requests_info"] = []
            self.info["sessions_info"] = []
            self.info["text_finishin_reasons"] = []

        except Exception as e:
            LOGGER.error(
                f'Error while cretaing Model Object : {str(e)}')
            raise Exception(
                f'Error while cretaing Model Object : {str(e)}')

    @staticmethod
    def _format_input(message: str) -> Dict[str, str]:
        return {"role": "user", "content": message}

    @staticmethod
    def _format_output(message: str) -> Dict[str, str]:
        return {"role": "assistant", "content": message}

    @staticmethod
    def _process_output(response: ChatCompletion) -> Dict:

        usage_dict = response.usage.to_dict()
        try:
            prompt_tokens = int(usage_dict['prompt_tokens'])
            output_tokens = int(usage_dict['completion_tokens'])
            total_tokens = int(usage_dict['total_tokens'])

        except Exception as e:
            raise Exception(f"Error converting token counts to int : {e}")

        message = response.choices[0].message.content
        finish_reason = response.choices[0].finish_reason
        try:
            finish_reason = GptModel.FRMAP[finish_reason]
        except KeyError:
            LOGGER.error(f'Received Unexpected Finish Reason: {finish_reason}')
            raise

        return {'output': message,
                'prompt_tokens': prompt_tokens,
                'output_tokens': output_tokens,
                'total_tokens': total_tokens,
                'finish_reason': finish_reason
                }

    def __str__(self) -> str:
        return f"{self.info['model']}"

    def __repr__(self) -> str:
        return f"{self.info}"

    def request(self, prompt: str) -> Dict:
        """
        Make a new session request.

        Args:
          prompt (str): The prompt for the request.

        Returns:
          dict: Dictionary containg "prompt" used and the formatted "response"
        """
        self.info["inputs"].append(prompt)
        new_message = GptModel._format_input(prompt)
        self.info["messages"].append(new_message)
        wtl = self.info["window_token_limit"]
        if self.info["request_count"] > 0 and self.info["total_tokens"] >= wtl:
            raise Exception('Max Context Exceeded')
        try:
            msgs = self.info["messages"]
            result = self.info["client"].chat.completions.create(
                model=self.info["model"],
                messages=msgs)
            f_result = GptModel._process_output(result)
            self.info["requests_info"].append(f_result)
            self.info["outputs"].append(f_result['output'])
            self.info["messages"].append(
                GptModel._format_output(f_result['output']))
            self.info["input_tokens"] = f_result['prompt_tokens']
            self.info["output_tokens"] = f_result['output_tokens']
            self.info["total_tokens"] = f_result['total_tokens']
            self.info["request_count"] += 1
            freason_dict = GptModel.FRCODEDICT
            freason = freason_dict[f_result['finish_reason']]
            self.info["text_finishin_reasons"].append(freason)
            return {'prompt': prompt,
                    'response': f_result['output']
                    }

        except Exception as e:
            LOGGER.error(f'Error Requesting : {str(e)}')
            raise e

    def stream_request(self, prompt: str) -> Generator[Any, None, None]:
        """
        Send a streaming chat request; yield each content
        chunk as it arrives.

        Args:
          prompt (str): Prompt to use.

        Yields:
          str: The string chunks from the request response.
        """
        self.info["inputs"].append(prompt)
        self.info["messages"].append(GptModel._format_input(prompt))

        try:
            stream = self.info["client"].chat.completions.create(
                model=self.info["model"],
                messages=self.info["messages"],
                stream=True
            )

            full_output = ""
            for chunk in stream:
                delta = chunk.choices[0].delta
                text = getattr(delta, "content", None) or ""
                if text:
                    full_output += text
                    yield text

            self.info["outputs"].append(full_output)
            self.info["messages"].append(GptModel._format_output(full_output))
            self.info["request_count"] += 1

        except Exception as e:
            LOGGER.error(f"Streaming request error: {e}")
            raise Exception(f"Error during streaming request: {e}")

    def new_session(self) -> None:
        """
        Clear the current session.
        """

        session_info = {'total_tokens': self.info["total_tokens"],
                        'inputs': self.info["inputs"],
                        'outputs': self.info["outputs"],
                        'requests_info': self.info["requests_info"],
                        'input_tokens': self.info["input_tokens"],
                        'output_tokens': self.info["output_tokens"],
                        'request_count': self.info["request_count"]
                        }
        self.info["sessions_info"].append(session_info)
        self.info["messages"] = [self.sys_msg]
        self.info["outputs"] = []
        self.info["inputs"] = []
        self.info["total_price"] = 0
        self.info["total_tokens"] = None
        self.info["input_tokens"] = None
        self.info["request_count"] = 0
        self.info["output_tokens"] = None
        self.info["requests_info"] = []
        LOGGER.info('Session Cleared!')

    @staticmethod
    def load_from_json(info: str) -> GptModel:
        """
        Load an object from a serialized JSON string

        Args:
          info (str): JSON string.
        """
        info = json.loads(info)

        gpt_model = GptModel(version=info["model"],
                             system_msg=info["sys_msg"],
                             from_dotenv=info["from_dotenv"],
                             ApiKey=info["raw_ApiKey"],
                             max_context=info["window_token_limit"]
                             )

        gpt_model.info = info
        gpt_model.info["client"] = OpenAI(api_key=gpt_model.info["ApiKey"])
        return gpt_model

    def serialize(self) -> str:
        """
        Serialize object information into JSON string
        """
        return json.dumps(self.info, skipkeys=True)
