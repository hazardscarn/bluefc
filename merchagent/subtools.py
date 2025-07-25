import requests
import json
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import os
import logging
from google.adk.tools import ToolContext
from datetime import datetime
from src.qloo import QlooAPIClient, QlooSignals, QlooAudience
from .config import SecretConfig

load_dotenv()

# Initialize Qloo API Client with Secret Manager
qloo_api_key = SecretConfig.get_qloo_api_key()
client = QlooAPIClient(api_key=qloo_api_key)

# ##Initiate Qloo API Client
# client = QlooAPIClient(api_key=os.getenv("QLOO_API_KEY"))


# subtools.py - Update convert_and_create_signals to include audience IDs
def convert_and_create_signals(tool_context: ToolContext) -> Dict[str, Any]:
    """Convert detected signals and call create_qloo_signals"""
    
    # Get detected signals from state
    detected = tool_context.state.get('detected_signals')
    if not detected:
        return {"error": "No signals detected"}
    
    # Get detected audiences (if any)
    audience_ids = tool_context.state.get('detected_audience_ids', [])
    
    # Convert to Qloo format - handle multiple values
    demographics = {}
    
    # Handle multiple age ranges - only add if not empty
    if detected.get('age') and len(detected['age']) > 0:
        demographics['age'] = ','.join(detected['age'])
    
    # Handle multiple genders - only add if not empty
    if detected.get('gender') and len(detected['gender']) > 0:
        demographics['gender'] = ','.join(detected['gender'])
    
    location = {}
    # Handle multiple locations - only add if not empty
    if detected.get('location') and len(detected['location']) > 0:
        location['query'] = ','.join(detected['location'])
    
    try:
        # Convert to JSON strings as required by create_qloo_signals
        demographics_json = json.dumps(demographics) if demographics else "{}"
        location_json = json.dumps(location) if location else "{}"

        # Call create_qloo_signals with audience support
        result = create_qloo_signals(
            demographics=demographics_json,
            location=location_json,
            audience_ids=audience_ids  # Pass audience IDs
        )

        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create QlooSignals object"
        }


def create_qloo_signals(
    demographics: str, 
    location: str,
    audience_ids: List[str] = None  # Add audience_ids parameter
) -> Dict[str, Any]:
    """
    Creates QlooSignals object with demographics, location, and audiences.
    """
    if not client:
        return {
            "success": False,
            "error": "Qloo client not available. Check QLOO_API_KEY configuration.",
            "message": "Failed to create QlooSignals - client not initialized"
        }
    
    try:
        # Parse input parameters
        demo_dict = json.loads(demographics) if demographics else {}
        location_dict = json.loads(location) if location else {}
        
        # Create QlooSignals object with all parameters
        signals = QlooSignals(
            demographics=demo_dict if demo_dict else None,
            location=location_dict if location_dict else None,
            audience_ids=audience_ids if audience_ids else None,  # Include audience IDs
            entity_queries=None
        )
        
        return {
            "success": True,
            "signals_created": True,
            "demographics_provided": bool(demo_dict),
            "location_provided": bool(location_dict),
            "audience_ids_provided": bool(audience_ids),
            "audience_count": len(audience_ids) if audience_ids else 0,
            "qloo_signal": signals,
            "demographics": demo_dict,
            "location": location_dict,
            "audience_ids": audience_ids or [],
            "message": "QlooSignals object created successfully",
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create QlooSignals object"
        }


def get_first_available(obj, *keys):
    """Get first available key from object"""
    for key in keys:
        if key in obj:
            return obj[key]
    return None

