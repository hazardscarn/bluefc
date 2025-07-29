# debug_agent_session.py - Test both recommendation and customization in same session
from vertexai import agent_engines

PROJECT_ID = "energyagentai"
LOCATION = "us-central1"
RESOURCE_ID = "7774435613771563008"
RESOURCE_NAME = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{RESOURCE_ID}"

print("=== AGENT ENGINE SESSION DEBUG TEST ===")
print(f"Resource: {RESOURCE_NAME}")
print()

# Connect to agent
adk_app = agent_engines.get(RESOURCE_NAME)
user_id="test-debug"
# Create session
session = adk_app.create_session(user_id="test-debug")
print(f"✅ Session created: {session['id']}")
print(f"   User ID: {user_id}")
print()

# ============================================================================
# STEP 1: PRODUCT RECOMMENDATION
# ============================================================================
print("🎯 STEP 1: PRODUCT RECOMMENDATION")
print("=" * 50)

recommendation_query = "What products for young soccer fans who like soccer and hiking in Los Angeles?"
print(f"Query: {recommendation_query}")
print()

# Track state for recommendation
full_state = {}
event_count = 0

print("📡 Streaming recommendation...")
for event in adk_app.stream_query(
    user_id="test-debug",
    session_id=session["id"],
    message=recommendation_query
):
    event_count += 1
    
    # Merge state_delta into full_state
    if "state_delta" in event.get("actions", {}):
        state_delta = event["actions"]["state_delta"]
        if state_delta:
            print(f"  📝 Event {event_count}: State delta keys: {list(state_delta.keys())}")
            for key, value in state_delta.items():
                full_state[key] = value
                if key in ["persona_name", "detected_signals", "detected_audience_names"]:
                    print(f"     ✨ {key}: {value}")

    # Print any text responses
    if "content" in event:
        for part in event["content"].get("parts", []):
            if "text" in part:
                text = part["text"][:100] + "..." if len(part["text"]) > 100 else part["text"]
                print(f"  💬 Agent response: {text}")

print()
print("📊 RECOMMENDATION RESULTS:")
print(f"   Total events: {event_count}")
print(f"   Final state keys: {list(full_state.keys())}")

# Check key context data
if full_state.get("persona_name"):
    print(f"   ✅ Persona: {full_state['persona_name']}")
else:
    print("   ❌ No persona found")

if full_state.get("detected_audience_names"):
    print(f"   ✅ Audiences: {full_state['detected_audience_names'][:3]}")
else:
    print("   ❌ No audiences found")

if full_state.get("recommendations"):
    print(f"   ✅ Products: {len(full_state['recommendations'])} recommendations")
    # Show first product ID for customization test
    if full_state["recommendations"]:
        first_product = full_state["recommendations"][0]
        product_id = first_product.get("product_id", "unknown")
        print(f"   🎯 First product ID: {product_id}")
else:
    print("   ❌ No product recommendations")

print()
print("=" * 50)

# ============================================================================
# STEP 2: PRODUCT CUSTOMIZATION (same session)
# ============================================================================
print("🎨 STEP 2: PRODUCT CUSTOMIZATION")
print("=" * 50)

# Use first recommended product for customization
if full_state.get("recommendations") and full_state["recommendations"]:
    product_to_customize = full_state["recommendations"][0].get("product_id", "prod_394")
else:
    product_to_customize = "prod_394"  # Fallback

customization_query = f'Customize product_id: "{product_to_customize}" with the following instructions: Customize the product to make it more appealing to the target audience'
print(f"Query: {customization_query}")
print(f"Product ID: {product_to_customize}")
print()

# ============================================================================
# CHECK FULL SESSION STATE BEFORE CUSTOMIZATION
# ============================================================================
print("🔍 FULL SESSION STATE CHECK (Before Customization):")
print("-" * 60)
print(f"Session ID: {session['id']}")
print(f"User ID: {user_id}")
print()

