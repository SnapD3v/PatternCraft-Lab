from typing import Any, Dict, Type

import markdown
import re
from werkzeug.datastructures import ImmutableMultiDict

from .config import BaseModel


def markdown_process(md_text: str) -> str:
    result = markdown.markdown(
        md_text,
        extensions=[
            'extra',
            'codehilite',
            'toc',
            'nl2br',
            'fenced_code'
        ]
    )
    return result


def strip_markdown(text: str) -> str:
    # Убираем ссылки: [текст](ссылка)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Убираем картинки: ![alt](src)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # Убираем жирный и курсив: **text** или *text*
    text = re.sub(r'(\*\*|\*)(.*?)\1', r'\2', text)
    # Убираем заголовки: # Header
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    # Убираем инлайн-код: `code`
    text = re.sub(r'`([^`]*)`', r'\1', text)
    # Убираем code-блоки: ```код```
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Убираем цитаты: > quote
    text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)
    # Убираем списки: - item, * item, 1. item
    text = re.sub(r'^([-*+]|\d+\.)\s+', '', text, flags=re.MULTILINE)
    return text


def build_nested_update_auto_with_cast(
    form_data: ImmutableMultiDict[str, str],
    model: Type[BaseModel]
) -> Dict[str, Any]:
    nested: Dict[str, Any] = {}

    for field_name, field_info in model.model_fields.items():
        annotation = field_info.annotation

        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            nested_sub: Dict[str, Any] = {}

            for sub_field in annotation.model_fields.keys():
                if sub_field in form_data:
                    nested_sub[sub_field] = form_data[sub_field]

            if nested_sub:
                nested[field_name] = annotation(**nested_sub)

    return nested