def get_entity_movie_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None,limit=3) -> str:
    """
    Get movie insights for any signals and or audience ID list passed.
    
    :param signals: Optional QlooSignals object containing signals for the query
    :param audience_ids: Optional list of audience IDs to filter results
    :return: Formatted string containing movie insights
    """
    insights = client.get_entity_insights(
        audience_ids=audience_ids or [],
        entity_type="movie",
        signals=signals,
        limit=limit
    )
    
    entities = insights.get('results', {}).get('entities', [])
    postman_url = insights.get('postman_url')

    if not entities:
        return "No movie results found."
    
    # Build formatted string result
    result = [f"""Top {limit} movies liked by the audience\n
              """]
    result.append("")

    # Process each movie entity
    for i, entity in enumerate(entities, 1):
        
        # Add movie header for multiple movies
        if len(entities) > 1:
            result.append(f"--- MOVIE RANK {i} ---")
        
        # Basic movie information
        result.append(f"MOVIE Name: {entity['name']}\n")
        # result.append(f"   Entity ID: {entity['entity_id']}")
        # Properties section
        props = entity.get('properties', {})
        
        # Release information
        # if 'release_year' in props:
        #     result.append(f"   Release Year: {props['release_year']}")
        # if 'release_date' in props:
        #     result.append(f"   Release Date: {props['release_date']}")
        
        # # Duration
        # if 'duration' in props:
        #     result.append(f"   Duration: {props['duration']} minutes")
        
        # Rating
        if 'content_rating' in props:
            result.append(f"Content Rating: {props['content_rating']}\n")
        
        # Description
        if 'description' in props:
            description = props['description']
            result.append(f"Plot: {description}\n")

        # Affinity and popularity - handle different possible locations
        affinity = 0
        if 'query' in entity and 'affinity' in entity['query']:
            affinity = entity['query']['affinity']
        elif 'affinity_score' in entity:
            affinity = entity['affinity_score']
        elif 'affinity' in entity:
            affinity = entity['affinity']
        
        popularity = entity.get('popularity', 0)
        result.append(f"Affinity: {affinity:.3f}\n")
        # result.append(f"   Popularity: {popularity:.3f}")


        # # Production details
        # if 'production_companies' in props and props['production_companies']:
        #     companies = props['production_companies'][:3]
        #     result.append(f"   Production: {', '.join(companies)}")
        
        # # Filming location
        # if 'filming_location' in props:
        #     result.append(f"   Filmed in: {props['filming_location']}")
        
        # # Release countries
        # if 'release_country' in props and props['release_country']:
        #     countries = props['release_country'][:3]
        #     result.append(f"   Released in: {', '.join(countries)}")
        
        # # Image
        # if 'image' in props and 'url' in props['image']:
        #     result.append(f"   Image: {props['image']['url']}")
        
        
        # Add spacing between movies
        if i < len(entities):
            result.append("")
    
    # Postman URL (only show once at the end)
    # if postman_url:
    #     result.append("")
    #     result.append(f"Postman URL: {postman_url}")
    #     result.append("   " + "="*60)
    
    return "\n".join(result)


def get_entity_brand_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None,limit=3) -> str:
    """
    Get brand insights for any signals and/or audience ID list passed.
    
    :param signals: Optional QlooSignals object containing signals for the query
    :param audience_ids: Optional list of audience IDs to filter results
    :return: Formatted string containing brand insights
    """
    insights = client.get_entity_insights(
        audience_ids=audience_ids or [],
        entity_type="brand",
        signals=signals,
        limit=limit
    )
    
    entities = insights.get('results', {}).get('entities', [])
    postman_url = insights.get('postman_url')

    if not entities:
        return "No brand results found."
    
    # Build formatted string result
    result = [f"""Top {limit} brands liked by the audience\n"""]
    result.append("")

    # Process each brand entity
    for i, entity in enumerate(entities, 1):
        
        # Add brand header for multiple brands
        if len(entities) > 1:
            result.append(f"--- BRAND Rank {i} ---\n")
        
        # Basic brand information
        result.append(f"BRAND Name: {entity['name']}\n")
        # result.append(f"   Entity ID: {entity['entity_id']}")
        # Properties section
        props = entity.get('properties', {})
        
        # Brand description
        if 'short_description' in props:
            result.append(f"Brand Description: {props['short_description']}\n")
        
        # Affinity and popularity - handle different possible locations
        affinity = 0
        if 'query' in entity and 'affinity' in entity['query']:
            affinity = entity['query']['affinity']
        elif 'affinity_score' in entity:
            affinity = entity['affinity_score']
        elif 'affinity' in entity:
            affinity = entity['affinity']
        
        result.append(f"   Affinity: {affinity:.3f}\n")
        
        # # Audience Growth
        # growth = 0
        # if 'query' in entity and 'measurements' in entity['query']:
        #     growth = entity['query']['measurements'].get('audience_growth', 0)
        
        # if growth > 0:
        #     growth_indicator = "(up)"
        # elif growth < 0:
        #     growth_indicator = "(down)"
        # else:
        #     growth_indicator = "(flat)"
        
        # result.append(f"   Audience Growth: {growth:.2f} {growth_indicator}")
        

        
        # # Image URL if available
        # if 'image' in props and 'url' in props['image']:
        #     result.append(f"   Image: {props['image']['url']}")
        
        # # External data (if available)
        # if 'external' in entity:
        #     for platform, data in entity['external'].items():
        #         if data and isinstance(data, list) and len(data) > 0:
        #             platform_data = data[0]
        #             result.append(f"   {platform.title()}: {platform_data.get('url', 'Available')}")
        
        # Add spacing between brands
        if i < len(entities):
            result.append("")
    
    # Postman URL (only show once at the end)
    # if postman_url:
    #     result.append("")
    #     result.append(f"Postman URL: {postman_url}")
    #     result.append("   " + "="*60)
    
    return "\n".join(result)


