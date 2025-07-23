import requests
import json
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import os
import logging
from src.qloo import QlooAPIClient, QlooSignals, QlooAudience

load_dotenv()

##Initiate Qloo API Client
client = QlooAPIClient(api_key=os.getenv("QLOO_API_KEY"))


def get_insights_tool(signals: Optional[QlooSignals], entity: Optional[List[str]]) -> str:
    """
    Get insights based on the entity type and signals provided.
    
    :param signals: Optional QlooSignals object containing signals for the query
    :param entity: The list of types of entity to get insights for
       ["movie", "podcast", "videogame", "tv_show", "artist", "people", "tag", "place"]
    :return: Formatted string containing insights
    """
    
    insight_summary = []  # Keep as list throughout
    
    if "brand" in entity or "all" in entity or not entity or entity is None:
        result = get_entity_brand_insights(signals)
        if result:
            insight_summary.append(result)
            
    if "movie" in entity or "all" in entity or not entity or entity is None:
        result = get_entity_movie_insights(signals)
        if result:
            insight_summary.append(result)
            
    if "podcast" in entity or "all" in entity or not entity or entity is None:
        result = get_entity_podcast_insights(signals)
        if result:
            insight_summary.append(result)
            
    if "videogame" in entity or "all" in entity or not entity or entity is None:
        result = get_entity_videogame_insights(signals)
        if result:
            insight_summary.append(result)
            
    if "tv_show" in entity or "all" in entity or not entity or entity is None:
        result = get_entity_tv_show_insights(signals)
        if result:
            insight_summary.append(result)
            
    if "artist" in entity or "all" in entity or not entity or entity is None:
        result = get_entity_artist_insights(signals)
        if result:
            insight_summary.append(result)
            
    if "people" in entity or "all" in entity or not entity or entity is None:
        result = get_entity_people_insights(signals)
        if result:
            insight_summary.append(result)
            
    if "tag" in entity or "all" in entity or not entity or entity is None:
        result = get_tag_insights(signals)
        if result:
            insight_summary.append(result)
            
    if "place" in entity or "all" in entity or not entity or entity is None:
        result = get_entity_place_insights(signals)  # Fixed: should be place insights
        if result:
            insight_summary.append(result)
    
    if not insight_summary:
        return "No insights available for the selected entity."
    
    # Join all results with separators
    separator = f"\n\n{'='*80}\n\n"
    return separator.join(insight_summary)

def get_entity_movie_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None) -> str:
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
        limit=3
    )
    
    entities = insights.get('results', {}).get('entities', [])
    postman_url = insights.get('postman_url')

    if not entities:
        return "No movie results found."
    
    # Build formatted string result
    result = [f"""Below are the details of the top 10 movies liked by the audience based on the signals provided.
              You can understand the taste of movies and genres that resonate with your audience from this.
              """]
    result.append("")

    # Process each movie entity
    for i, entity in enumerate(entities, 1):
        
        # Add movie header for multiple movies
        if len(entities) > 1:
            result.append(f"--- MOVIE {i} ---")
        
        # Basic movie information
        result.append(f"MOVIE: {entity['name']}")
        result.append(f"   Entity ID: {entity['entity_id']}")
        
        # Affinity and popularity - handle different possible locations
        affinity = 0
        if 'query' in entity and 'affinity' in entity['query']:
            affinity = entity['query']['affinity']
        elif 'affinity_score' in entity:
            affinity = entity['affinity_score']
        elif 'affinity' in entity:
            affinity = entity['affinity']
        
        popularity = entity.get('popularity', 0)
        
        result.append(f"   Affinity: {affinity:.3f}")
        # result.append(f"   Popularity: {popularity:.3f}")
        
        
        # Properties section
        props = entity.get('properties', {})
        
        # Release information
        if 'release_year' in props:
            result.append(f"   Release Year: {props['release_year']}")
        # if 'release_date' in props:
        #     result.append(f"   Release Date: {props['release_date']}")
        
        # # Duration
        # if 'duration' in props:
        #     result.append(f"   Duration: {props['duration']} minutes")
        
        # Rating
        if 'content_rating' in props:
            result.append(f"   Content Rating: {props['content_rating']}")
        
        # Description
        if 'description' in props:
            description = props['description']
            result.append(f"   Plot: {description}")
        
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


