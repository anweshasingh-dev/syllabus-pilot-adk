from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client()

for model in client.models.list():
    if "generateContent" in (model.supported_actions or []):
        print(model.name)