def get_entity_artist_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None,limit=3) -> str:
    """
    Get artist insights for any signals and/or audience ID list passed.
    
    :param signals: Optional QlooSignals object containing signals for the query
    :param audience_ids: Optional list of audience IDs to filter results
    :return: Formatted string containing artist insights
    """
    insights = client.get_entity_insights(
        audience_ids=audience_ids or [],
        entity_type="artist",
        signals=signals,
        limit=3
    )
    
    entities = insights.get('results', {}).get('entities', [])
    postman_url = insights.get('postman_url')

    if not entities:
        return "No artist results found."
    
    # Build formatted string result
    result = [f"""Top {limit} artists/musicians audience likes. You can use these insights to understand the taste of music of the audience"""]
    result.append("\n")

    # Process each artist entity
    for i, entity in enumerate(entities, 1):
        
        # Add artist header for multiple artists
        if len(entities) > 1:
            result.append(f"--- ARTIST Rank {i} ---")
        
        # Basic artist information
        result.append(f"ARTIST Name: {entity['name']}\n")
        # result.append(f"   Entity ID: {entity['entity_id']}")
        props = entity.get('properties', {})
        
        descriptions = props.get('short_descriptions') or props.get('short_description')
        if descriptions:
            if isinstance(descriptions, list) and descriptions:
                desc = descriptions[0]
            else:
                desc = descriptions            
            description_text = desc.get('value') if isinstance(desc, dict) else desc
            if description_text:
                result.append(f"Description: {description_text}\n")
        
        # Affinity and popularity - handle different possible locations
        affinity = 0
        if 'query' in entity and 'affinity' in entity['query']:
            affinity = entity['query']['affinity']
        elif 'affinity_score' in entity:
            affinity = entity['affinity_score']
        elif 'affinity' in entity:
            affinity = entity['affinity']
        
        result.append(f"   Affinity: {affinity:.3f}\n")
        
        # # Audience Growth
        # growth = 0
        # if 'query' in entity and 'measurements' in entity['query']:
        #     growth = entity['query']['measurements'].get('audience_growth', 0)
        
        # if growth > 0:
        #     growth_indicator = "(up)"
        # elif growth < 0:
        #     growth_indicator = "(down)"
        # else:
        #     growth_indicator = "(flat)"
        
        # result.append(f"   Audience Growth: {growth:.2f} {growth_indicator}")
        

        
        # # Birth info
        # if 'date_of_birth' in props:
        #     result.append(f"   Born: {props['date_of_birth']}")
        # if 'place_of_birth' in props:
        #     result.append(f"   Birthplace: {props['place_of_birth']}")
        
        # # Alternative names
        # if 'akas' in props and props['akas']:
        #     akas = [aka.get('value', aka) for aka in props['akas'][:3] if aka]
        #     result.append(f"   Also known as: {', '.join(akas)}")
        
        # # Image
        # if 'image' in props and 'url' in props['image']:
        #     result.append(f"   Image: {props['image']['url']}")
        
        # External platforms
        if 'external' in entity:
            for platform, data in entity['external'].items():
                if data and isinstance(data, list) and len(data) > 0:
                    platform_data = data[0]
                    if platform == 'spotify':
                        followers = platform_data.get('followers', 'N/A')
                        listeners = platform_data.get('monthly_listeners', 'N/A')
                        result.append(f"Popularity in Spotify: {followers} followers, {listeners} monthly listeners\n")
                    # else:
                    #     result.append(f"   {platform.title()}: Available")
        
        # Add spacing between artists
        if i < len(entities):
            result.append("")
    
    # Postman URL (only show once at the end)
    # if postman_url:
    #     result.append("")
    #     result.append(f"Postman URL: {postman_url}")
    #     result.append("   " + "="*60)
    
    return "\n".join(result)


