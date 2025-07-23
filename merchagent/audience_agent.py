import json
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from .config import Modelconfig
from google.adk.tools import ToolContext
from typing import Optional, Dict, List, Any
from vertexai.generative_models import GenerativeModel

def detect_specific_audiences(request: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Detect specific audiences from the 104 available audiences based on user query"""
    
    # Full list of 104 audiences
    AVAILABLE_AUDIENCES = [
    {"id": "urn:audience:hobbies_and_interests:health_and_beauty", "name": "Health And Beauty"},
    {"id": "urn:audience:hobbies_and_interests:adventuring", "name": "Adventuring"},
    {"id": "urn:audience:hobbies_and_interests:photography", "name": "Photography"},
    # {"id": "urn:audience:hobbies_and_interests:tattoos", "name": "Tattoos"},
    {"id": "urn:audience:hobbies_and_interests:meditation", "name": "Meditation"},
    {"id": "urn:audience:hobbies_and_interests:hockey", "name": "Hockey"},
    {"id": "urn:audience:hobbies_and_interests:american_football", "name": "American Football"},
    {"id": "urn:audience:hobbies_and_interests:martial_arts", "name": "Martial Arts"},
    {"id": "urn:audience:hobbies_and_interests:running", "name": "Running"},
    # {"id": "urn:audience:hobbies_and_interests:secret_unravelers", "name": "Secret Unravelers"},
    # {"id": "urn:audience:hobbies_and_interests:motorcycles", "name": "Motorcycles"},
    {"id": "urn:audience:hobbies_and_interests:jewellery", "name": "Jewellery"},
    {"id": "urn:audience:hobbies_and_interests:hiking", "name": "Hiking"},
    {"id": "urn:audience:hobbies_and_interests:watches", "name": "Watches"},
    # {"id": "urn:audience:hobbies_and_interests:spy_enthusiast", "name": "Spy Enthusiast"},
    # {"id": "urn:audience:hobbies_and_interests:arts_crafts", "name": "Arts Crafts"},
    {"id": "urn:audience:hobbies_and_interests:wrestling", "name": "Wrestling"},
    # {"id": "urn:audience:hobbies_and_interests:home_organization", "name": "Home Organization"},
    {"id": "urn:audience:hobbies_and_interests:sneakerheads", "name": "Sneakerheads"},
    {"id": "urn:audience:hobbies_and_interests:travel", "name": "Travel"},
    {"id": "urn:audience:hobbies_and_interests:golf", "name": "Golf"},
    {"id": "urn:audience:hobbies_and_interests:high_fashion", "name": "High Fashion"},
    {"id": "urn:audience:hobbies_and_interests:home_decor", "name": "Home Decor"},
    {"id": "urn:audience:hobbies_and_interests:street_fashion", "name": "Street Fashion"},
    {"id": "urn:audience:hobbies_and_interests:video_gamer", "name": "Video Gamer"},
    {"id": "urn:audience:hobbies_and_interests:tennis", "name": "Tennis"},
    {"id": "urn:audience:hobbies_and_interests:swimming", "name": "Swimming"},
    {"id": "urn:audience:hobbies_and_interests:automotive", "name": "Automotive"},
    {"id": "urn:audience:hobbies_and_interests:musician", "name": "Musician"},
    {"id": "urn:audience:hobbies_and_interests:perfume", "name": "Perfume"},
    {"id": "urn:audience:hobbies_and_interests:casual_escapists", "name": "Casual Escapists"},
    {"id": "urn:audience:hobbies_and_interests:racing", "name": "Racing"},
    {"id": "urn:audience:hobbies_and_interests:adrenaline_rushers", "name": "Adrenaline Rushers"},
    {"id": "urn:audience:hobbies_and_interests:soccer", "name": "Soccer"},
    {"id": "urn:audience:hobbies_and_interests:yoga", "name": "Yoga"},
    {"id": "urn:audience:hobbies_and_interests:baseball", "name": "Baseball"},
    {"id": "urn:audience:hobbies_and_interests:architecture", "name": "Architecture"},
    {"id": "urn:audience:hobbies_and_interests:wine_enthusiast", "name": "Wine Enthusiast"},
    {"id": "urn:audience:hobbies_and_interests:basketball", "name": "Basketball"},
    {"id": "urn:audience:hobbies_and_interests:outdoors", "name": "Outdoors"},
    {"id": "urn:audience:hobbies_and_interests:fishing", "name": "Fishing"},
    {"id": "urn:audience:hobbies_and_interests:dance", "name": "Dance"},
    {"id": "urn:audience:spending_habits:vintage_apparel", "name": "Vintage Apparel"},
    {"id": "urn:audience:spending_habits:technology_enthusiast", "name": "Technology Enthusiast"},
    {"id": "urn:audience:spending_habits:watch_collecting", "name": "Watch Collecting"},
    {"id": "urn:audience:spending_habits:boutique_hotels", "name": "Boutique Hotels"},
    {"id": "urn:audience:spending_habits:discount_shoppers", "name": "Discount Shoppers"},
    {"id": "urn:audience:spending_habits:gourmand_fine_dining", "name": "Gourmand Fine Dining"},
    {"id": "urn:audience:communities:aapi", "name": "AAPI"},
    {"id": "urn:audience:communities:latino", "name": "Latino"},
    {"id": "urn:audience:communities:lgbtq", "name": "LGBTQ"},
    {"id": "urn:audience:communities:black", "name": "Black"},
    # {"id": "urn:audience:global_issues:climate_activism", "name": "Climate Activism"},
    # {"id": "urn:audience:global_issues:gender_equality", "name": "Gender Equality"},
    # {"id": "urn:audience:global_issues:racial_justice", "name": "Racial Justice"},
    # {"id": "urn:audience:global_issues:education_issues", "name": "Education Issues"},
    # {"id": "urn:audience:global_issues:ocean_health", "name": "Ocean Health"},
    # {"id": "urn:audience:global_issues:foreign_affairs", "name": "Foreign Affairs"},
    # {"id": "urn:audience:global_issues:wealth_inequality", "name": "Wealth Inequality"},
    # {"id": "urn:audience:global_issues:animal_issues", "name": "Animal Issues"},
    # {"id": "urn:audience:global_issues:mental_health", "name": "Mental Health"},
    # {"id": "urn:audience:global_issues:sustainability", "name": "Sustainability"},
    # {"id": "urn:audience:global_issues:fair_wages", "name": "Fair Wages"},
    # {"id": "urn:audience:investing_interests:stocks_bonds", "name": "Stocks Bonds"},
    # {"id": "urn:audience:investing_interests:angel_start_up_investing", "name": "Angel Start Up Investing"},
    # {"id": "urn:audience:investing_interests:real_estate", "name": "Real Estate"},
    {"id": "urn:audience:investing_interests:nft_collectors", "name": "NFT Collectors"},
    {"id": "urn:audience:investing_interests:cryptocurrency_enthusiasts", "name": "Cryptocurrency Enthusiasts"},
    {"id": "urn:audience:investing_interests:art_collectibles", "name": "Art Collectibles"},
    # {"id": "urn:audience:leisure:political_junkie", "name": "Political Junkie"},
    {"id": "urn:audience:leisure:arts_culture", "name": "Arts Culture"},
    {"id": "urn:audience:leisure:foodie", "name": "Foodie"},
    {"id": "urn:audience:leisure:cooking", "name": "Cooking"},
    {"id": "urn:audience:leisure:museums", "name": "Museums"},
    {"id": "urn:audience:leisure:cinephile", "name": "Cinephile"},
    {"id": "urn:audience:leisure:music_festivals", "name": "Music Festivals"},
    {"id": "urn:audience:leisure:avid_reader", "name": "Avid Reader"},
    {"id": "urn:audience:leisure:exercising", "name": "Exercising"},
    {"id": "urn:audience:leisure:coffee", "name": "Coffee"},
    {"id": "urn:audience:leisure:news_junkie", "name": "News Junkie"},
    {"id": "urn:audience:life_stage:parents_with_young_children", "name": "Parents With Young Children"},
    {"id": "urn:audience:life_stage:engaged", "name": "Engaged"},
    {"id": "urn:audience:life_stage:single", "name": "Single"},
    {"id": "urn:audience:life_stage:retirement", "name": "Retirement"},
    # {"id": "urn:audience:lifestyle_preferences_beliefs:astrology", "name": "Astrology"},
    # {"id": "urn:audience:lifestyle_preferences_beliefs:organic_ingredients", "name": "Organic Ingredients"},
    # {"id": "urn:audience:lifestyle_preferences_beliefs:christianity", "name": "Christianity"},
    # {"id": "urn:audience:lifestyle_preferences_beliefs:healthy_eating", "name": "Healthy Eating"},
    # {"id": "urn:audience:lifestyle_preferences_beliefs:judaism", "name": "Judaism"},
    # {"id": "urn:audience:lifestyle_preferences_beliefs:veganism", "name": "Veganism"},
    # {"id": "urn:audience:lifestyle_preferences_beliefs:spirituality", "name": "Spirituality"},
    # {"id": "urn:audience:lifestyle_preferences_beliefs:islam", "name": "Islam"},
    # {"id": "urn:audience:political_preferences:politically_progressive", "name": "Politically Progressive"},
    # {"id": "urn:audience:political_preferences:politically_center", "name": "Politically Center"},
    # {"id": "urn:audience:political_preferences:politically_conservative", "name": "Politically Conservative"},
    {"id": "urn:audience:professional_area:business_professional", "name": "Business Professional"},
    {"id": "urn:audience:professional_area:hospitality_professional", "name": "Hospitality Professional"},
    {"id": "urn:audience:professional_area:medical_professional", "name": "Medical Professional"},
    {"id": "urn:audience:professional_area:advertising_design", "name": "Advertising Design"},
    {"id": "urn:audience:professional_area:technology_professional", "name": "Technology Professional"},
    {"id": "urn:audience:professional_area:marketing_professional", "name": "Marketing Professional"},
    {"id": "urn:audience:professional_area:retail_professional", "name": "Retail Professional"},
    {"id": "urn:audience:professional_area:finance_professional", "name": "Finance Professional"},
    {"id": "urn:audience:professional_area:sales_professional", "name": "Sales Professional"}
]
    
    # Create audience list for LLM
    audience_list = []
    for aud in AVAILABLE_AUDIENCES:
        audience_list.append(f'"{aud["name"]}"')
    
    audience_text = ", ".join(audience_list)
        
    prompt = f"""Analyze this user query and identify ALL specific audiences they mentioned or strongly implied or are similar/related to what user is asking for.

User query: "{request}"

Available audiences: {[aud["name"] for aud in AVAILABLE_AUDIENCES]}

Instructions:
- Look for explicit mentions (e.g., "gamers", "runners", "fashionistas")
- Include strongly implied audiences (e.g., "fitness gear" implies "Running", "Health And Beauty")
- Include related audiences (e.g., "sports" could be "American Football")
- Return multiple audiences if multiple interests are mentioned
- Return empty list if no specific interests are mentioned
- Be inclusive rather than restrictive
- Note soccer is American word for football. Include these similar audiences unless said by user not to
- user asks for job,occupation,profession etc return all the valid audience from urn:audience:professional_area to users query
- any kind of spending characters/money habits use urn:spending_habits audience



Examples:
- "products for gamers and sneaker lovers" → ["Video Gamer", "Sneakerheads"]
- "merch for fitness enthusiasts" → ["Running", "Health And Beauty", "Martial Arts"]
- "items for fashion-forward travelers" → ["High Fashion", "Street Fashion", "Travel"]
- "products for 25 year old men" → []

Return JSON: {{"audience_names": ["Name1", "Name2"]}}
"""
    

    model = GenerativeModel(Modelconfig.flash_model)
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        result = json.loads(response_text)
        detected_names = result.get("audience_names", [])
        
        # Map names to IDs
        detected_audiences = []
        name_to_audience = {aud["name"]: aud for aud in AVAILABLE_AUDIENCES}
        
        for name in detected_names:
            if name in name_to_audience:
                detected_audiences.append(name_to_audience[name])
        
        # Store in state
        if detected_audiences:
            audience_ids = [aud["id"] for aud in detected_audiences]
            tool_context.state['detected_audience_ids'] = audience_ids
            tool_context.state['detected_audience_names'] = [aud["name"] for aud in detected_audiences]
        else:
            tool_context.state['detected_audience_ids'] = []
            tool_context.state['detected_audience_names'] = []
        
        return {
            "success": True,
            "audiences_detected": len(detected_audiences),
            "audience_names": [aud["name"] for aud in detected_audiences],
            "audience_ids": [aud["id"] for aud in detected_audiences],
            "message": f"Detected {len(detected_audiences)} specific audiences" if detected_audiences else "No specific audiences mentioned"
        }
        
    except Exception as e:
        return {"error": f"Audience detection failed: {str(e)}"}

audience_detector_agent = Agent(
    name="AudienceDetectorAgent",
    model=Modelconfig.flash_model,
    instruction="""You detect specific audience interests from user queries.
    
    Use detect_specific_audiences to identify which audiences the user mentioned.
    Be thorough - look for explicit mentions and strong implications.
    Include multiple audiences when relevant.
    """,
    description="Detects specific audience interests from user queries",
    tools=[FunctionTool(detect_specific_audiences)]
)