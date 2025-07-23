import requests
import json
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import os
from src.qloo import QlooAPIClient, QlooSignals, QlooAudience
from .subtools import get_entity_movie_insights, get_entity_podcast_insights, get_entity_videogame_insights, get_tag_insights
from .subtools import get_entity_tv_show_insights,get_entity_artist_insights,get_entity_people_insights,get_entity_brand_insights,get_entity_place_insights


load_dotenv()

##Initiate Qloo API Client
client = QlooAPIClient(api_key=os.getenv("QLOO_API_KEY"))


def get_insights_tool(signals: Optional[QlooSignals], entity: Optional[List[str]]) -> str:
    """
    Get insights based on the entity type and signals provided.
    
    :param signals: Optional QlooSignals object containing signals for the query
    :param entity: The list of types of entity to get insights for 
       ["movie", "podcast", "videogame", "tv_show", "artist", "people", "tag","people","place"]
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



def get_demographics_insights_tool(entity_ids: List[str], signals: Optional[QlooSignals] = None) -> str:
    """
    Get demographics insights for entity IDs with optional signals.
    
    :param entity_ids: List of entity IDs to analyze demographics for
    :param signals: Optional QlooSignals object containing additional signals
    :return: Formatted string containing demographics insights
    """
    demographics_result = client.get_demographics_analysis(
        entity_ids=entity_ids,
        signals=signals,
        limit=20
    )
    
    demographics_data = demographics_result.get('results', {}).get('demographics', [])
    
    if not demographics_data:
        return "No demographics results found."
    
    # Build formatted string result
    result = [f"""Below are the demographics details for the {len(demographics_data)} entities analyzed.
You can use these insights to understand the age and gender composition of your audience."""]
    result.append("")
    
    # Process each entity's demographics
    for i, demo in enumerate(demographics_data, 1):
        entity_id = demo.get("entity_id", "Unknown")
        query_data = demo.get("query", {})
        
        # Add entity header for multiple entities
        if len(demographics_data) > 1:
            result.append(f"--- ENTITY {i} ---")
        
        # Basic entity information
        result.append(f"ENTITY ID: {entity_id}")
        
        # Extract and format age data
        age_data = query_data.get("age", {})
        if age_data:
            result.append("   AGE DEMOGRAPHICS:")
            # Sort age groups by score (highest first)
            sorted_ages = sorted(age_data.items(), key=lambda x: x[1], reverse=True)
            for age_group, score in sorted_ages:
                age_display = age_group.replace('_', ' ').title()
                score_indicator = "+" if score > 0 else ""
                result.append(f"      {age_display}: {score_indicator}{score:.3f}")
        
        # Extract and format gender data
        gender_data = query_data.get("gender", {})
        if gender_data:
            result.append("   GENDER DEMOGRAPHICS:")
            for gender, score in gender_data.items():
                score_indicator = "+" if score > 0 else ""
                result.append(f"      {gender.title()}: {score_indicator}{score:.3f}")
        
        # Determine dominant demographics
        if age_data:
            dominant_age = max(age_data.items(), key=lambda x: x[1])
            result.append(f"   Dominant Age Group: {dominant_age[0].replace('_', ' ').title()} ({dominant_age[1]:+.3f})")
        
        if gender_data:
            dominant_gender = max(gender_data.items(), key=lambda x: x[1])
            if dominant_gender[1] > 0.3:  # Significant skew
                result.append(f"   Gender Skew: {dominant_gender[0].title()} ({dominant_gender[1]:+.3f})")
            else:
                result.append("   Gender Skew: Neutral")
        
        # Add spacing between entities
        if i < len(demographics_data):
            result.append("")
    
    return "\n".join(result)


def get_heatmap_insights_report_tool(location_query: str, entity_ids: Optional[List[str]] = None, 
                               signals: Optional[QlooSignals] = None, limit: int = 50) -> str:
    """
    Get detailed heatmap insights report for a location with optional entity IDs and signals.
    
    :param location_query: Location to analyze (e.g., "Toronto", "New York")
    :param entity_ids: Optional list of entity IDs for context
    :param signals: Optional QlooSignals object containing additional signals
    :param limit: Maximum number of location points to analyze
    :return: Formatted string containing detailed heatmap insights report
    """
    heatmap_result = client.get_heatmap_analysis(
        location_query=location_query,
        entity_ids=entity_ids,
        signals=signals,
        limit=limit
    )
    
    heatmap_data = heatmap_result.get('results', {}).get('heatmap', [])
    query_info = heatmap_result.get('raw_response', {}).get('query', {})
    
    if not heatmap_data:
        return "No heatmap results found."
    
    # Get location context
    location_info = {}
    if "localities" in query_info:
        localities = query_info["localities"].get("filter", [])
        if localities:
            location_info = localities[0]
    
    # Build formatted string result
    result = [f"""DETAILED HEATMAP ANALYSIS REPORT
