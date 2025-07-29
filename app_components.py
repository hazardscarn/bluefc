import streamlit as st
import time
import uuid
import json
import requests
import tempfile
import os
from typing import Dict, List, Any, Optional


def style_component():
    style="""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        /* Hide Streamlit elements */
        .stApp > header {background-color: transparent;}
        .stApp > header [data-testid="stHeader"] {display: none;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}

        /* Global styling */
        html, body, [class*="st"] {
            font-family: 'Inter', sans-serif;
            color: #1a1a1a;
        }

        .stApp {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        }

        /* Navigation */
        .nav-header {
            background: white;
            padding: 1.5rem 2rem;
            margin: -1rem -1rem 2rem -1rem;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            border-radius: 0 0 16px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .nav-logo {
            font-size: 1.1rem;
            font-weight: 600;
            color: #034694;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex: 1;
            max-width: 70%;
            line-height: 1.4;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }

        .status-connected {
            background: linear-gradient(135deg, #d1fae5, #10b981);
            color: #065f46;
            border: 1px solid #059669;
        }

        .status-disconnected {
            background: linear-gradient(135deg, #fef3c7, #f59e0b);
            color: #92400e;
            border: 1px solid #d97706;
        }

        /* Hero Section */
        .hero-section {
            background: linear-gradient(135deg, #034694 0%, #1e3c72 100%);
            color: white;
            padding: 3rem;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }

        .hero-title {
            font-size: 2.8rem;
            font-weight: 800;
            margin-bottom: 1rem;
            text-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }

        .hero-subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
            max-width: 600px;
            margin: 0 auto;
            line-height: 1.6;
        }

        /* Cards */
        .content-card {
            background: white;
            border-radius: 16px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
            border: 1px solid #e2e8f0;
            transition: all 0.3s ease;
        }

        .content-card:hover {
            box-shadow: 0 8px 32px rgba(0,0,0,0.12);
            transform: translateY(-2px);
        }

        /* Feature Cards */
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }

        .feature-card {
            background: white;
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border: 1px solid #e2e8f0;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .feature-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.15);
        }

        .feature-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }

        .feature-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: #034694;
            margin-bottom: 1rem;
        }

        .feature-description {
            color: #64748b;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }

        /* Status tracking */
        .status-pill {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem 1rem;
            border-radius: 12px;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.3s ease;
            margin: 0.25rem 0;
        }

        .status-pending {
            background: #f1f5f9;
            color: #64748b;
            border: 1px solid #e2e8f0;
        }

        .status-running {
            background: linear-gradient(135deg, #fef3c7, #fbbf24);
            color: #92400e;
            border: 1px solid #f59e0b;
            animation: pulse 2s infinite;
        }

        .status-completed {
            background: linear-gradient(135deg, #d1fae5, #10b981);
            color: #065f46;
            border: 1px solid #059669;
        }

        .status-error {
            background: linear-gradient(135deg, #fee2e2, #ef4444);
            color: #991b1b;
            border: 1px solid #dc2626;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }

        /* Product card styling */
        .product-card {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            margin: 0.5rem 0;
        }

        .product-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        }

        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #16a34a 0%, #15803d 100%) !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 0.75rem 2rem !important;
            border-radius: 12px !important;
            border: none !important;
            transition: all 0.3s ease !important;
            font-size: 1rem !important;
            box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3) !important;
        }

        .stButton > button:hover {
            background: linear-gradient(135deg, #15803d 0%, #166534 100%) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 20px rgba(22, 163, 74, 0.4) !important;
        }

        /* Customization button variant */
        .stButton.customization-button > button {
            background: linear-gradient(135deg, #034694 0%, #1e3c72 100%) !important;
            box-shadow: 0 4px 12px rgba(3, 70, 148, 0.3) !important;
        }

        .stButton.customization-button > button:hover {
            background: linear-gradient(135deg, #1e3c72 0%, #034694 100%) !important;
            box-shadow: 0 6px 20px rgba(3, 70, 148, 0.4) !important;
        }

        /* Loading animation */
        .loading-animation {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #16a34a;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Success callout */
        .success-callout {
            background: linear-gradient(135deg, #d1fae5, #a7f3d0);
            border: 1px solid #059669;
            border-radius: 12px;
            padding: 1rem;
            margin: 1rem 0;
            color: #065f46;
        }

        /* Error callout */
        .error-callout {
            background: linear-gradient(135deg, #fee2e2, #fecaca);
            border: 1px solid #dc2626;
            border-radius: 12px;
            padding: 1rem;
            margin: 1rem 0;
            color: #991b1b;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .hero-title { font-size: 2rem; }
            .feature-grid { grid-template-columns: 1fr; }
            .nav-header { 
                flex-direction: column; 
                text-align: center; 
                gap: 1rem; 
            }
            .nav-logo { 
                max-width: 100%; 
                text-align: center; 
            }
            .status-indicator {
                align-self: center;
            }
        }
        </style>
        """
    return style