def get_entity_place_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None,limit=3) -> str:
    """
    Get place insights for any signals and/or audience ID list passed.
    
    :param signals: Optional QlooSignals object containing signals for the query
    :param audience_ids: Optional list of audience IDs to filter results
    :return: Formatted string containing place insights
    """
    insights = client.get_entity_insights(
        audience_ids=audience_ids or [],
        entity_type="place",
        signals=signals,
        limit=limit
    )
    
    entities = insights.get('results', {}).get('entities', [])
    postman_url = insights.get('postman_url')

    if not entities:
        return "No place results found."
    
    # Build formatted string result
    result = [f"""Top {limit} Places the Audience likes\n"""]
    result.append("")

    # Process each place entity
    for i, entity in enumerate(entities, 1):
        
        # Add place header for multiple places
        if len(entities) > 1:
            result.append(f"--- PLACE Rank {i} ---")
        
        # Basic place information
        result.append(f"PLACE Name: {entity['name']}\n")
        # result.append(f"   Entity ID: {entity['entity_id']}")
        
        # Affinity and popularity - handle different possible locations
        affinity = 0
        if 'query' in entity and 'affinity' in entity['query']:
            affinity = entity['query']['affinity']
        elif 'affinity_score' in entity:
            affinity = entity['affinity_score']
        elif 'affinity' in entity:
            affinity = entity['affinity']
        
        result.append(f"   Affinity: {affinity:.3f}\n")
        
        # # Audience Growth
        # growth = 0
        # if 'query' in entity and 'measurements' in entity['query']:
        #     growth = entity['query']['measurements'].get('audience_growth', 0)
        
        # if growth > 0:
        #     growth_indicator = "(up)"
        # elif growth < 0:
        #     growth_indicator = "(down)"
        # else:
        #     growth_indicator = "(flat)"
        
        # result.append(f"   Audience Growth: {growth:.2f} {growth_indicator}")
        
        props = entity.get('properties', {})
        
        # Address
        # if 'address' in props:
        #     result.append(f"   Address: {props['address']}")
        
        # Business details
        if 'business_rating' in props:
            result.append(f"   Business Rating: {props['business_rating']}/5.0\n")
        
        # if 'phone' in props:
        #     result.append(f"   Phone: {props['phone']}")
        
        # if 'website' in props:
        #     result.append(f"   Website: {props['website']}")
        
        # Neighborhood/Location
        if 'neighborhood' in props:
            result.append(f"   Neighborhood: {props['neighborhood']}\n")
        
        # # Status
        # if 'is_closed' in props:
        #     status = "Closed" if props['is_closed'] else "Open"
        #     result.append(f"   Status: {status}")
        
        # Keywords/Popular terms
        if 'keywords' in props and props['keywords']:
            top_keywords = [kw.get('name', str(kw)) for kw in props['keywords'][:5]]
            result.append(f"   Keywords: {', '.join(top_keywords)}\n")
        
        # # Coordinates
        # if 'location' in entity:
        #     loc = entity['location']
        #     lat = loc.get('lat', 'N/A')
        #     lon = loc.get('lon', 'N/A')
        #     result.append(f"   Coordinates: {lat}, {lon}")
        
        # Add spacing between places
        if i < len(entities):
            result.append("")
    
    # Postman URL (only show once at the end)
    # if postman_url:
    #     result.append("")
    #     result.append(f"Postman URL: {postman_url}")
    #     result.append("   " + "="*60)
    
    return "\n".join(result)


