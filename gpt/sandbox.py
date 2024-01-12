from openai import OpenAI
import openai 
client = OpenAI()
openai.api_key = "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"
completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
    {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
  ]
)

print(completion.choices[0].message)