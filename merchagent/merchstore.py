import os
import pandas as pd
import time
import re
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from supabase import create_client, Client
import logging
from abc import ABC
import vertexai
from vertexai.language_models import TextEmbeddingModel
from .config import SecretConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChelseaEmbedderAgent(ABC):
    """
    Embedder Agent following your proven pattern for Chelsea merchandise
    """
    
    def __init__(self, mode='vertex', embeddings_model='text-embedding-005'):
        if mode == 'vertex':
            self.mode = mode
            self.model = TextEmbeddingModel.from_pretrained(embeddings_model)
        else:
            raise ValueError('EmbedderAgent mode must be vertex')
    
    def create(self, question):
        """Text embedding with a Large Language Model."""
        
        if self.mode == 'vertex':
            if isinstance(question, str):
                embeddings = self.model.get_embeddings([question])
                for embedding in embeddings:
                    vector = embedding.values
                return vector
            
            elif isinstance(question, list):
                vector = list()
                for q in question:
                    embeddings = self.model.get_embeddings([q])
                    for embedding in embeddings:
                        vector.append(embedding.values)
                return vector
            
            else:
                raise ValueError('Input must be either str or list')

class ChelseaMerchandise:
    """
    Chelsea Merchandise Vector DB Retrieval
    """
    
    def __init__(self,  location: str = "us-central1"):
        # Load environment variables
        load_dotenv()
        
        # Initialize Supabase
        # self.supabase_url = os.getenv("REACT_APP_SUPABASE_URL")
        # self.supabase_key = os.getenv("SUPABASE_SECRET_KEY")
        # self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        
        # if not all([self.supabase_url, self.supabase_key]):
        #     raise ValueError("Missing Supabase environment variables")

        # Get secrets from Secret Manager with fallbacks
        try:
            self.supabase_url = SecretConfig.get_supabase_url()
            self.supabase_key = SecretConfig.get_supabase_secret_key()
            self.project_id = SecretConfig.get_google_cloud_project()
            
            logger.info("✅ Successfully retrieved secrets from Secret Manager")
        except Exception as e:
            logger.error(f"❌ Failed to retrieve secrets: {e}")
            raise ValueError("Missing required secrets for Supabase connection")

        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize Vertex AI using your proven pattern
        vertexai.init(project=self.project_id, location=location)
        
        # Initialize embedder using your exact pattern
        self.embedder = ChelseaEmbedderAgent('vertex', 'text-embedding-005')
        
        logger.info(f"✅ Initialized Chelsea loader with proven embedding pattern")
    

    def _ensure_balanced_diversity(self, results: List[Dict], target_count: int, match_threshold: float = 0.3) -> List[Dict]:
        """
        Balanced diversity rules:
        1. Allow max 2 products of same type
        2. Only add more of same type if no other types meet threshold
        3. Prioritize similarity quality
        """
        
        if len(results) <= target_count:
            return results
        
        # Sort by similarity score (highest first)
        results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        
        diverse_results = []
        type_counts = {}
        
        for result in results:
            if len(diverse_results) >= target_count:
                break
                
            product_type = result.get('type', 'Unknown')
            similarity = result.get('similarity', 0)
            current_type_count = type_counts.get(product_type, 0)
            
            # Check if we should add this product
            should_add = False
            
            if current_type_count == 0:
                # First of this type - always add if above threshold
                should_add = similarity >= match_threshold
                
            elif current_type_count == 1:
                # Second of this type - add if above threshold
                should_add = similarity >= match_threshold
                
            else:
                # Third+ of this type - only add if no other types available above threshold
                # Check if there are other types still available above threshold
                other_types_available = False
                for other_result in results:
                    if other_result in diverse_results:
                        continue
                    other_type = other_result.get('type', 'Unknown')
                    other_similarity = other_result.get('similarity', 0)
                    other_count = type_counts.get(other_type, 0)
                    
                    if other_type != product_type and other_count < 2 and other_similarity >= match_threshold:
                        other_types_available = True
                        break
                
                # Only add if no other types available AND this one is still good quality
                should_add = not other_types_available and similarity >= match_threshold
            
            if should_add:
                diverse_results.append(result)
                type_counts[product_type] = current_type_count + 1
        
        # Log what we achieved
        logger.info(f"🎯 Balanced diversity results:")
        # logger.info(f"Total {target_count} used:")

        for ptype, count in type_counts.items():
            logger.info(f"   {ptype}: {count} products")
        
        return diverse_results

    def search_diverse_products(self, query: str, match_count: int = 6, match_threshold: float = 0.3) -> List[Dict]:
        """Search with balanced diversity - max 2 per type, quality first"""
        try:
            query_embedding = self.embedder.create(query)
            
            # Get 3x more results for diversity selection
            initial_count = min(match_count * 3, 40)
            
            response = self.supabase.rpc(
                'match_merchandise',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': match_threshold,
                    'match_count': initial_count
                }
            ).execute()
            
            results = response.data
            if not results:
                return []
            
            # Apply your specific balanced diversity rules
            diverse_results = self._ensure_balanced_diversity(results, match_count, match_threshold)
            
            return diverse_results
            
        except Exception as e:
            logger.error(f"Error searching diverse products: {e}")
            return []
    def search_similar_products(self, query: str, match_count: int = 3, match_threshold: float = 0.3, diverse: bool = True) -> List[Dict]:
        """Search for similar products using your proven embedding pattern"""
        if diverse:
            return self.search_diverse_products(query, match_count, match_threshold)
        else:
            try:
                # Generate embedding using your proven pattern
                query_embedding = self.embedder.create(query)
                
                # Search using the RPC function
                response = self.supabase.rpc(
                    'match_merchandise',
                    {
                        'query_embedding': query_embedding,
                        'match_threshold': match_threshold,
                        'match_count': match_count
                    }
                ).execute()
                
                return response.data
                
            except Exception as e:
                logger.error(f"Error searching products: {e}")
                return []