def render_cultural_insights():
    """Render cultural insights in expandable sections with enhanced styling"""
    results = st.session_state.results
    
    if any([results.get("brand_insight"), results.get("movie_insight"), results.get("artist_insight"), results.get("podcast_insight"), results.get("tag_insight")]):
        st.markdown('<div class="content-card">', unsafe_allow_html=True)
        st.markdown("### 🧠 Cultural Insights")
        
        # Brand insights
        if results.get("brand_insight"):
            with st.expander("🏷️ **Brand Affinities**", expanded=False):
                display_brand_insights(results["brand_insight"])
        
        # Movie insights
        if results.get("movie_insight"):
            with st.expander("🎬 **Movie Preferences**", expanded=False):
                display_movie_insights(results["movie_insight"])
        
        # Artist insights
        if results.get("artist_insight"):
            with st.expander("🎵 **Music & Artists**", expanded=False):
                display_artist_insights(results["artist_insight"])
        
        # Podcast insights
        if results.get("podcast_insight"):
            with st.expander("🎧 **Podcast Preferences**", expanded=False):
                display_podcast_insights(results["podcast_insight"])
        
        # Tag insights
        if results.get("tag_insight"):
            with st.expander("🏷️ **Cultural Tags**", expanded=False):
                display_tag_insights(results["tag_insight"])
        
        st.markdown('</div>', unsafe_allow_html=True)

def display_brand_insights(brand_text):
    """Display brand insights in elegant cards"""
    st.markdown("#### 🛍️ Top Brand Affinities")
    
    # Parse brand data (simplified parsing)
    brands = []
    lines = brand_text.split('\n')
    current_brand = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('--- BRAND Rank'):
            if current_brand:
                brands.append(current_brand)
            current_brand = {}
        elif line.startswith('BRAND Name:'):
            current_brand['name'] = line.replace('BRAND Name:', '').strip()
        elif line.startswith('Brand Description:'):
            current_brand['description'] = line.replace('Brand Description:', '').strip()
        elif line.startswith('Affinity:'):
            current_brand['affinity'] = float(line.replace('Affinity:', '').strip())
    
    if current_brand:
        brands.append(current_brand)
    
    # Display brands in cards
    for i, brand in enumerate(brands[:6]):  # Show top 6
        affinity_percent = int(brand.get('affinity', 0) * 100)
        
        st.markdown(f'''
        <div style="
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border-left: 4px solid #3b82f6;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <h5 style="color: #1e40af; margin: 0; font-weight: 600;">#{i+1} {brand.get('name', 'Unknown Brand')}</h5>
                <span style="background: #3b82f6; color: white; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">
                    {affinity_percent}% Affinity
                </span>
            </div>
            <p style="color: #64748b; margin: 0; font-size: 0.9rem; line-height: 1.4;">
                {brand.get('description', 'No description available')}
            </p>
        </div>
        ''', unsafe_allow_html=True)

