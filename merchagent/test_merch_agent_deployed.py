from vertexai import agent_engines

PROJECT_ID = "energyagentai"
LOCATION = "us-central1"
RESOURCE_ID = "7774435613771563008"
#https://us-central1-aiplatform.googleapis.com/v1/projects/energyagentai/locations/us-central1/reasoningEngines/7774435613771563008:streamQuery?alt=sse
RESOURCE_NAME = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{RESOURCE_ID}"

adk_app = agent_engines.get(RESOURCE_NAME)

# Create or reuse session
session = adk_app.create_session(user_id="test-db")
print("Session created:", session)

# Track full state
full_state = {}

for event in adk_app.stream_query(
    user_id="test-db",
    session_id=session["id"],
    message="What products for young soccer fans who like soccer and hiking in Los Angeles?"
):
    # Merge state_delta into full_state
    if "state_delta" in event.get("actions", {}):
        for key, value in event["actions"]["state_delta"].items():
            full_state[key] = value

    # Optional: print content parts
    if "content" in event:
        for part in event["content"].get("parts", []):
            print("PART:", part)

# After stream completes, print accumulated state
print("Final state variables:", full_state)