def get_entity_people_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None,limit=3) -> str:
    """
    Get people insights for any signals and/or audience ID list passed.
    
    :param signals: Optional QlooSignals object containing signals for the query
    :param audience_ids: Optional list of audience IDs to filter results
    :return: Formatted string containing people insights
    """
    insights = client.get_entity_insights(
        audience_ids=audience_ids or [],
        entity_type="people",
        signals=signals,
        limit=limit
    )
    
    entities = insights.get('results', {}).get('entities', [])
    postman_url = insights.get('postman_url')

    if not entities:
        return "No people results found."
    
    # Build formatted string result
    result = [f"""Top {limit} people liked by the audience. You can use these insights to understand the personalities or public figures that resonate with your audience\n"""]
    result.append("")

    # Process each people entity
    for i, entity in enumerate(entities, 1):
        
        # Add people header for multiple people
        if len(entities) > 1:
            result.append(f"--- PERSON Rank {i} ---")
        
        # Basic people information
        result.append(f"PERSON Name: {entity['name']}")
        # result.append(f"   Entity ID: {entity['entity_id']}")
        
        # Affinity and popularity - handle different possible locations
        affinity = 0
        if 'query' in entity and 'affinity' in entity['query']:
            affinity = entity['query']['affinity']
        elif 'affinity_score' in entity:
            affinity = entity['affinity_score']
        elif 'affinity' in entity:
            affinity = entity['affinity']
        
        result.append(f"   Affinity: {affinity:.3f}")
        
        # # Audience Growth
        # growth = 0
        # if 'query' in entity and 'measurements' in entity['query']:
        #     growth = entity['query']['measurements'].get('audience_growth', 0)
        
        # if growth > 0:
        #     growth_indicator = "(up)"
        # elif growth < 0:
        #     growth_indicator = "(down)"
        # else:
        #     growth_indicator = "(flat)"
        
        # result.append(f"   Audience Growth: {growth:.2f} {growth_indicator}")
        
        props = entity.get('properties', {})
        
        # # Personal info
        # if 'date_of_birth' in props:
        #     result.append(f"   Born: {props['date_of_birth']}")
        
        if 'gender' in props and props['gender']:
            gender = props['gender'][0] if isinstance(props['gender'], list) else props['gender']
            result.append(f"   Gender: {gender}\n")
        
        # if 'citizenship' in props and props['citizenship']:
        #     citizenship = props['citizenship'][0] if isinstance(props['citizenship'], list) else props['citizenship']
        #     result.append(f"   Citizenship: {citizenship}")
        
        # Professional info
        if 'instrument' in props and props['instrument']:
            instruments = props['instrument'][:3] if isinstance(props['instrument'], list) else [props['instrument']]
            result.append(f"   Instruments: {', '.join(instruments)}\n")
        
        # if 'work_period_start' in props:
        #     result.append(f"   Career Started: {props['work_period_start']}")
        
        # Awards
        if 'award_received' in props and props['award_received']:
            awards = props['award_received'][:3] if isinstance(props['award_received'], list) else [props['award_received']]
            result.append(f"   Awards: {', '.join(awards)}\n")
        
        # Description
        if 'short_descriptions' in props and props['short_descriptions']:
            description = props['short_descriptions'][0]
            if isinstance(description, dict) and 'value' in description:
                result.append(f"   Description: {description['value']}\n")
            elif isinstance(description, str):
                result.append(f"   Description: {description}\n")
        
        # # Alternative names
        # if 'akas' in props and props['akas']:
        #     akas = [aka.get('value', str(aka)) for aka in props['akas'][:3] if aka]
        #     result.append(f"   Also known as: {', '.join(akas)}")
        
        # # Website
        # if 'official_website' in props and props['official_website']:
        #     website = props['official_website'][0] if isinstance(props['official_website'], list) else props['official_website']
        #     result.append(f"   Website: {website}")
        
        # # Image
        # if 'image' in props and 'url' in props['image']:
        #     result.append(f"   Image: {props['image']['url']}")
        
        # Add spacing between people
        if i < len(entities):
            result.append("")
    
    # # Postman URL (only show once at the end)
    # if postman_url:
    #     result.append("")
    #     result.append(f"Postman URL: {postman_url}")
    #     result.append("   " + "="*60)
    
    return "\n".join(result)


