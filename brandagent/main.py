#!/usr/bin/env python3
"""
Brand Analysis Agent - ADK Session Management Example

This file demonstrates how to properly set up and run the Brand Analysis Agent
using ADK's session management and runner patterns.

Usage:
    python main.py
"""

import asyncio
import os
from dotenv import load_dotenv
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

# Import the root agent and configuration
from brandagent.agent import root_agent, APP_NAME, USER_ID, SESSION_ID, initialize_session_state

load_dotenv()

async def async_main():
    """
    Main asynchronous function demonstrating ADK session management and agent execution.
    """
    print("🚀 [MAIN] Starting Brand Analysis Agent with ADK Session Management")
    print("=" * 80)
    
    # --- Step 1: Service Initialization ---
    print("🔧 [MAIN] Step 1: Initializing ADK services")
    
    # Use in-memory session service for demo/testing
    session_service = InMemorySessionService()
    
    # Create a new user session to maintain conversation state
    session = session_service.create_session(
        state=initialize_session_state(),  # Initial session state for brand analysis
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    
    print(f"✅ [MAIN] Session created - ID: {session.id}, User: {session.user_id}")
    print(f"📝 [MAIN] Initial state keys: {list(session.state.keys())}")
    
    # --- Step 2: Initialize ADK Runner ---
    print("\n🔧 [MAIN] Step 2: Creating ADK Runner")
    
    runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        session_service=session_service,
    )
    
    print(f"✅ [MAIN] Runner created with agent: {root_agent.name}")
    print(f"🛠️ [MAIN] Agent has {len(root_agent.tools)} tools available")
    
    # --- Step 3: Test with Brand Analysis Query ---
    print("\n🧪 [MAIN] Step 3: Testing Brand Analysis")
    
    # Test queries for brand analysis
    test_queries = [
        "Compare Chelsea Football Club with Arsenal FC",
        "Analyze Nike vs Adidas demographics",
        "What are the differences between Apple and Samsung?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 [MAIN] Test {i}: '{query}'")
        print("-" * 50)
        
        # Format the query into Content structure expected by ADK Runner
        content = types.Content(role='user', parts=[types.Part(text=query)])
        
        print(f"🤖 [MAIN] Running agent...")
        
        try:
            # Run the agent asynchronously
            events_async = runner.run_async(
                session_id=session.id,
                user_id=session.user_id,
                new_message=content
            )
            
            # Process events from the agent
            final_response_content = "No final response received."
            event_count = 0
            
            async for event in events_async:
                event_count += 1
                print(f"📡 [MAIN] Event {event_count}: {type(event).__name__}")
                
                # Check for final response
                if hasattr(event, 'final_response') and event.final_response:
                    if hasattr(event, 'content') and event.content:
                        # Extract text content from the final response
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                final_response_content = part.text
                                break
            
            print(f"✅ [MAIN] Agent completed after {event_count} events")
            print(f"📊 [MAIN] Response preview: {final_response_content[:200]}...")
            
            # Check updated session state
            updated_session = session_service.get_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=SESSION_ID
            )
            
            if updated_session and updated_session.state:
                state_keys = list(updated_session.state.keys())
                brand_keys = [k for k in state_keys if k.startswith('brand_') or k.startswith('detected_')]
                
                print(f"💾 [MAIN] Session state updated - Brand analysis keys: {brand_keys}")
                
                # Show detected brands if available
                if 'detected_brands' in updated_session.state:
                    detected = updated_session.state['detected_brands']
                    if isinstance(detected, dict) and 'brands' in detected:
                        brands = detected['brands']
                        print(f"🏷️ [MAIN] Brands detected in session: {brands}")
            
        except Exception as e:
            print(f"❌ [MAIN] Error running agent: {e}")
            import traceback
            traceback.print_exc()
        
        if i < len(test_queries):
            print(f"\n⏳ [MAIN] Pausing before next test...")
            await asyncio.sleep(1)
    
    # --- Step 4: Session Summary ---
    print(f"\n📋 [MAIN] Step 4: Final Session Summary")
    print("-" * 50)
    
    final_session = session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    
    if final_session and final_session.state:
        print(f"📊 [MAIN] Final session state keys: {list(final_session.state.keys())}")
        
        # Check for complete analysis workflow
        workflow_status = {
            "brands_detected": 'detected_brands' in final_session.state,
            "entities_resolved": 'brand_entity_details' in final_session.state,
            "demographics_analyzed": 'brand_demographics' in final_session.state,
            "insights_collected": 'all_brand_insights' in final_session.state,
            "final_report": 'brand_analysis_report' in final_session.state
        }
        
        print(f"🔍 [MAIN] Workflow completion status:")
        for step, completed in workflow_status.items():
            status = "✅" if completed else "❌"
            print(f"   {status} {step}: {completed}")
    
    print("\n" + "=" * 80)
    print("✅ [MAIN] Brand Analysis Agent session management demo completed!")
    print(f"🎯 [MAIN] Agent '{root_agent.name}' is ready for ADK web interface")

def main():
    """
    Synchronous entry point for the application.
    """
    print("🏃 [MAIN] Starting Brand Analysis Agent")
    
    # Check environment
    required_env_vars = ["GOOGLE_CLOUD_PROJECT", "QLOO_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️ [MAIN] Warning: Missing environment variables: {missing_vars}")
        print(f"📝 [MAIN] Some features may not work without proper configuration")
    else:
        print(f"✅ [MAIN] Environment variables configured")
    
    try:
        # Run the async main function
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print(f"\n👋 [MAIN] Interrupted by user")
    except Exception as e:
        print(f"\n❌ [MAIN] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()