from typing import TypeAlias, Union, List, Dict


HistoryData: TypeAlias = List[Dict[str, str]]
'''
e.g.
[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"},
    {"role": "assistant", "content": "The capital of France is Paris."}
]
'''
ChatsList: TypeAlias = List[Dict[str, Union[int, str]]]
'''
e.g.
[
    {"id": 1, "name": "Мой первый чат"},
    {"id": 2, "name": "Чат про питон"}
]
'''