def get_entity_tv_show_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None,limit=3) -> str:
    """
    Get TV show insights for any signals and/or audience ID list passed.
    
    :param signals: Optional QlooSignals object containing signals for the query
    :param audience_ids: Optional list of audience IDs to filter results
    :return: Formatted string containing TV show insights
    """
    insights = client.get_entity_insights(
        audience_ids=audience_ids or [],
        entity_type="tv_show",
        signals=signals,
        limit=limit
    )
    
    entities = insights.get('results', {}).get('entities', [])
    postman_url = insights.get('postman_url')

    if not entities:
        return "No TV show results found."
    
    # Build formatted string result
    result = [f"""Top {limit} TV shows liked by the audience\n"""]
    result.append("")

    # Process each TV show entity
    for i, entity in enumerate(entities, 1):
        
        # Add TV show header for multiple TV shows
        if len(entities) > 1:
            result.append(f"--- TV SHOW Rank {i} ---")
        
        # Basic TV show information
        result.append(f"TV SHOW Name: {entity['name']}")
        # result.append(f"   Entity ID: {entity['entity_id']}")
        
        # Affinity and popularity - handle different possible locations
        affinity = 0
        if 'query' in entity and 'affinity' in entity['query']:
            affinity = entity['query']['affinity']
        elif 'affinity_score' in entity:
            affinity = entity['affinity_score']
        elif 'affinity' in entity:
            affinity = entity['affinity']
        
        result.append(f"   Affinity: {affinity:.3f}")
        
        # # Audience Growth
        # growth = 0
        # if 'query' in entity and 'measurements' in entity['query']:
        #     growth = entity['query']['measurements'].get('audience_growth', 0)
        
        # if growth > 0:
        #     growth_indicator = "(up)"
        # elif growth < 0:
        #     growth_indicator = "(down)"
        # else:
        #     growth_indicator = "(flat)"
        
        # result.append(f"   Audience Growth: {growth:.2f} {growth_indicator}")
        
        props = entity.get('properties', {})
        
        # # Release information
        # if 'release_year' in props:
        #     result.append(f"   Started: {props['release_year']}")
        
        # # Episode duration
        # if 'duration' in props:
        #     result.append(f"   Episode Length: {props['duration']} minutes")
        
        # Rating
        if 'content_rating' in props:
            result.append(f"   Content Rating: {props['content_rating']}\n")
        
        # Description
        if 'description' in props:
            description = props['description']
            result.append(f"   Description: {description}\n")
        
        # # Production details
        # if 'production_companies' in props and props['production_companies']:
        #     companies = props['production_companies'][:3]
        #     result.append(f"   Production: {', '.join(companies)}")
        
        # # Filming location
        # if 'filming_location' in props:
        #     result.append(f"   Filmed in: {props['filming_location']}")
        
        # # Image
        # if 'image' in props and 'url' in props['image']:
        #     result.append(f"   Image: {props['image']['url']}")
        
        # Add spacing between TV shows
        if i < len(entities):
            result.append("")
    
    # Postman URL (only show once at the end)
    # if postman_url:
    #     result.append("")
    #     result.append(f"Postman URL: {postman_url}")
    #     result.append("   " + "="*60)
    
    return "\n".join(result)