def get_entity_brand_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None) -> str:
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
        limit=3
    )
    
    entities = insights.get('results', {}).get('entities', [])
    postman_url = insights.get('postman_url')

    if not entities:
        return "No brand results found."
    
    # Build formatted string result
    result = [f"""Below are the details of the top 10 brands liked by the audience based on the signals provided.
              You can use these insights to understand what brands resonate with your audience"""]
    result.append("")

    # Process each brand entity
    for i, entity in enumerate(entities, 1):
        
        # Add brand header for multiple brands
        if len(entities) > 1:
            result.append(f"--- BRAND {i} ---")
        
        # Basic brand information
        result.append(f"BRAND: {entity['name']}")
        result.append(f"   Entity ID: {entity['entity_id']}")
        
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
        
        # Properties section
        props = entity.get('properties', {})
        
        # Brand description
        if 'short_description' in props:
            result.append(f"   Description: {props['short_description']}")
        
        # Image URL if available
        if 'image' in props and 'url' in props['image']:
            result.append(f"   Image: {props['image']['url']}")
        
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


def get_entity_artist_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None) -> str:
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
    result = [f"""Below are the details of the top 10 artists/musicians liked by the audience based on the signals provided.
              You can use these insights to understand the taste of music most liked by your audience"""]
    result.append("")

    # Process each artist entity
    for i, entity in enumerate(entities, 1):
        
        # Add artist header for multiple artists
        if len(entities) > 1:
            result.append(f"--- ARTIST {i} ---")
        
        # Basic artist information
        result.append(f"ARTIST: {entity['name']}")
        result.append(f"   Entity ID: {entity['entity_id']}")
        
        # Affinity and popularity - handle different possible locations
        affinity = 0
        if 'query' in entity and 'affinity' in entity['query']:
            affinity = entity['query']['affinity']
        elif 'affinity_score' in entity:
            affinity = entity['affinity_score']
        elif 'affinity' in entity:
            affinity = entity['affinity']
        
        result.append(f"   Affinity: {affinity:.3f}")
        
        # Audience Growth
        growth = 0
        if 'query' in entity and 'measurements' in entity['query']:
            growth = entity['query']['measurements'].get('audience_growth', 0)
        
        if growth > 0:
            growth_indicator = "(up)"
        elif growth < 0:
            growth_indicator = "(down)"
        else:
            growth_indicator = "(flat)"
        
        result.append(f"   Audience Growth: {growth:.2f} {growth_indicator}")
        
        props = entity.get('properties', {})
        
        # Description
        description = props.get('short_description', {})
        if isinstance(description, dict) and 'value' in description:
            result.append(f"   Description: {description['value']}")
        elif isinstance(description, str):
            result.append(f"   Description: {description}")
        
        # Birth info
        if 'date_of_birth' in props:
            result.append(f"   Born: {props['date_of_birth']}")
        if 'place_of_birth' in props:
            result.append(f"   Birthplace: {props['place_of_birth']}")
        
        # Alternative names
        if 'akas' in props and props['akas']:
            akas = [aka.get('value', aka) for aka in props['akas'][:3] if aka]
            result.append(f"   Also known as: {', '.join(akas)}")
        
        # Image
        if 'image' in props and 'url' in props['image']:
            result.append(f"   Image: {props['image']['url']}")
        
        # External platforms
        if 'external' in entity:
            for platform, data in entity['external'].items():
                if data and isinstance(data, list) and len(data) > 0:
                    platform_data = data[0]
                    if platform == 'spotify':
                        followers = platform_data.get('followers', 'N/A')
                        listeners = platform_data.get('monthly_listeners', 'N/A')
                        result.append(f"   Spotify: {followers} followers, {listeners} monthly listeners")
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


