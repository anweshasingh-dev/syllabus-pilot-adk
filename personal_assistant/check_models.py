from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client()

for model in client.models.list():
    if "generateContent" in (model.supported_actions or []):
        print(model.name)
