from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
from dotenv import dotenv_values, load_dotenv
import logging
import os


class GptModel:
    model_versions = ['gpt-4.1', 'gpt-4o-mini', 'gpt-4o', 'gpt-4.1-mini']
    # Per 1 Million Tokens, in Dollars
    pricing_dict = {'gpt-4o-mini': {'input': 0.150, 'output': 0.6},
                    'gpt-4.1': {'input': 2.0, 'output': 8},
                    'gpt-4o': {'input': 2.5, 'output': 10},
                    'gpt-4.1-mini': {'input': 0.4, 'output': 1.6}}

    logger = logging.getLogger('gpt-model')
    fr_0 = 'Success,Complete Message'
    fr_1 = 'Token Limit or parameter "max_token" exceeded,Incomplete Message'
    fr_2 = 'The model decided to call a function,Incomplete Message'
    fr_3 = "Content flagged and stopped by model's content filter"
    fr_3 += ",Incomplete Message"
    fr_4 = "API Response is still in progress,Incomplete Message"
    finish_reason_code_dict = {0: fr_0,
                               1: fr_1,
                               2: fr_2,
                               3: fr_3,
                               4: fr_4}

    def __init__(self, version: str, system_msg: str = 'default',
                 from_dotenv: bool = True, ApiKey=None,
                 max_context: int = 100000):
        try:
            if from_dotenv:
                load_dotenv()
                try:
                    key = dotenv_values('.env')['OPENAI_API_KEY']
                except Exception:
                    try:
                        key = os.environ["OPENAI_API_KEY"]
                    except Exception as e:
                        GptModel.logger.error("OpenAI key not found")
                        raise e
                self.ApiKey = key
                ApiKey = self.ApiKey
            elif ApiKey is not None:
                key = ApiKey
            else:
                _msg = "Must provide ApiKey or enable from_dotenv to create"
                _msg += 'client'
                GptModel.logger.error(_msg)
                raise Exception(_msg)
            self.client = OpenAI(api_key=key)
            if version not in GptModel.model_versions:
                _msg = 'Model version provided is not supported, got'
                _msg += f"{version};Expected one of {GptModel.model_versions}"
                GptModel.logger.error(_msg)
                raise Exception(_msg)
            else:
                self.model = version
            if system_msg == 'default':
                system_message = "You are a helpful assistant."
            else:
                system_message = system_msg
            sys_msg = {"role": "system", "content": system_message}
            # --Attrs for repr----
            self.raw_sys_msg = system_message
            self.from_dotenv = from_dotenv
            self.ApiKey = ApiKey
            # --------------------
            self.sys_msg = sys_msg
            self.window_token_limit = max_context
            self.messages = [sys_msg]
            self.outputs = []
            self.inputs = []
            self.total_price = 0
            self.total_tokens = None
            self.input_tokens = None
            self.request_count = 0
            self.output_tokens = None
            self.requests_info = []
            self.sessions_info = []
            self.text_finishin_reasons = []
        except Exception as e:
            _msg = f'Error while cretaing Model Object : {str(e)}'
            GptModel.logger.error(_msg)
            raise Exception(_msg)

    @staticmethod
    def format_input(message: str):
        return {"role": "user", "content": message}

    @staticmethod
    def format_output(message: str):
        return {"role": "assistant", "content": message}

    @staticmethod
    def response_price(model: str, input_tokens: int, output_tokens: int):
        if model not in GptModel.model_versions:
            raise Exception(f'Model {model} not supported')
        input_price_1m = GptModel.pricing_dict[model]['input']
        output_price_1m = GptModel.pricing_dict[model]['output']
        input_price_per_token = input_price_1m/(10**6)
        output_price_per_token = output_price_1m/(10**6)
        InputPrice = input_tokens*input_price_per_token
        OutputPrice = output_tokens*output_price_per_token
        return InputPrice+OutputPrice

    @staticmethod
    def process_output(response: ChatCompletion,
                       model: str):
        usage_dict = response.usage.to_dict()
        try:
            prompt_tokens = int(usage_dict['prompt_tokens'])
            output_tokens = int(usage_dict['completion_tokens'])
            total_tokens = int(usage_dict['total_tokens'])
            request_price = GptModel.response_price(model,
                                                    prompt_tokens,
                                                    output_tokens)
        except Exception as e:
            em = "Error converting token counts to int"
            em += f"and calculating price : {str(e)}"
            raise Exception(em)
        message = response.choices[0].message.content
        finish_reason = response.choices[0].finish_reason
        if finish_reason == 'stop':
            finish_reason = 0
        elif finish_reason == 'length':
            finish_reason = 1
        elif finish_reason == 'function_call':
            finish_reason = 2
        elif finish_reason == 'content_filter':
            finish_reason = 3
        elif finish_reason == 'null':
            finish_reason = 4
        else:
            em = f'Received Unexpected Finish Reason: {finish_reason}'
            raise Exception(em)

        return {'output': message, 'prompt_tokens': prompt_tokens,
                'output_tokens': output_tokens, 'total_tokens': total_tokens,
                'finish_reason': finish_reason, 'price': request_price}

    def __str__(self):
        return f"{self.model} Wrapper, with System Message :{self.raw_sys_msg}"

    def __repr__(self):
        m = self.model
        s = self.raw_sys_msg
        d = self.from_dotenv
        a = self.ApiKey
        w = self.window_token_limit
        at = ['version', 'system_msg', 'from_dotenv', 'ApiKey', 'max_content']
        c = 'GptModel'
        ats = [f"{at[0]}='{m}'",
               f"{at[1]}='{s}'",
               f"{at[2]}={d}",
               f"{at[3]}='{a}'",
               f"{at[4]}={w}"]
        r = f"{c}({ats[0]},{ats[1]},{ats[2]},{ats[3]},{ats[4]})"
        return r

    def request(self, prompt: str):
        self.inputs.append(prompt)
        new_message = GptModel.format_input(prompt)
        self.messages.append(new_message)
        wtl = self.window_token_limit
        if self.request_count > 0 and self.total_tokens >= wtl:
            raise Exception('Max Context Exceeded')
        try:
            msgs = self.messages
            result = self.client.chat.completions.create(model=self.model,
                                                         messages=msgs)
            f_result = GptModel.process_output(result, self.model)
            self.requests_info.append(f_result)
            self.outputs.append(f_result['output'])
            self.messages.append(GptModel.format_output(f_result['output']))
            self.input_tokens = f_result['prompt_tokens']
            self.output_tokens = f_result['output_tokens']
            self.total_tokens = f_result['total_tokens']
            self.total_price += f_result['price']
            self.request_count += 1
            freason_dict = GptModel.finish_reason_code_dict
            freason = freason_dict[f_result['finish_reason']]
            self.text_finishin_reasons.append(freason)
            return {'prompt': prompt, 'response': f_result['output']}

        except Exception as e:
            _msg = f'Error Requesting : {str(e)}'
            GptModel.logger.error(_msg)
            raise Exception(_msg)

    def stream_request(self, prompt: str):
        """Send a streaming chat request; yield each content
        chunk as it arrives."""
        # 1) stash the user prompt in history
        self.inputs.append(prompt)
        self.messages.append(GptModel.format_input(prompt))

        try:
            # 2) fire off a streaming completion
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                stream=True
            )

            full_output = ""
            # 3) as chunks come in, yield them immediately
            for chunk in stream:
                delta = chunk.choices[0].delta
                # use getattr to safely pull out .content
                text = getattr(delta, "content", None) or ""
                if text:
                    full_output += text
                    yield text

            # 4) once done, record the full response
            self.outputs.append(full_output)
            self.messages.append(GptModel.format_output(full_output))
            self.request_count += 1

        except Exception as e:
            GptModel.logger.error(f"Streaming request error: {e}")
            raise Exception(f"Error during streaming request: {e}")

    def new_session(self):
        session_info = {'total_tokens': self.total_tokens,
                        'total_price': self.total_price,
                        'inputs': self.inputs,
                        'outputs': self.outputs,
                        'requests_info': self.requests_info,
                        'input_tokens': self.input_tokens,
                        'output_tokens': self.output_tokens,
                        'request_count': self.request_count}
        self.sessions_info.append(session_info)
        self.messages = [self.sys_msg]
        self.outputs = []
        self.inputs = []
        self.total_price = 0
        self.total_tokens = None
        self.input_tokens = None
        self.request_count = 0
        self.output_tokens = None
        self.requests_info = []
        GptModel.logger.info('Session Cleared!')

    @staticmethod
    def load_from_dict(info: dict):
        keys = ['model',
                'sys_msg',
                'max_context',
                'messages',
                'outputs',
                'inputs',
                'total_price',
                'total_tokens',
                'input_tokens',
                'request_count',
                'output_tokens',
                'requests_info',
                'sessions_info',
                'text_finishin_reasons'
                ]
        gpt_model = GptModel('gpt-4o-mini')
        for key in info.keys():
            if key not in keys:
                raise Exception(f"Error loading from dict: {key} not found.")
        fmt_sys_msg = {"role": "system", "content": info['sys_msg']}
        gpt_model.raw_sys_msg = info['sys_msg']
        gpt_model.from_dotenv = True
        gpt_model.ApiKey = dotenv_values('.env')['OPENAI_API_KEY']
        gpt_model.sys_msg = fmt_sys_msg
        gpt_model.window_token_limit = info['max_context']
        gpt_model.messages = info['messages']
        gpt_model.outputs = info['outputs']
        gpt_model.inputs = info['inputs']
        gpt_model.total_price = info['total_price']
        gpt_model.total_tokens = info['total_tokens']
        gpt_model.input_tokens = info['input_tokens']
        gpt_model.request_count = info['request_count']
        gpt_model.output_tokens = info['output_tokens']
        gpt_model.requests_info = info['requests_info']
        gpt_model.sessions_info = info['sessions_info']
        gpt_model.text_finishin_reasons = info['text_finishin_reasons']
        gpt_model.client = OpenAI(api_key=gpt_model.ApiKey)
        return gpt_model

    def serialize(self):
        d = {'model': self.model,
             'sys_msg': self.raw_sys_msg,
             'max_context': self.window_token_limit,
             'messages': self.messages,
             'outputs': self.outputs,
             'inputs': self.inputs,
             'total_price': self.total_price,
             'total_tokens': self.total_tokens,
             'input_tokens': self.input_tokens,
             'request_count': self.request_count,
             'output_tokens': self.output_tokens,
             'requests_info': self.requests_info,
             'sessions_info': self.sessions_info,
             'text_finishin_reasons': self.text_finishin_reasons
             }
        return d