def display_movie_insights(movie_text):
    """Display movie insights in elegant cards"""
    st.markdown("#### 🎬 Top Movie Preferences")
    
    # Parse movie data
    movies = []
    lines = movie_text.split('\n')
    current_movie = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('--- MOVIE RANK'):
            if current_movie:
                movies.append(current_movie)
            current_movie = {}
        elif line.startswith('MOVIE Name:'):
            current_movie['name'] = line.replace('MOVIE Name:', '').strip()
        elif line.startswith('Content Rating:'):
            current_movie['rating'] = line.replace('Content Rating:', '').strip()
        elif line.startswith('Plot:'):
            current_movie['plot'] = line.replace('Plot:', '').strip()
        elif line.startswith('Affinity:'):
            current_movie['affinity'] = float(line.replace('Affinity:', '').strip())
    
    if current_movie:
        movies.append(current_movie)
    
    # Display movies
    for i, movie in enumerate(movies[:5]):
        affinity_percent = int(movie.get('affinity', 0) * 100)
        rating = movie.get('rating', 'Not Rated')
        
        st.markdown(f'''
        <div style="
            background: linear-gradient(135deg, #fef3c7 0%, #fbbf24 30%, #f59e0b 100%);
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(245, 158, 11, 0.2);
        ">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                <div>
                    <h5 style="color: #92400e; margin: 0; font-weight: 700;">🎬 {movie.get('name', 'Unknown Movie')}</h5>
                    <span style="background: #92400e; color: white; padding: 0.1rem 0.5rem; border-radius: 8px; font-size: 0.7rem; margin-top: 0.3rem; display: inline-block;">
                        {rating}
                    </span>
                </div>
                <span style="background: #065f46; color: white; padding: 0.3rem 0.8rem; border-radius: 16px; font-size: 0.8rem; font-weight: 600;">
                    {affinity_percent}% Affinity
                </span>
            </div>
            <p style="color: #78350f; margin: 0; font-size: 0.9rem; line-height: 1.4; font-style: italic;">
                "{movie.get('plot', 'No plot available')}"
            </p>
        </div>
        ''', unsafe_allow_html=True)

def display_artist_insights(artist_text):
    """Display artist insights in elegant cards"""
    st.markdown("#### 🎵 Top Artists & Musicians")
    
    # Parse artist data
    artists = []
    lines = artist_text.split('\n')
    current_artist = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('--- ARTIST Rank'):
            if current_artist:
                artists.append(current_artist)
            current_artist = {}
        elif line.startswith('ARTIST Name:'):
            current_artist['name'] = line.replace('ARTIST Name:', '').strip()
        elif line.startswith('Description:'):
            current_artist['description'] = line.replace('Description:', '').strip()
        elif line.startswith('Affinity:'):
            current_artist['affinity'] = float(line.replace('Affinity:', '').strip())
        elif 'monthly listeners' in line:
            current_artist['popularity'] = line
    
    if current_artist:
        artists.append(current_artist)
    
    # Display artists in a grid
    cols = st.columns(2)
    for i, artist in enumerate(artists[:4]):
        affinity_percent = int(artist.get('affinity', 0) * 100)
        
        with cols[i % 2]:
            st.markdown(f'''
            <div style="
                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                border: 2px solid #0ea5e9;
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 12px;
                text-align: center;
            ">
                <h5 style="color: #0c4a6e; margin: 0 0 0.5rem 0; font-weight: 700;">🎤 {artist.get('name', 'Unknown Artist')}</h5>
                <div style="background: #0ea5e9; color: white; padding: 0.3rem; border-radius: 8px; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.5rem;">
                    {affinity_percent}% Affinity
                </div>
                <p style="color: #075985; margin: 0; font-size: 0.85rem; line-height: 1.3;">
                    {artist.get('description', 'No description available')}
                </p>
            </div>
            ''', unsafe_allow_html=True)

