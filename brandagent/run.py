#!/usr/bin/env python3
"""
Simple Brand Analysis Test Runner

Run this script to test the brand analysis system:
python -m brandagent.run
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from google.adk.tools import ToolContext
    from dotenv import load_dotenv
    load_dotenv()
    
    # Try to import our modules
    from brandagent.tools import (
        detect_brands_in_text,
        get_entity_ids_with_context,
        get_demographics_insights_with_context,
        run_brand_analysis
    )
    from brandagent.agent import brand_analysis_agent, multi_agent_coordinator
    
    print("✅ All imports successful!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you have all required packages installed:")
    print("- google-adk")
    print("- python-dotenv") 
    print("- vertexai")
    sys.exit(1)


class SimpleToolContext:
    """Simple ToolContext implementation for testing"""
    def __init__(self):
        self.state = {}
        
    def __repr__(self):
        return f"SimpleToolContext(state_keys={list(self.state.keys())})"


def test_brand_detection():
    """Test brand detection functionality"""
    print("\n" + "="*60)
    print("🔍 TESTING BRAND DETECTION")
    print("="*60)
    
    test_messages = [
        "I love Chelsea Football Club and Manchester United",
        "Compare Nike vs Adidas for sports brands", 
        "Apple and Samsung are great tech companies",
        "No brands mentioned in this text"
    ]
    
    context = SimpleToolContext()
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📝 Test {i}: '{message}'")
        print("-" * 40)
        
        try:
            result = detect_brands_in_text(message, context)
            
            print(f"Success: {result.get('success')}")
            print(f"Brands found: {result.get('brands_detected', [])}")
            print(f"Total brands: {result.get('total_brands', 0)}")
            
            if result.get('success') and result.get('brands_detected'):
                print("✅ Brands detected successfully")
            elif result.get('success'):
                print("ℹ️  No brands found (expected for test 4)")
            else:
                print(f"❌ Error: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")


def test_entity_resolution():
    """Test entity ID resolution"""
    print("\n" + "="*60)
    print("🔗 TESTING ENTITY RESOLUTION")
    print("="*60)
    
    test_brands = ["Chelsea FC", "Nike", "Apple"]
    context = SimpleToolContext()
    
    print(f"📝 Testing brands: {test_brands}")
    print("-" * 40)
    
    try:
        result = get_entity_ids_with_context(test_brands, context)
        
        print(f"Success: {result.get('success')}")
        print(f"Entities found: {result.get('total_entities_found', 0)}")
        
        if result.get('success'):
            entity_details = result.get('entity_details', {})
            for entity_id, details in entity_details.items():
                print(f"  ✅ {details['name']}")
                print(f"     ID: {entity_id}")
                print(f"     Type: {details.get('type', 'Unknown')}")
                print(f"     Popularity: {details.get('popularity', 'Unknown')}")
        else:
            print(f"❌ Error: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")


def test_full_workflow():
    """Test the complete brand analysis workflow"""
    print("\n" + "="*60)
    print("🚀 TESTING FULL WORKFLOW")
    print("="*60)
    
    test_message = "Compare Chelsea Football Club with Arsenal FC"
    context = SimpleToolContext()
    
    print(f"📝 Test message: '{test_message}'")
    print("-" * 40)
    
    try:
        # Test using the run_brand_analysis function
        print("🔄 Running brand analysis...")
        result = run_brand_analysis(test_message, context)
        
        print(f"Success: {result.get('success')}")
        print(f"Agent used: {result.get('agent_used')}")
        print(f"Message: {result.get('message')}")
        
        if result.get('success'):
            analysis = result.get('analysis', 'No analysis returned')
            print(f"\n📊 ANALYSIS RESULT:")
            print("-" * 30)
            print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
        else:
            print(f"❌ Error: {result.get('error')}")
            
        # Show session state
        print(f"\n💾 SESSION STATE:")
        print("-" * 30)
        if context.state:
            for key in context.state.keys():
                print(f"  ✓ {key}")
        else:
            print("  (No state data)")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()


def interactive_test():
    """Interactive test mode"""
    print("\n" + "="*60)
    print("💬 INTERACTIVE TEST MODE")
    print("="*60)
    print("Enter a message with brand mentions (or 'quit' to exit)")
    
    context = SimpleToolContext()
    
    while True:
        try:
            user_input = input("\n👤 Your message: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not user_input:
                print("❌ Please enter a message")
                continue
                
            print(f"\n🔄 Analyzing: '{user_input}'")
            print("-" * 40)
            
            # Run brand detection first
            detection_result = detect_brands_in_text(user_input, context)
            print(f"🔍 Brands detected: {detection_result.get('brands_detected', [])}")
            
            # If brands found, run full analysis
            if detection_result.get('success') and detection_result.get('brands_detected'):
                print("🚀 Running full analysis...")
                
                analysis_result = run_brand_analysis(user_input, context)
                if analysis_result.get('success'):
                    analysis = analysis_result.get('analysis', '')
                    print(f"\n📊 ANALYSIS:")
                    print("-" * 20)
                    print(analysis[:300] + "..." if len(analysis) > 300 else analysis)
                else:
                    print(f"❌ Analysis failed: {analysis_result.get('error')}")
            else:
                print("ℹ️  No brands found - skipping full analysis")
                
        except KeyboardInterrupt:
            print("\n👋 Interrupted by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main test runner"""
    print("🚀 BRAND ANALYSIS SYSTEM TEST RUNNER")
    print("=" * 80)
    
    # Check environment
    qloo_key = os.getenv("QLOO_API_KEY")
    if not qloo_key:
        print("⚠️  Warning: QLOO_API_KEY not found in environment")
        print("   Some tests may fail without a valid API key")
    else:
        print("✅ QLOO_API_KEY found")
    
    print("\nSelect a test to run:")
    print("1. Brand Detection Test")
    print("2. Entity Resolution Test") 
    print("3. Full Workflow Test")
    print("4. Interactive Test")
    print("5. Run All Tests")
    print("q. Quit")
    
    while True:
        choice = input("\nEnter your choice (1-5 or q): ").strip()
        
        if choice == 'q':
            print("👋 Goodbye!")
            break
        elif choice == '1':
            test_brand_detection()
        elif choice == '2':
            test_entity_resolution()
        elif choice == '3':
            test_full_workflow()
        elif choice == '4':
            interactive_test()
        elif choice == '5':
            test_brand_detection()
            test_entity_resolution()
            test_full_workflow()
        else:
            print("❌ Invalid choice. Please enter 1-5 or q.")
            continue
            
        if choice != '4':  # Don't show menu again after interactive mode
            print(f"\n{'='*60}")
            print("Test completed! Choose another test or 'q' to quit.")


if __name__ == "__main__":
    main()