def get_entity_podcast_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None,limit=3) -> str:
    """
    Get podcast insights for any signals and/or audience ID list passed.
    
    :param signals: Optional QlooSignals object containing signals for the query
    :param audience_ids: Optional list of audience IDs to filter results
    :return: Formatted string containing podcast insights
    """
    insights = client.get_entity_insights(
        audience_ids=audience_ids or [],
        entity_type="podcast",
        signals=signals,
        limit=limit
    )
    
    entities = insights.get('results', {}).get('entities', [])
    postman_url = insights.get('postman_url')

    if not entities:
        return "No podcast results found."
    
    # Build formatted string result
    result = [f"""Top {limit} podcasts liked by the audience\n"""]
    result.append("")

    # Process each podcast entity
    for i, entity in enumerate(entities, 1):
        
        # Add podcast header for multiple podcasts
        if len(entities) > 1:
            result.append(f"--- PODCAST Rank {i} ---")
        
        # Basic podcast information
        result.append(f"PODCAST Name: {entity['name']}")
        # result.append(f"   Entity ID: {entity['entity_id']}")
        
        # Affinity and popularity - handle different possible locations
        affinity = 0
        if 'query' in entity and 'affinity' in entity['query']:
            affinity = entity['query']['affinity']
        elif 'affinity_score' in entity:
            affinity = entity['affinity_score']
        elif 'affinity' in entity:
            affinity = entity['affinity']
        
        result.append(f"   Affinity: {affinity:.3f}\n")
        
        # # Audience Growth
        # growth = 0
        # if 'query' in entity and 'measurements' in entity['query']:
        #     growth = entity['query']['measurements'].get('audience_growth', 0)
        
        # if growth > 0:
        #     growth_indicator = "(up)"
        # elif growth < 0:
        #     growth_indicator = "(down)"
        # else:
        #     growth_indicator = "(flat)"
        
        # result.append(f"   Audience Growth: {growth:.2f} {growth_indicator}")
        
        props = entity.get('properties', {})
        
        # Channel/Host
        # if 'channel' in props:
        #     result.append(f"   Channel: {props['channel']}")
        # Rating
        if 'rating' in props:
            result.append(f"   Rating: {props['rating']}/5.0\n")        
        # # Episode count
        # if 'episode_count' in props:
        #     result.append(f"   Episodes: {props['episode_count']}")
        
        # Content rating
        if 'content_rating' in props:
            result.append(f"   Content Rating: {props['content_rating']}\n")
        
        # Description
        description = props.get('short_description', props.get('description', ''))
        if description:
            result.append(f"   Description: {description}\n")
        
        # # Image
        # if 'image' in props and 'url' in props['image']:
        #     result.append(f"   Image: {props['image']['url']}")
        
        # Add spacing between podcasts
        if i < len(entities):
            result.append("")
    
    # Postman URL (only show once at the end)
    # if postman_url:
    #     result.append("")
    #     result.append(f"Postman URL: {postman_url}")
    #     result.append("   " + "="*60)
    
    return "\n".join(result)


