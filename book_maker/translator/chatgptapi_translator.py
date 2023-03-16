import time
from os import environ

import openai

from .base_translator import Base

PROMPT_ENV_MAP = {
    "user": "BBM_CHATGPTAPI_USER_MSG_TEMPLATE",
    "system": "BBM_CHATGPTAPI_SYS_MSG",
}


class ChatGPTAPI(Base):
    # DEFAULT_PROMPT = "Please help me to translate,`{text}` to {language}, please return only translated content not include the origin text. remain all html tag if it has."

    DEFAULT_PROMPT = "将以下文章翻译成中文，保留所有的 <p> 标签，不允许合并标签，如 <p>You</p><p>are</p><p>nice</p> 最终翻译成 <p>你</p><p>很</p><p>好</p>, 下面是需要翻译的文章：`{text}`"

    DEFAULT_SYSTEM_PROMPT = "下面我让你来充当翻译家，你的目标是把任何语言翻译成中文，请翻译时不要带翻译腔，而是要翻译得自然、流畅和地道，使用优美和高雅的表达方式。"
    
    def __init__(
        self,
        key,
        language,
        api_base=None,
        prompt_template=None,
        prompt_sys_msg=None,
        **kwargs,
    ):
        super().__init__(key, language)
        self.key_len = len(key.split(","))
        if api_base:
            openai.api_base = api_base
        self.prompt_template = (
            prompt_template
            or environ.get(PROMPT_ENV_MAP["user"])
            or self.DEFAULT_PROMPT
        )
        self.prompt_sys_msg = (
            prompt_sys_msg
            or environ.get(
                "OPENAI_API_SYS_MSG"
            )  # XXX: for backward compatability, deprecate soon
            or environ.get(PROMPT_ENV_MAP["system"])
            or self.DEFAULT_SYSTEM_PROMPT
        )

    def rotate_key(self):
        openai.api_key = next(self.keys)

    def get_translation(self, text):
        self.rotate_key()
        messages = []
        if self.prompt_sys_msg:
            messages.append(
                {"role": "system", "content": self.prompt_sys_msg.format(text=text, language=self.language)},
            )
        messages.append(
            {
                "role": "user",
                "content":text,
            }
        )

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        t_text = (
            completion["choices"][0]
            .get("message")
            .get("content")
            .encode("utf8")
            .decode()
        )
        return t_text

    def translate(self, text):
        # todo: Determine whether to print according to the cli option
        print(text)

        try:
            t_text = self.get_translation(text)
        except Exception as e:
            # todo: better sleep time? why sleep alawys about key_len
            # 1. openai server error or own network interruption, sleep for a fixed time
            # 2. an apikey has no money or reach limit, don’t sleep, just replace it with another apikey
            # 3. all apikey reach limit, then use current sleep
            sleep_time = int(60 / self.key_len)
            print(e, f"will sleep {sleep_time} seconds")
            time.sleep(sleep_time)

            t_text = self.get_translation(text)

        # todo: Determine whether to print according to the cli option
        print(t_text.strip())
        return t_text