print("📊 ALL AVAILABLE STATE VARIABLES:")
if full_state:
    for key, value in full_state.items():
        value_preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
        print(f"   {key}: {type(value).__name__} = {value_preview}")
    
    print()
    print("🎯 KEY CONTEXT VARIABLES:")
    
    # Persona info
    if full_state.get("persona_name"):
        print(f"   ✅ persona_name: {full_state['persona_name']}")
    if full_state.get("persona_description"):
        desc = full_state['persona_description'][:150] + "..." if len(full_state['persona_description']) > 150 else full_state['persona_description']
        print(f"   ✅ persona_description: {desc}")
    
    # Audience info
    if full_state.get("detected_signals"):
        print(f"   ✅ detected_signals: {full_state['detected_signals']}")
    if full_state.get("detected_audience_names"):
        print(f"   ✅ detected_audience_names: {full_state['detected_audience_names']}")
    if full_state.get("detected_audience_ids"):
        print(f"   ✅ detected_audience_ids: {len(full_state['detected_audience_ids'])} IDs")
    
    # Cultural insights
    if full_state.get("brand_insight"):
        print(f"   ✅ brand_insight: Available ({len(full_state['brand_insight'])} chars)")
    if full_state.get("movie_insight"):
        print(f"   ✅ movie_insight: Available ({len(full_state['movie_insight'])} chars)")
    if full_state.get("tag_insight"):
        print(f"   ✅ tag_insight: Available ({len(full_state['tag_insight'])} chars)")
    
    # Product recommendations
    if full_state.get("recommendations"):
        print(f"   ✅ recommendations: {len(full_state['recommendations'])} products")
        for i, rec in enumerate(full_state['recommendations'][:3]):  # Show first 3
            print(f"      Product {i+1}: {rec.get('name', 'Unknown')} (ID: {rec.get('product_id', 'Unknown')})")
    
    # Profile data
    if full_state.get("audience_profile"):
        print(f"   ✅ audience_profile: Available")
    if full_state.get("cultural_values"):
        print(f"   ✅ cultural_values: Available")
    if full_state.get("purchase_motivations"):
        print(f"   ✅ purchase_motivations: {len(full_state['purchase_motivations'])} items")
    
else:
    print("   ❌ NO STATE VARIABLES FOUND!")

print()
print("-" * 60)
print("🚀 Now sending customization query with above context...")
print()

# Track customization events
customization_state = {}
customization_events = 0

print("📡 Streaming customization...")
for event in adk_app.stream_query(
    user_id="test-debug",
    session_id=session["id"],  # Same session!
    message=customization_query
):
    customization_events += 1
    print(f"  📨 Customization Event {customization_events}:")
    
    # Check for state changes
    if "state_delta" in event.get("actions", {}):
        state_delta = event["actions"]["state_delta"]
        if state_delta:
            print(f"     📝 State delta keys: {list(state_delta.keys())}")
            for key, value in state_delta.items():
                customization_state[key] = value
                if key in ["customized_image_url", "customization_reasoning", "original_product"]:
                    print(f"        ✨ {key}: {type(value)} - {str(value)[:100]}...")
        else:
            print(f"     📝 No state delta")
    
    # Print agent responses
    if "content" in event:
        for part in event["content"].get("parts", []):
            if "text" in part:
                print(f"     💬 Agent says: {part['text']}")

print()
print("📊 CUSTOMIZATION RESULTS:")
print(f"   Total events: {customization_events}")
print(f"   Customization state keys: {list(customization_state.keys())}")

# Check customization results
if customization_state.get("customized_image_url"):
    print(f"   ✅ Customized image: {customization_state['customized_image_url']}")
else:
    print("   ❌ No customized image URL")

if customization_state.get("customization_reasoning"):
    reasoning = customization_state['customization_reasoning'][:200] + "..." if len(customization_state.get('customization_reasoning', '')) > 200 else customization_state.get('customization_reasoning', '')
    print(f"   ✅ Reasoning: {reasoning}")
else:
    print("   ❌ No customization reasoning")

if customization_state.get("original_product"):
    original = customization_state['original_product']
    print(f"   ✅ Original product: {original.get('name', 'Unknown')} (ID: {original.get('product_id', 'Unknown')})")
else:
    print("   ❌ No original product data")

print()
print("=" * 50)
print("🏁 SUMMARY")
print("=" * 50)
print(f"Session ID used: {session['id']}")
print(f"Recommendation successful: {'✅' if full_state.get('recommendations') else '❌'}")
print(f"Customization successful: {'✅' if customization_state.get('customized_image_url') else '❌'}")

if not customization_state.get("customized_image_url"):
    print()
    print("🔍 DEBUGGING INFO:")
    print("Possible reasons customization failed:")
    print("1. Agent couldn't find the product ID in its database")
    print("2. Customization tool requires specific context that's missing")
    print("3. Session context not properly maintained")
    print("4. Tool may have temporary issues")
    
    if full_state.get("persona_name"):
        print(f"   ✅ Persona context available: {full_state['persona_name']}")
    else:
        print("   ❌ No persona context available")
    
    if full_state.get("detected_audience_names"):
        print(f"   ✅ Audience context available: {len(full_state['detected_audience_names'])} audiences")
    else:
        print("   ❌ No audience context available")

print()
print("🔬 Try running this same sequence in ADK web to compare results!")
print("=" * 50)