def get_entity_place_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None) -> str:
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
        limit=3
    )
    
    entities = insights.get('results', {}).get('entities', [])
    postman_url = insights.get('postman_url')

    if not entities:
        return "No place results found."
    
    # Build formatted string result
    result = [f"""Below are the details of the top 10 places liked by the audience based on the signals provided.
              This can help you understand the places the audience likes to visit or engage with most"""]
    result.append("")

    # Process each place entity
    for i, entity in enumerate(entities, 1):
        
        # Add place header for multiple places
        if len(entities) > 1:
            result.append(f"--- PLACE {i} ---")
        
        # Basic place information
        result.append(f"PLACE: {entity['name']}")
        result.append(f"   Entity ID: {entity['entity_id']}")
        
        # Affinity and popularity - handle different possible locations
        affinity = 0
        if 'query' in entity and 'affinity' in entity['query']:
            affinity = entity['query']['affinity']
        elif 'affinity_score' in entity:
            affinity = entity['affinity_score']
        elif 'affinity' in entity:
            affinity = entity['affinity']
        
        result.append(f"   Affinity: {affinity:.3f}")
        
        # Audience Growth
        growth = 0
        if 'query' in entity and 'measurements' in entity['query']:
            growth = entity['query']['measurements'].get('audience_growth', 0)
        
        if growth > 0:
            growth_indicator = "(up)"
        elif growth < 0:
            growth_indicator = "(down)"
        else:
            growth_indicator = "(flat)"
        
        result.append(f"   Audience Growth: {growth:.2f} {growth_indicator}")
        
        props = entity.get('properties', {})
        
        # Address
        if 'address' in props:
            result.append(f"   Address: {props['address']}")
        
        # Business details
        if 'business_rating' in props:
            result.append(f"   Business Rating: {props['business_rating']}/5.0")
        
        if 'phone' in props:
            result.append(f"   Phone: {props['phone']}")
        
        if 'website' in props:
            result.append(f"   Website: {props['website']}")
        
        # Neighborhood/Location
        if 'neighborhood' in props:
            result.append(f"   Neighborhood: {props['neighborhood']}")
        
        # Status
        if 'is_closed' in props:
            status = "Closed" if props['is_closed'] else "Open"
            result.append(f"   Status: {status}")
        
        # Keywords/Popular terms
        if 'keywords' in props and props['keywords']:
            top_keywords = [kw.get('name', str(kw)) for kw in props['keywords'][:5]]
            result.append(f"   Keywords: {', '.join(top_keywords)}")
        
        # Coordinates
        if 'location' in entity:
            loc = entity['location']
            lat = loc.get('lat', 'N/A')
            lon = loc.get('lon', 'N/A')
            result.append(f"   Coordinates: {lat}, {lon}")
        
        # Add spacing between places
        if i < len(entities):
            result.append("")
    
    # Postman URL (only show once at the end)
    # if postman_url:
    #     result.append("")
    #     result.append(f"Postman URL: {postman_url}")
    #     result.append("   " + "="*60)
    
    return "\n".join(result)


