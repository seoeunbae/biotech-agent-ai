import os
import sys
from google.genai import Client

print(f"GOOGLE_CLOUD_PROJECT: {os.environ.get('GOOGLE_CLOUD_PROJECT')}")
print(f"GOOGLE_CLOUD_LOCATION: {os.environ.get('GOOGLE_CLOUD_LOCATION')}")

# Try initializing WITHOUT arguments (as google_llm.py does)
try:
    client = Client()
    print("Client initialized successfully (default)")
except Exception as e:
    print(f"Client init failed (default): {e}")

# Try with vertexai=True (maybe via env var?)
try:
    # Is there an env var to force vertexai?
    client = Client(vertexai=True)
    print("Client initialized successfully (vertexai=True)")
except Exception as e:
    print(f"Client init failed (vertexai=True): {e}")

# Try explicit
project = os.environ.get('GOOGLE_CLOUD_PROJECT')
location = os.environ.get('GOOGLE_CLOUD_LOCATION')
if project and location:
    try:
        client = Client(vertexai=True, project=project, location=location)
        print("Client initialized successfully (explicit)")
    except Exception as e:
        print(f"Client init failed (explicit): {e}")