def get_entity_videogame_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None,limit=3) -> str:
    """
    Get videogame insights for any signals and/or audience ID list passed.
    
    :param signals: Optional QlooSignals object containing signals for the query
    :param audience_ids: Optional list of audience IDs to filter results
    :return: Formatted string containing videogame insights
    """
    insights = client.get_entity_insights(
        audience_ids=audience_ids or [],
        entity_type="videogame",
        signals=signals,
        limit=limit
    )
    
    entities = insights.get('results', {}).get('entities', [])
    postman_url = insights.get('postman_url')

    if not entities:
        return "No videogame results found."
    
    # Build formatted string result
    result = [f"""Top {limit} videogames liked by the audience"""]
    result.append("\n")

    # Process each videogame entity
    for i, entity in enumerate(entities, 1):
        
        # Add videogame header for multiple videogames
        if len(entities) > 1:
            result.append(f"--- VIDEOGAME Rank {i} ---\n")
        
        # Basic videogame information
        result.append(f"VIDEOGAME Name: {entity['name']}")
        # result.append(f"   Entity ID: {entity['entity_id']}")
        
        # Affinity and popularity - handle different possible locations
        affinity = 0
        if 'query' in entity and 'affinity' in entity['query']:
            affinity = entity['query']['affinity']
        elif 'affinity_score' in entity:
            affinity = entity['affinity_score']
        elif 'affinity' in entity:
            affinity = entity['affinity']
        
        result.append(f"   Affinity: {affinity:.3f}\n")
        
        # # Audience Growth
        # growth = 0
        # if 'query' in entity and 'measurements' in entity['query']:
        #     growth = entity['query']['measurements'].get('audience_growth', 0)
        
        # if growth > 0:
        #     growth_indicator = "(up)"
        # elif growth < 0:
        #     growth_indicator = "(down)"
        # else:
        #     growth_indicator = "(flat)"
        
        # result.append(f"   Audience Growth: {growth:.2f} {growth_indicator}")
        
        props = entity.get('properties', {})
        
        # Release information
        if 'release_year' in props:
            result.append(f"Release Year: {props['release_year']}\n")
        
        # # Developer and Publisher
        # if 'developer' in props:
        #     result.append(f"   Developer: {props['developer']}")
        # if 'publisher' in props:
        #     result.append(f"   Publisher: {props['publisher']}")
        
        # Platforms
        if 'platforms' in props:
            result.append(f"   Platforms: {props['platforms']}\n")
        
        # Content rating
        if 'content_rating' in props:
            result.append(f"   Rating: {props['content_rating']}\n")
        
        # Description
        description = props.get('description', '')
        if description:
            result.append(f"   Description: {description}\n")
        
        # # Image
        # if 'image' in props and 'url' in props['image']:
        #     result.append(f"   Image: {props['image']['url']}")
        
        # Add spacing between videogames
        if i < len(entities):
            result.append("")
    
    # Postman URL (only show once at the end)
    # if postman_url:
    #     result.append("")
    #     result.append(f"Postman URL: {postman_url}")
    #     result.append("   " + "="*60)
    
    return "\n".join(result)


def get_tag_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None, tag_filter: Optional[str] = None,limit=10) -> str:
    """
    Get tag insights for any signals and/or audience ID list passed.
    
    :param signals: Optional QlooSignals object containing signals for the query
    :param audience_ids: Optional list of audience IDs to filter results
    :param tag_filter: Optional specific tag filter (e.g., "urn:tag:lifestyle:qloo")
    :return: Formatted string containing tag insights
    """
    insights = client.get_tag_insights(
        audience_ids=audience_ids or [],
        signals=signals,
        limit=limit,
        tag_filter=tag_filter
    )
    tags = insights.get('results', {}).get('tags', [])
    postman_url = insights.get('postman_url')
    #logging.info(f"Postman URL: {postman_url}")

    if not tags:
        return "No tag results found."
    
    # Build formatted string result
    tag_type = tag_filter or "all types"
    result = [f"""Top {limit} tags describing audience based on the signals provided.
              Tag insights reveal the themes, characteristics, and content attributes that resonate most strongly with your target audience.
              They're like a "DNA profile" of your audience's cultural preferences.\n"""]
    result.append("")

    # Process each tag
    for i, tag in enumerate(tags, 1):
        
        # Add tag header for multiple tags
        if len(tags) > 1:
            result.append(f"--- TAG Rank {i} ---")
        
        # Basic tag information
        result.append(f"TAG Name: {tag['name']}\n")
        # result.append(f"   Tag ID: {tag['tag_id']}")
        
        # Safe access to affinity score
        affinity = tag.get('query', {}).get('affinity', 0)
        result.append(f"   Affinity: {affinity:.3f}\n")
        
        # Tag type information
        result.append(f"   Type: {tag.get('subtype', 'Unknown')}\n")
        
        # What entities this tag applies to
        entity_types = tag.get('types', [])
        if entity_types:
            # Clean up the URN format for readability
            clean_types = []
            for entity_type in entity_types:
                if 'urn:entity:' in entity_type:
                    clean_type = entity_type.replace('urn:entity:', '')
                    clean_types.append(clean_type)
                else:
                    clean_types.append(entity_type)
            result.append(f"   Applies to: {', '.join(clean_types)}\n")
        
        # Add spacing between tags
        if i < len(tags):
            result.append("")
    
    # Postman URL (only show once at the end)
    # if postman_url:
    #     result.append("")
    #     result.append(f"Postman URL: {postman_url}")
    #     result.append("   " + "="*60)
    
    return "\n".join(result)