def get_entity_people_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None) -> str:
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
        limit=3
    )
    
    entities = insights.get('results', {}).get('entities', [])
    postman_url = insights.get('postman_url')

    if not entities:
        return "No people results found."
    
    # Build formatted string result
    result = [f"""Below are the details of the top 10 people liked by the audience based on the signals provided.
              You can use these insights to understand the personalities or public figures that resonate with your audience"""]
    result.append("")

    # Process each people entity
    for i, entity in enumerate(entities, 1):
        
        # Add people header for multiple people
        if len(entities) > 1:
            result.append(f"--- PERSON {i} ---")
        
        # Basic people information
        result.append(f"PERSON: {entity['name']}")
        result.append(f"   Entity ID: {entity['entity_id']}")
        
        # Affinity and popularity - handle different possible locations
        affinity = 0
        if 'query' in entity and 'affinity' in entity['query']:
            affinity = entity['query']['affinity']
        elif 'affinity_score' in entity:
            affinity = entity['affinity_score']
        elif 'affinity' in entity:
            affinity = entity['affinity']
        
        result.append(f"   Affinity: {affinity:.3f}")
        
        # Audience Growth
        growth = 0
        if 'query' in entity and 'measurements' in entity['query']:
            growth = entity['query']['measurements'].get('audience_growth', 0)
        
        if growth > 0:
            growth_indicator = "(up)"
        elif growth < 0:
            growth_indicator = "(down)"
        else:
            growth_indicator = "(flat)"
        
        result.append(f"   Audience Growth: {growth:.2f} {growth_indicator}")
        
        props = entity.get('properties', {})
        
        # Personal info
        if 'date_of_birth' in props:
            result.append(f"   Born: {props['date_of_birth']}")
        
        if 'gender' in props and props['gender']:
            gender = props['gender'][0] if isinstance(props['gender'], list) else props['gender']
            result.append(f"   Gender: {gender}")
        
        if 'citizenship' in props and props['citizenship']:
            citizenship = props['citizenship'][0] if isinstance(props['citizenship'], list) else props['citizenship']
            result.append(f"   Citizenship: {citizenship}")
        
        # Professional info
        if 'instrument' in props and props['instrument']:
            instruments = props['instrument'][:3] if isinstance(props['instrument'], list) else [props['instrument']]
            result.append(f"   Instruments: {', '.join(instruments)}")
        
        if 'work_period_start' in props:
            result.append(f"   Career Started: {props['work_period_start']}")
        
        # Awards
        if 'award_received' in props and props['award_received']:
            awards = props['award_received'][:3] if isinstance(props['award_received'], list) else [props['award_received']]
            result.append(f"   Awards: {', '.join(awards)}")
        
        # Description
        if 'short_descriptions' in props and props['short_descriptions']:
            description = props['short_descriptions'][0]
            if isinstance(description, dict) and 'value' in description:
                result.append(f"   Description: {description['value']}")
            elif isinstance(description, str):
                result.append(f"   Description: {description}")
        
        # Alternative names
        if 'akas' in props and props['akas']:
            akas = [aka.get('value', str(aka)) for aka in props['akas'][:3] if aka]
            result.append(f"   Also known as: {', '.join(akas)}")
        
        # Website
        if 'official_website' in props and props['official_website']:
            website = props['official_website'][0] if isinstance(props['official_website'], list) else props['official_website']
            result.append(f"   Website: {website}")
        
        # Image
        if 'image' in props and 'url' in props['image']:
            result.append(f"   Image: {props['image']['url']}")
        
        # Add spacing between people
        if i < len(entities):
            result.append("")
    
    # # Postman URL (only show once at the end)
    # if postman_url:
    #     result.append("")
    #     result.append(f"Postman URL: {postman_url}")
    #     result.append("   " + "="*60)
    
    return "\n".join(result)


