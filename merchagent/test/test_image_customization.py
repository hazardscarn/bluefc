# test_image_customization.py
"""
Test script to verify image customization functionality works correctly.
"""

import os
import sys

# Add your project root to Python path if needed
# sys.path.append('/path/to/your/project')

# Import your customization function
try:
    from ..product_customization import customize_product_image_function
    print("✅ Successfully imported image customization function")
except ImportError as e:
    print(f"❌ Failed to import customization function: {e}")
    print(f"   Make sure cultural_image_tool.py is in your Python path")
    sys.exit(1)

def create_test_state():
    """Create a mock state with test data similar to your real recommendations."""
    
    return {
        'recommendations': [
            {
                'id': 408,
                'product_id': 'prod_394',
                'name': 'Chelsea New Era Floral Bucket Hat - Black - Unisex',
                'type': 'Headwear',
                'description': 'Chelsea New Era Floral Bucket Hat - Black - Unisex. This headwear is part of our Accessories collection. Excellent value at USD 28, offering quality at a fair price.',
                'price': 28,
                'currency': 'USD',
                'image_url': 'https://images.footballfanatics.com/chelsea/chelsea-new-era-floral-bucket-hat-black-unisex_ss5_p-200498205+u-rhooymcrvpqwkcznmgub+v-rviybbenbvfwmr2h4epw.jpg?_hv=2&w=532',
                'category': 'Accessories',
                'availability': 'In Stock',
                'price_class': 'Medium',
                'tags': ['gift-worthy', 'mid-range', 'fan-accessory'],
                'similarity': 0.647520982092429
            },
            {
                'id': 258,
                'product_id': 'prod_244',
                'name': 'Chelsea Nike Dri-FIT ADV Home Match Shirt 2025-26 - Kids with Palmer 10 printing',
                'type': 'Shirt',
                'description': 'Chelsea Nike Dri-FIT ADV Home Match Shirt 2025-26 - Kids with Palmer 10 printing. Premium quality at USD 182, representing the finest in Chelsea merchandise.',
                'price': 182,
                'currency': 'USD',
                'image_url': 'https://images.footballfanatics.com/chelsea/chelsea-nike-dri-fit-adv-home-match-shirt-2025-26-kids-with-palmer-10-printing_ss5_p-203072538+u-0bw2wdzeubcbqfnlcpqh+v-zudbhtmdvqjzm5pc7zun.jpg?_hv=2&w=532',
                'category': 'Kits',
                'availability': 'In Stock',
                'price_class': 'High',
                'tags': ['current', 'brand-quality', 'latest-season', 'performance', 'premium'],
                'similarity': 0.659149949936528
            }
        ],
        'persona_name': 'The Global Maverick Fan',
        'persona_description': 'A young, tech-savvy Chelsea FC fan who values unique style and cultural expression.',
        'cultural_values': {
            'entertainment_preferences': 'Enjoys contemporary music, tech culture, and unique fashion statements.',
            'brand_affinities': 'Prefers innovative brands that blend tradition with modern aesthetics.',
            'social_behaviors': 'Active on social media, values individuality and cultural authenticity.'
        },
        'audience_profile': {
            'demographics': 'Young adult, tech-oriented, global perspective',
            'lifestyle': 'Digital native, values unique expression and cultural fusion',
            'values': 'Innovation, authenticity, cultural pride, individual expression'
        }
    }

class MockToolContext:
    """Mock ToolContext for testing."""
    
    def __init__(self, state_data):
        self.state = state_data

