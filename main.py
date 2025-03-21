import requests
import json

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer <OPENROUTER_API_KEY>",  # Put in your own API key
    "Content-Type": "application/json",
}
payload = {
    # anthropic/claude-3.7-sonnet
    # deepseek/deepseek-r1
    # google/gemini-2.0-flash-thinking-exp:free
    # openai/{o3-mini; o3-mini-high; o1; o1-mini}

    "model": "anthropic/claude-3.7-sonnet",
    "messages": [
        {
            "role": "system",
            "content": "You're a professional programmer.",
        },
        {
            "role": "user",
            "content": [
                {"type": "text", 
                 "text": "What's the most efficient algorithm for sorting a large dataset?"
                },
                # {
                #     "type": "image_url",
                #     "image_url": {
                #         ""
                #     },
                # },
            ],
        },
    ],
    "reasoning": {
        # Optional: Default is false. All models support this. Set to true to exclude reasoning tokens from response
        "exclude": False,
        # Specific token limit (Anthropic-style)
        "max_tokens": 2000,
        # # Specific token limit. Can be "high(80% of max_tokens)", "medium(50% of max_tokens)", or "low(20% of max_tokens)" (OpenAI-style)
        # "effort": "high",
    },
    # Default: False. Set to true to stream response
    "stream": False,
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
print("<think>")
print(response.json()["choices"][0]["message"]["reasoning"])
print("</think>")
print(response.json()["choices"][0]["message"]["content"])

# # Streaming mode. Dynamic real-time response output
# buffer = ""
# with requests.post(url, headers=headers, json=payload, stream=True) as r:
#   for chunk in r.iter_content(chunk_size=1024, decode_unicode=True):
#     buffer += chunk
#     while True:
#       try:
#         # Find the next complete SSE line
#         line_end = buffer.find('\n')
#         if line_end == -1:
#           break
#         line = buffer[:line_end].strip()
#         buffer = buffer[line_end + 1:]
#         if line.startswith('data: '):
#           data = line[6:]
#           if data == '[DONE]':
#             break
#           try:
#             data_obj = json.loads(data)
#             content = data_obj["choices"][0]["delta"].get("content")
#             if content:
#               print(content, end="", flush=True)
#           except json.JSONDecodeError:
#             pass
#       except Exception:
#         break