def get_entity_tv_show_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None) -> str:
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
        limit=3
    )
    
    entities = insights.get('results', {}).get('entities', [])
    postman_url = insights.get('postman_url')

    if not entities:
        return "No TV show results found."
    
    # Build formatted string result
    result = [f"""Below are the details of the top 10 TV shows liked by the audience based on the signals provided.
              You can use these insights to understand the taste of TV shows and genres that resonate with your audience"""]
    result.append("")

    # Process each TV show entity
    for i, entity in enumerate(entities, 1):
        
        # Add TV show header for multiple TV shows
        if len(entities) > 1:
            result.append(f"--- TV SHOW {i} ---")
        
        # Basic TV show information
        result.append(f"TV SHOW: {entity['name']}")
        result.append(f"   Entity ID: {entity['entity_id']}")
        
        # Affinity and popularity - handle different possible locations
        affinity = 0
        if 'query' in entity and 'affinity' in entity['query']:
            affinity = entity['query']['affinity']
        elif 'affinity_score' in entity:
            affinity = entity['affinity_score']
        elif 'affinity' in entity:
            affinity = entity['affinity']
        
        result.append(f"   Affinity: {affinity:.3f}")
        
        # Audience Growth
        growth = 0
        if 'query' in entity and 'measurements' in entity['query']:
            growth = entity['query']['measurements'].get('audience_growth', 0)
        
        if growth > 0:
            growth_indicator = "(up)"
        elif growth < 0:
            growth_indicator = "(down)"
        else:
            growth_indicator = "(flat)"
        
        result.append(f"   Audience Growth: {growth:.2f} {growth_indicator}")
        
        props = entity.get('properties', {})
        
        # Release information
        if 'release_year' in props:
            result.append(f"   Started: {props['release_year']}")
        
        # Episode duration
        if 'duration' in props:
            result.append(f"   Episode Length: {props['duration']} minutes")
        
        # Rating
        if 'content_rating' in props:
            result.append(f"   Content Rating: {props['content_rating']}")
        
        # Description
        if 'description' in props:
            description = props['description']
            result.append(f"   Description: {description}")
        
        # # Production details
        # if 'production_companies' in props and props['production_companies']:
        #     companies = props['production_companies'][:3]
        #     result.append(f"   Production: {', '.join(companies)}")
        
        # Filming location
        if 'filming_location' in props:
            result.append(f"   Filmed in: {props['filming_location']}")
        
        # Image
        if 'image' in props and 'url' in props['image']:
            result.append(f"   Image: {props['image']['url']}")
        
        # Add spacing between TV shows
        if i < len(entities):
            result.append("")
    
    # Postman URL (only show once at the end)
    # if postman_url:
    #     result.append("")
    #     result.append(f"Postman URL: {postman_url}")
    #     result.append("   " + "="*60)
    
    return "\n".join(result)


def get_entity_podcast_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None) -> str:
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
        limit=3
    )
    
    entities = insights.get('results', {}).get('entities', [])
    postman_url = insights.get('postman_url')

    if not entities:
        return "No podcast results found."
    
    # Build formatted string result
    result = [f"""Below are the details of the top 10 podcasts liked by the audience based on the signals provided.
              You can use these insights to understand the taste of podcasts and genres that resonate with your audience"""]
    result.append("")

    # Process each podcast entity
    for i, entity in enumerate(entities, 1):
        
        # Add podcast header for multiple podcasts
        if len(entities) > 1:
            result.append(f"--- PODCAST {i} ---")
        
        # Basic podcast information
        result.append(f"PODCAST: {entity['name']}")
        result.append(f"   Entity ID: {entity['entity_id']}")
        
        # Affinity and popularity - handle different possible locations
        affinity = 0
        if 'query' in entity and 'affinity' in entity['query']:
            affinity = entity['query']['affinity']
        elif 'affinity_score' in entity:
            affinity = entity['affinity_score']
        elif 'affinity' in entity:
            affinity = entity['affinity']
        
        result.append(f"   Affinity: {affinity:.3f}")
        
        # Audience Growth
        growth = 0
        if 'query' in entity and 'measurements' in entity['query']:
            growth = entity['query']['measurements'].get('audience_growth', 0)
        
        if growth > 0:
            growth_indicator = "(up)"
        elif growth < 0:
            growth_indicator = "(down)"
        else:
            growth_indicator = "(flat)"
        
        result.append(f"   Audience Growth: {growth:.2f} {growth_indicator}")
        
        props = entity.get('properties', {})
        
        # Channel/Host
        if 'channel' in props:
            result.append(f"   Channel: {props['channel']}")
        
        # Rating
        if 'rating' in props:
            result.append(f"   Rating: {props['rating']}/5.0")
        
        # Episode count
        if 'episode_count' in props:
            result.append(f"   Episodes: {props['episode_count']}")
        
        # Content rating
        if 'content_rating' in props:
            result.append(f"   Content Rating: {props['content_rating']}")
        
        # Description
        description = props.get('short_description', props.get('description', ''))
        if description:
            result.append(f"   Description: {description}")
        
        # Image
        if 'image' in props and 'url' in props['image']:
            result.append(f"   Image: {props['image']['url']}")
        
        # Add spacing between podcasts
        if i < len(entities):
            result.append("")
    
    # Postman URL (only show once at the end)
    # if postman_url:
    #     result.append("")
    #     result.append(f"Postman URL: {postman_url}")
    #     result.append("   " + "="*60)
    
    return "\n".join(result)