def test_bucket_hat_customization():
    """Test customizing the bucket hat (prod_394)."""
    
    print("\n🧢 Testing Bucket Hat Customization")
    print("-" * 50)
    
    # Create mock context with test data
    test_state = create_test_state()
    mock_context = MockToolContext(test_state)
    
    product_id = "prod_394"  # The bucket hat from your logs
    
    print(f"📦 Product: {test_state['recommendations'][0]['name']}")
    print(f"🎯 Persona: {test_state['persona_name']}")
    print(f"🌐 Original URL: {test_state['recommendations'][0]['image_url']}")
    
    try:
        print(f"\n🚀 Starting customization...")
        result = customize_product_image_function(product_id, mock_context)
        
        if result.get('success'):
            print(f"✅ Customization successful!")
            print(f"🖼️  Original image: {result.get('original_image_url', 'N/A')}")
            print(f"🎨 Customized image: {result.get('customized_image_url', 'N/A')}")
            print(f"📝 Product name: {result.get('product_name', 'N/A')}")
            print(f"\n💡 Reasoning:")
            print(f"   {result.get('customization_reasoning', 'N/A')}")
            
            return True
        else:
            print(f"❌ Customization failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_jersey_customization():
    """Test customizing the jersey (prod_244)."""
    
    print("\n👕 Testing Jersey Customization")
    print("-" * 50)
    
    # Create mock context with test data
    test_state = create_test_state()
    mock_context = MockToolContext(test_state)
    
    product_id = "prod_244"  # The jersey
    
    print(f"📦 Product: {test_state['recommendations'][1]['name']}")
    print(f"🎯 Persona: {test_state['persona_name']}")
    print(f"🌐 Original URL: {test_state['recommendations'][1]['image_url']}")
    
    try:
        print(f"\n🚀 Starting customization...")
        result = customize_product_image_function(product_id, mock_context)
        
        if result.get('success'):
            print(f"✅ Customization successful!")
            print(f"🖼️  Original image: {result.get('original_image_url', 'N/A')}")
            print(f"🎨 Customized image: {result.get('customized_image_url', 'N/A')}")
            print(f"📝 Product name: {result.get('product_name', 'N/A')}")
            print(f"\n💡 Reasoning:")
            print(f"   {result.get('customization_reasoning', 'N/A')}")
            
            return True
        else:
            print(f"❌ Customization failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_environment_checks():
    """Check that the environment is set up correctly."""
    
    print("🔍 Environment Checks")
    print("-" * 30)
    
    # Check environment variables
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if project_id:
        print(f"✅ GOOGLE_CLOUD_PROJECT: {project_id}")
    else:
        print("❌ GOOGLE_CLOUD_PROJECT not set")
        return False
    
    # Check Google Cloud authentication
    try:
        from google.cloud import storage
        storage_client = storage.Client(project=project_id)
        # Try to list buckets to verify authentication
        list(storage_client.list_buckets(max_results=1))
        print(f"✅ Google Cloud authentication working")
    except Exception as e:
        print(f"❌ Google Cloud authentication failed: {str(e)}")
        return False
    
    # Check if required buckets exist
    required_buckets = [
        f"{project_id}-bluefc-original-products",
        f"{project_id}-bluefc-customized-product"
    ]
    
    for bucket_name in required_buckets:
        try:
            bucket = storage_client.bucket(bucket_name)
            bucket.reload()
            print(f"✅ Bucket exists: {bucket_name}")
        except Exception as e:
            print(f"❌ Bucket missing: {bucket_name} - {str(e)}")
            print(f"   Run: python setup_gcs_buckets.py")
            return False
    
    return True

if __name__ == "__main__":
    print("🎨 Chelsea FC Image Customization - Test Suite")
    print("=" * 60)
    
    # Run environment checks first
    if not run_environment_checks():
        print(f"\n❌ Environment checks failed. Fix issues before testing.")
        sys.exit(1)
    
    print(f"\n🧪 Running Tests")
    print("=" * 30)
    
    # Test both products
    tests_passed = 0
    total_tests = 2
    
    if test_bucket_hat_customization():
        tests_passed += 1
    
    if test_jersey_customization():
        tests_passed += 1
    
    print(f"\n📊 Test Results")
    print("=" * 30)
    print(f"✅ Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print(f"🎉 All tests passed! Image customization is working correctly.")
    else:
        print(f"⚠️  Some tests failed. Check the error messages above.")
        sys.exit(1)