def display_podcast_insights(podcast_text):
    """Display podcast insights in elegant format"""
    st.markdown("#### 🎧 Top Podcast Preferences")
    
    # Parse podcast data (simplified)
    podcasts = []
    lines = podcast_text.split('\n')
    current_podcast = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('--- PODCAST Rank'):
            if current_podcast:
                podcasts.append(current_podcast)
            current_podcast = {}
        elif line.startswith('PODCAST Name:'):
            # Handle the case where name and affinity are on the same line
            if 'Affinity:' in line:
                # Split by 'Affinity:' to separate name and affinity
                parts = line.split('Affinity:')
                current_podcast['name'] = parts[0].replace('PODCAST Name:', '').strip()
                if len(parts) > 1:
                    try:
                        current_podcast['affinity'] = float(parts[1].strip())
                    except ValueError:
                        current_podcast['affinity'] = 0.0
            else:
                # Just the name
                current_podcast['name'] = line.replace('PODCAST Name:', '').strip()
        elif line.startswith('Affinity:'):
            # Handle separate affinity line
            try:
                current_podcast['affinity'] = float(line.replace('Affinity:', '').strip())
            except ValueError:
                current_podcast['affinity'] = 0.0
        elif line.startswith('Rating:'):
            current_podcast['rating'] = line.replace('Rating:', '').strip()
        elif line.startswith('Content Rating:'):
            current_podcast['content_rating'] = line.replace('Content Rating:', '').strip()
        elif line.startswith('Description:'):
            current_podcast['description'] = line.replace('Description:', '').strip()
    
    if current_podcast:
        podcasts.append(current_podcast)
    
    # Display podcasts
    for i, podcast in enumerate(podcasts[:5]):
        affinity_percent = int(podcast.get('affinity', 0) * 100)
        rating = podcast.get('rating', 'Not Rated')
        content_rating = podcast.get('content_rating', '')
        
        st.markdown(f'''
        <div style="
            background: linear-gradient(135deg, #f3e8ff 0%, #ddd6fe 100%);
            border-left: 5px solid #8b5cf6;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 8px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <h5 style="color: #5b21b6; margin: 0; font-weight: 600; flex: 1;">🎧 {podcast.get('name', 'Unknown Podcast')}</h5>
                <div style="text-align: right;">
                    <div style="background: #8b5cf6; color: white; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.2rem;">
                        {affinity_percent}% Match
                    </div>
                    <div style="color: #7c3aed; font-size: 0.8rem; font-weight: 500;">
                        ⭐ {rating}
                    </div>
                    {f'<div style="color: #7c3aed; font-size: 0.7rem;">{content_rating}</div>' if content_rating else ''}
                </div>
            </div>
            <p style="color: #6b21a8; margin: 0; font-size: 0.9rem; line-height: 1.4;">
                {podcast.get('description', 'No description available')}
            </p>
        </div>
        ''', unsafe_allow_html=True)

def display_tag_insights(tag_text):
    """Display cultural tags in an elegant grid"""
    st.markdown("#### 🏷️ Cultural DNA Profile")
    st.markdown("*Tags that define your audience's cultural preferences*")
    
    # Parse tag data
    tags = []
    lines = tag_text.split('\n')
    current_tag = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('--- TAG Rank'):
            if current_tag:
                tags.append(current_tag)
            current_tag = {}
        elif line.startswith('TAG Name:'):
            current_tag['name'] = line.replace('TAG Name:', '').strip()
        elif line.startswith('Affinity:'):
            current_tag['affinity'] = float(line.replace('Affinity:', '').strip())
        elif line.startswith('Type:'):
            current_tag['type'] = line.replace('Type:', '').strip()
        elif line.startswith('Applies to:'):
            current_tag['applies_to'] = line.replace('Applies to:', '').strip()
    
    if current_tag:
        tags.append(current_tag)
    
    # Display tags in a responsive grid
    cols = st.columns(3)
    for i, tag in enumerate(tags[:9]):  # Show top 9 in 3x3 grid
        affinity_percent = int(tag.get('affinity', 0) * 100)
        
        with cols[i % 3]:
            st.markdown(f'''
            <div style="
                background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
                border: 1px solid #10b981;
                padding: 0.8rem;
                margin: 0.3rem 0;
                border-radius: 8px;
                text-align: center;
                min-height: 100px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <h6 style="color: #065f46; margin: 0 0 0.3rem 0; font-weight: 700; font-size: 0.9rem;">
                    {tag.get('name', 'Unknown Tag')}
                </h6>
                <div style="background: #10b981; color: white; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.7rem; font-weight: 600; margin: 0.2rem 0;">
                    {affinity_percent}% Affinity
                </div>
                <p style="color: #047857; margin: 0; font-size: 0.7rem;">
                    {tag.get('applies_to', 'General')}
                </p>
            </div>
            ''', unsafe_allow_html=True)