def get_entity_videogame_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None) -> str:
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
        limit=3
    )
    
    entities = insights.get('results', {}).get('entities', [])
    postman_url = insights.get('postman_url')

    if not entities:
        return "No videogame results found."
    
    # Build formatted string result
    result = [f"""Below are the details of the top 10 videogames liked by the audience based on the signals provided.
              You can use these insights to understand the taste of videogames and genres that resonate with your audience"""]
    result.append("")

    # Process each videogame entity
    for i, entity in enumerate(entities, 1):
        
        # Add videogame header for multiple videogames
        if len(entities) > 1:
            result.append(f"--- VIDEOGAME {i} ---")
        
        # Basic videogame information
        result.append(f"VIDEOGAME: {entity['name']}")
        result.append(f"   Entity ID: {entity['entity_id']}")
        
        # Affinity and popularity - handle different possible locations
        affinity = 0
        if 'query' in entity and 'affinity' in entity['query']:
            affinity = entity['query']['affinity']
        elif 'affinity_score' in entity:
            affinity = entity['affinity_score']
        elif 'affinity' in entity:
            affinity = entity['affinity']
        
        result.append(f"   Affinity: {affinity:.3f}")
        
        # Audience Growth
        growth = 0
        if 'query' in entity and 'measurements' in entity['query']:
            growth = entity['query']['measurements'].get('audience_growth', 0)
        
        if growth > 0:
            growth_indicator = "(up)"
        elif growth < 0:
            growth_indicator = "(down)"
        else:
            growth_indicator = "(flat)"
        
        result.append(f"   Audience Growth: {growth:.2f} {growth_indicator}")
        
        props = entity.get('properties', {})
        
        # Release information
        if 'release_year' in props:
            result.append(f"   Release Year: {props['release_year']}")
        
        # Developer and Publisher
        if 'developer' in props:
            result.append(f"   Developer: {props['developer']}")
        if 'publisher' in props:
            result.append(f"   Publisher: {props['publisher']}")
        
        # Platforms
        if 'platforms' in props:
            result.append(f"   Platforms: {props['platforms']}")
        
        # Content rating
        if 'content_rating' in props:
            result.append(f"   Rating: {props['content_rating']}")
        
        # Description
        description = props.get('description', '')
        if description:
            result.append(f"   Description: {description}")
        
        # Image
        if 'image' in props and 'url' in props['image']:
            result.append(f"   Image: {props['image']['url']}")
        
        # Add spacing between videogames
        if i < len(entities):
            result.append("")
    
    # Postman URL (only show once at the end)
    # if postman_url:
    #     result.append("")
    #     result.append(f"Postman URL: {postman_url}")
    #     result.append("   " + "="*60)
    
    return "\n".join(result)