Location: {location_query}
Analysis Date: {heatmap_result.get('raw_response', {}).get('duration', 'N/A')}ms processing time

This report provides comprehensive geographic insights for {len(heatmap_data)} location points.
Use this data to identify high-value areas, understand spatial patterns, and optimize location-based strategies."""]
    result.append("")
    result.append("="*80)
    result.append("")
    
    # Location context
    if location_info:
        result.append("LOCATION DETAILS:")
        result.append(f"   Primary Location: {location_info.get('name', 'Unknown')}")
        if 'disambiguation' in location_info:
            result.append(f"   Full Address: {location_info['disambiguation']}")
        if 'popularity' in location_info:
            result.append(f"   Location Popularity Score: {location_info['popularity']:.4f}")
        if 'location' in location_info:
            loc_coords = location_info['location']
            result.append(f"   Center Coordinates: {loc_coords.get('lat', 'N/A'):.6f}, {loc_coords.get('lon', 'N/A'):.6f}")
        result.append("")
    
    # Calculate comprehensive statistics
    affinities = [point.get("query", {}).get("affinity", 0) for point in heatmap_data]
    popularities = [point.get("query", {}).get("popularity", 0) for point in heatmap_data]
    affinity_ranks = [point.get("query", {}).get("affinity_rank", 0) for point in heatmap_data]
    
    result.append("STATISTICAL ANALYSIS:")
    result.append(f"   Total Data Points: {len(heatmap_data)}")
    result.append(f"   Coverage Area: Geographic heatmap coverage")
    result.append("")
    
    if affinities:
        result.append("   AFFINITY METRICS:")
        result.append(f"      Range: {min(affinities):.4f} - {max(affinities):.4f}")
        result.append(f"      Average: {sum(affinities)/len(affinities):.4f}")
        result.append(f"      High Affinity Points (>0.8): {len([a for a in affinities if a > 0.8])}")
        result.append(f"      Medium Affinity Points (0.4-0.8): {len([a for a in affinities if 0.4 <= a <= 0.8])}")
        result.append(f"      Low Affinity Points (<0.4): {len([a for a in affinities if a < 0.4])}")
        result.append("")
    
    if popularities:
        result.append("   POPULARITY METRICS:")
        result.append(f"      Range: {min(popularities):.4f} - {max(popularities):.4f}")
        result.append(f"      Average: {sum(popularities)/len(popularities):.4f}")
        result.append(f"      High Popularity Points (>0.8): {len([p for p in popularities if p > 0.8])}")
        result.append(f"      Medium Popularity Points (0.4-0.8): {len([p for p in popularities if 0.4 <= p <= 0.8])}")
        result.append(f"      Low Popularity Points (<0.4): {len([p for p in popularities if p < 0.4])}")
        result.append("")
    
    if affinity_ranks:
        result.append("   RANKING METRICS:")
        result.append(f"      Affinity Rank Range: {min(affinity_ranks):.4f} - {max(affinity_ranks):.4f}")
        result.append(f"      Average Rank: {sum(affinity_ranks)/len(affinity_ranks):.4f}")
        result.append("")
    
    # Identify different tiers of hotspots
    tier1_hotspots = []  # Excellent: Both metrics > 0.8
    tier2_hotspots = []  # Good: Combined score > 0.6
    tier3_hotspots = []  # Moderate: Combined score 0.4-0.6
    
    for point in heatmap_data:
        location = point.get("location", {})
        query = point.get("query", {})
        
        affinity = query.get("affinity", 0)
        popularity = query.get("popularity", 0)
        affinity_rank = query.get("affinity_rank", 0)
        hotspot_score = (affinity * 0.6) + (popularity * 0.4)
        
        hotspot_data = {
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "geohash": location.get("geohash"),
            "affinity": affinity,
            "popularity": popularity,
            "affinity_rank": affinity_rank,
            "hotspot_score": hotspot_score
        }
        
        if affinity > 0.8 and popularity > 0.8:
            tier1_hotspots.append(hotspot_data)
        elif hotspot_score > 0.6:
            tier2_hotspots.append(hotspot_data)
        elif hotspot_score >= 0.4:
            tier3_hotspots.append(hotspot_data)
    
    # Sort each tier by score
    tier1_hotspots = sorted(tier1_hotspots, key=lambda x: x["hotspot_score"], reverse=True)
    tier2_hotspots = sorted(tier2_hotspots, key=lambda x: x["hotspot_score"], reverse=True)
    tier3_hotspots = sorted(tier3_hotspots, key=lambda x: x["hotspot_score"], reverse=True)
    
    result.append("HOTSPOT ANALYSIS:")
    result.append("")
    
    # Tier 1 - Premium hotspots
    if tier1_hotspots:
        result.append(f"   TIER 1 - PREMIUM HOTSPOTS ({len(tier1_hotspots)} locations):")
        result.append("   High affinity (>0.8) AND high popularity (>0.8)")
        result.append("")
        for i, hotspot in enumerate(tier1_hotspots[:15], 1):
            result.append(f"      --- PREMIUM LOCATION {i} ---")
            result.append(f"      Coordinates: {hotspot['latitude']:.6f}, {hotspot['longitude']:.6f}")
            result.append(f"      Geohash: {hotspot['geohash']}")
            result.append(f"      Affinity: {hotspot['affinity']:.4f}")
            result.append(f"      Popularity: {hotspot['popularity']:.4f}")
            result.append(f"      Affinity Rank: {hotspot['affinity_rank']:.4f}")
            result.append(f"      Overall Score: {hotspot['hotspot_score']:.4f}")
            result.append("")
    
    # Tier 2 - Good hotspots
    if tier2_hotspots:
        result.append(f"   TIER 2 - GOOD HOTSPOTS ({len(tier2_hotspots)} locations):")
        result.append("   Strong combined performance (score >0.6)")
        result.append("")
        for i, hotspot in enumerate(tier2_hotspots[:10], 1):
            result.append(f"      --- GOOD LOCATION {i} ---")
            result.append(f"      Coordinates: {hotspot['latitude']:.6f}, {hotspot['longitude']:.6f}")
            result.append(f"      Geohash: {hotspot['geohash']}")
            result.append(f"      Affinity: {hotspot['affinity']:.4f}")
            result.append(f"      Popularity: {hotspot['popularity']:.4f}")
            result.append(f"      Affinity Rank: {hotspot['affinity_rank']:.4f}")
            result.append(f"      Overall Score: {hotspot['hotspot_score']:.4f}")
            result.append("")
    
    # Tier 3 - Moderate hotspots (summary only)
    if tier3_hotspots:
        result.append(f"   TIER 3 - MODERATE HOTSPOTS ({len(tier3_hotspots)} locations):")
        result.append("   Moderate performance (score 0.4-0.6)")
        result.append("   Top 3 moderate locations:")
        for i, hotspot in enumerate(tier3_hotspots[:3], 1):
            result.append(f"      {i}. {hotspot['latitude']:.6f}, {hotspot['longitude']:.6f} (Score: {hotspot['hotspot_score']:.4f})")
        result.append("")
    
    # Summary recommendations
    result.append("STRATEGIC RECOMMENDATIONS:")
    total_significant = len(tier1_hotspots) + len(tier2_hotspots)
    if tier1_hotspots:
        result.append(f"   • PRIORITY FOCUS: {len(tier1_hotspots)} premium locations identified for immediate attention")
    if tier2_hotspots:
        result.append(f"   • SECONDARY TARGETS: {len(tier2_hotspots)} good locations for expansion or optimization")
    if tier3_hotspots:
        result.append(f"   • MONITORING: {len(tier3_hotspots)} moderate locations for future consideration")
    
    coverage_percent = (total_significant / len(heatmap_data)) * 100 if heatmap_data else 0
    result.append(f"   • MARKET COVERAGE: {coverage_percent:.1f}% of analyzed area shows significant potential")
    
    result.append("")
    result.append("="*80)
    
    return "\n".join(result)



def get_heatmap_data_json_tool(location_query: str, entity_ids: Optional[List[str]] = None, 
                         signals: Optional[QlooSignals] = None, limit: int = 50) -> dict:
    """
    Get all heatmap data points as JSON/dictionary from the heatmap API - simple version.
    
    :param client: QlooAPIClient instance (initialized with your API key)
    :param location_query: Location to analyze (e.g., "Toronto", "New York")
    :param entity_ids: Optional list of entity IDs for context
    :param signals: Optional QlooSignals object containing additional signals
    :param limit: Maximum number of location points to retrieve (max 50)
    :return: Dictionary containing heatmap data points directly from API
    """
    # Ensure limit is within API bounds (1-50)
    limit = min(max(limit, 1), 50)
    
    heatmap_result = client.get_heatmap_analysis(
        location_query=location_query,
        entity_ids=entity_ids,
        signals=signals,
        limit=limit
    )
    
    if not heatmap_result.get("success"):
        return {
            "success": False,
            "error": heatmap_result.get("error", "Heatmap analysis failed"),
            "heatmap_data": []
        }
    
    # Just return the raw heatmap data from API
    heatmap_data = heatmap_result.get('results', {}).get('heatmap', [])
    
    return {
        "success": True,
        "heatmap_data": heatmap_data,
        "total_points": len(heatmap_data),
        "location_query": location_query,
        "entity_ids_used": entity_ids or [],
        "limit_requested": limit
    }

def get_entity_ids(queries: List[str]):
    """
    Get entity IDs for a list of queries.
    
    Args:
        queries (List[str]): List of entity queries to search for.
        
    Returns:
        List[str]: List of found entity IDs.
    """

    all_entity_ids = []
    entity_details = {}

    print("🔍 Searching for entities to get IDs...")
    for query in queries:
        print(f"\n📍 Searching: '{query}'")
        
        result = client.search_entities(
            query=query,
            limit=2 # Just get top 2 per query
        )
        
        if result['success'] and result['entities']:
            entity = result['entities'][0]  # Take the top result
            all_entity_ids.append(entity.id)
            entity_details[entity.id] = {
                'name': entity.name,
                'type': entity.entity_type,
                'type_urn': entity.type_urn,
                'popularity': entity.popularity,
                'query': query
            }
    return entity_details


if __name__ == "__main__":
    # Example signals
    entity_signals = QlooSignals(
        demographics={"age": "55_and_older", "gender": "male"},
        location={"query": "Austin Texas"},
    )

    # Test all entity types
    print("=== INSIGHTS ===")
    insights = get_insights_tool(signals=entity_signals,entity=["artist","tag","movie","podcast","videogame","tv_show","people","place"])
    print(insights)

    # # Test demographics insights
    # print("=== DEMOGRAPHICS INSIGHTS ===")
    # print("Signals:", entity_signals)
    # demo_insights = get_demographics_insights_tool(entity_ids=["A21D248A-7379-458E-A3BE-7B8C4B961AF6","D719B77A-E9A2-4E07-BF7B-F6ED1C9521C6"], signals=entity_signals)
    # print(demo_insights)

    # # Test heatmap insights
    # print("=== HEATMAP INSIGHTS ===")
    # print("Signals:", entity_signals)
    # heatmap_insights = get_heatmap_insights_report_tool(location_query="Toronto", entity_ids=["A21D248A-7379-458E-A3BE-7B8C4B961AF6","D719B77A-E9A2-4E07-BF7B-F6ED1C9521C6"], signals=entity_signals)
    # print(heatmap_insights)





# ## 📊 **Qloo Metrics - Quick Reference**

# ### 🎯 **Affinity Score**
# **Range**: 0.0 - 1.0  
# **Definition**: Measures how strongly an entity matches your specific query signals (demographics, location, interests). Higher scores indicate greater relevance to your search criteria.
# - **0.9**: Extremely relevant to your query
# - **0.5**: Moderately relevant  
# - **0.1**: Weakly relevant

# ### ⭐ **Popularity**
# **Range**: 0.0 - 1.0  
# **Definition**: Represents an entity's overall popularity ranking compared to all other entities in the same category. Based on global signal activity, not query-specific.
# - **0.95**: Very popular globally (top 5%)
# - **0.5**: Average popularity (50th percentile)
# - **0.1**: Less popular/niche (bottom 10%)

# ### 📈 **Audience Growth**
# **Range**: Negative to Positive decimals  
# **Definition**: Indicates how an entity's audience interest has changed over a recent time period. Shows trending momentum.
# - **+0.05**: Growing audience (up trend)
# - **0.00**: Stable audience (no change)
# - **-0.03**: Declining audience (down trend)

# ---

# **Key Difference**: 
# - **Affinity** = "How relevant to MY query?"
# - **Popularity** = "How popular in general?"  
# - **Growth** = "Is it trending up or down?"