def get_tag_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None, tag_filter: Optional[str] = None) -> str:
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
        limit=3,
        tag_filter=tag_filter
    )
    tags = insights.get('results', {}).get('tags', [])
    postman_url = insights.get('postman_url')
    #logging.info(f"Postman URL: {postman_url}")

    if not tags:
        return "No tag results found."
    
    # Build formatted string result
    tag_type = tag_filter or "all types"
    result = [f"""Below are the details of the top 10 tags liked by the audience based on the signals provided.
              Tag insights reveal the themes, characteristics, and content attributes that resonate most strongly with your target audience.
              They're like a "DNA profile" of your audience's cultural preferences."""]
    result.append("")

    # Process each tag
    for i, tag in enumerate(tags, 1):
        
        # Add tag header for multiple tags
        if len(tags) > 1:
            result.append(f"--- TAG {i} ---")
        
        # Basic tag information
        result.append(f"TAG: {tag['name']}")
        result.append(f"   Tag ID: {tag['tag_id']}")
        
        # Safe access to affinity score
        affinity = tag.get('query', {}).get('affinity', 0)
        result.append(f"   Affinity: {affinity:.3f}")
        
        # Tag type information
        result.append(f"   Type: {tag.get('subtype', 'Unknown')}")
        
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
            result.append(f"   Applies to: {', '.join(clean_types)}")
        
        # Add spacing between tags
        if i < len(tags):
            result.append("")
    
    # Postman URL (only show once at the end)
    # if postman_url:
    #     result.append("")
    #     result.append(f"Postman URL: {postman_url}")
    #     result.append("   " + "="*60)
    
    return "\n".join(result)


def get_lifestyle_tag_insights(signals: Optional[QlooSignals], audience_ids: Optional[List[str]] = None) -> str:
    """
    Get lifestyle tag insights for any signals and/or audience ID list passed.
    
    :param signals: Optional QlooSignals object containing signals for the query
    :param audience_ids: Optional list of audience IDs to filter results
    :return: Formatted string containing lifestyle tag insights
    """
    return get_tag_insights(signals, audience_ids, tag_filter="urn:tag:lifestyle:qloo")


# Usage examples:

if __name__ == "__main__":
    # Example signals
    entity_signals = QlooSignals(
        demographics={"age": "25_to_29", "gender": "female"},
        location={"query": "Mumbai"},
        entity_ids=["A21D248A-7379-458E-A3BE-7B8C4B961AF6"]  # Chelsea FC entity ID
    )

    # Test all entity types
    logging.info("=== BRAND INSIGHTS ===")
    brand_results = get_entity_brand_insights(signals=entity_signals)
    logging.info(brand_results)
    
    logging.info("\n=== ARTIST INSIGHTS ===")
    artist_results = get_entity_artist_insights(signals=entity_signals)
    logging.info(artist_results)
    
    logging.info("\n=== PLACE INSIGHTS ===")
    place_results = get_entity_place_insights(signals=entity_signals)
    logging.info(place_results)
    
    logging.info("\n=== PEOPLE INSIGHTS ===")
    people_results = get_entity_people_insights(signals=entity_signals)
    logging.info(people_results)
    
    logging.info("\n=== TV SHOW INSIGHTS ===")
    tv_results = get_entity_tv_show_insights(signals=entity_signals)
    logging.info(tv_results)
    
    logging.info("\n=== PODCAST INSIGHTS ===")
    podcast_results = get_entity_podcast_insights(signals=entity_signals)
    logging.info(podcast_results)
    
    logging.info("\n=== VIDEOGAME INSIGHTS ===")
    game_results = get_entity_videogame_insights(signals=entity_signals)
    logging.info(game_results)
    
    logging.info("\n=== TAG INSIGHTS ===")
    tag_results = get_tag_insights(signals=entity_signals)
    logging.info(tag_results)
    
    logging.info("\n=== LIFESTYLE TAG INSIGHTS ===")
    lifestyle_results = get_lifestyle_tag_insights(signals=entity_signals)
    logging.info(lifestyle_results)
