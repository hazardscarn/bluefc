# deploy_merchagent_official_way.py - Using Official Agent Engine Guidelines

import os
import sys
import uuid

print("🚀 MerchAgent Agent Engine Deployment (Official Method)")
print("=" * 60)

# Configuration
PROJECT_ID = "energyagentai"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://energyagentai-agent-staging-merchagent"

def check_prerequisites():
    """Check if all required files exist"""
    print("🔍 Checking prerequisites...")
    
    required_files = [
        './merchagent/agent.py',
        './merchagent/requirements.txt',
        './src/qloo.py', 
        './src/secret_manager.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   {file_path}")
        return False
    
    print("✅ All required files found")
    return True

def deploy_with_official_method():
    """Deploy using the official Agent Engine method with extra_packages"""
    
    # Add current directory to path for local imports
    sys.path.insert(0, '.')
    
    try:
        import vertexai
        from vertexai.preview import reasoning_engines
        from vertexai import agent_engines
        
        # Step 1: Initialize Vertex AI
        print("🔧 Initializing Vertex AI...")
        vertexai.init(
            project=PROJECT_ID,
            location=LOCATION,
            staging_bucket=STAGING_BUCKET,
        )
        print(f"   ✅ Project: {PROJECT_ID}")
        print(f"   ✅ Location: {LOCATION}")
        print(f"   ✅ Staging: {STAGING_BUCKET}")

        # Step 2: Import the agent locally (this works locally)
        print("🤖 Importing MerchAgent locally...")
        from merchagent.agent import root_agent
        print(f"   ✅ Agent imported: {root_agent.name}")
        print(f"   ✅ Agent model: {root_agent.model}")
        print(f"   ✅ Agent tools: {len(root_agent.tools)} tools")

        # Step 3: Wrap agent with AdkApp
        print("🎁 Wrapping agent with AdkApp...")
        app = reasoning_engines.AdkApp(
            agent=root_agent,
            enable_tracing=True,
        )
        print("   ✅ Agent wrapped for Agent Engine")

        # Step 4: Read requirements from merchagent folder
        print("📋 Reading agent-specific requirements...")
        requirements_file = './merchagent/requirements.txt'
        with open(requirements_file, 'r') as f:
            requirements_content = f.read()
        
        # Parse requirements into list
        requirements = []
        for line in requirements_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)
        
        print(f"   ✅ {len(requirements)} requirements loaded")
        print("   📦 Requirements:")
        for req in requirements[:6]:
            print(f"      {req}")
        if len(requirements) > 6:
            print(f"      ... and {len(requirements) - 6} more")

        # Step 5: Define extra_packages (OFFICIAL METHOD)
        print("📁 Defining extra packages...")
        extra_packages = [
            "merchagent",  # Include entire merchagent directory
            "src"          # Include entire src directory
        ]
        
        print("   ✅ Extra packages:")
        for pkg in extra_packages:
            print(f"      {pkg}/")

        # Step 6: Define environment variables (Agent Engine provides GOOGLE_CLOUD_* automatically)
        print("🔐 Setting up environment variables...")
        env_vars = None  # Agent Engine provides GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION automatically
        
        print("   ✅ Environment variables configured (using Agent Engine defaults)")

        # Step 7: Generate unique GCS directory name
        gcs_dir_name = f"merchagent-{str(uuid.uuid4())[:8]}"
        print(f"   📂 GCS directory: {gcs_dir_name}")

        # Step 8: Deploy using OFFICIAL method
        print("\n🚀 Deploying to Vertex AI Agent Engine...")
        print("⏰ This takes 5-10 minutes - time for coffee! ☕")
        print("🔄 Official deployment process:")
        print("   - Bundling local packages")
        print("   - Uploading to Cloud Storage")
        print("   - Building container image") 
        print("   - Starting HTTP servers")
        print("   - Setting up auto-scaling")
        
        remote_agent = agent_engines.create(
            app,                           # The AdkApp-wrapped agent
            requirements=requirements,     # From merchagent/requirements.txt
            extra_packages=extra_packages, # Local directories to include
            env_vars=env_vars,            # Environment variables
            gcs_dir_name=gcs_dir_name,    # Unique folder name
            display_name="MerchAgent",    # Display name
            description="Chelsea FC Merchandise Recommendation Agent with cultural insights and product customization"
        )
        
        print("\n🎉 DEPLOYMENT SUCCESSFUL!")
        print("=" * 60)
        print(f"🔗 Resource Name: {remote_agent.resource_name}")
        print(f"🌐 Agent Engine UI: https://console.cloud.google.com/vertex-ai/reasoning-engines?project={PROJECT_ID}")
        
        return remote_agent
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        print("\n🔍 Error details:")
        import traceback
        traceback.print_exc()
        return None

def test_deployed_agent(remote_agent):
    """Test the deployed agent"""
    print("\n🧪 Testing deployed MerchAgent...")
    
    try:
        # Create session
        session = remote_agent.create_session(user_id="test_user")
        session_id = session["id"]
        print(f"   ✅ Session created: {session_id}")
        
        # Test query
        test_query = "What products for young soccer fans in Los Angeles?"
        print(f"\n🔍 Test query: '{test_query}'")
        
        events = list(remote_agent.stream_query(
            user_id="test_user",
            session_id=session_id,
            message=test_query,
        ))
        
        print(f"   ✅ {len(events)} events generated")
        
        # Show response preview
        for event in events[-2:]:
            if 'parts' in event:
                for part in event['parts']:
                    if 'text' in part and len(part['text']) > 50:
                        text_preview = part['text'][:200]
                        print(f"   🤖 Response: {text_preview}...")
                        break
        
        print("\n✅ MerchAgent is working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        return False

def main():
    """Main deployment workflow using official method"""
    
    print("Starting MerchAgent deployment using OFFICIAL Agent Engine method")
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print()
    
    # Check we're in the right directory
    if not os.path.exists('./merchagent') or not os.path.exists('./src'):
        print("❌ Please run this script from the 'bluefc' directory")
        print("\nExpected structure:")
        print("bluefc/")
        print("├── merchagent/")
        print("│   ├── agent.py")
        print("│   ├── requirements.txt")
        print("│   └── ...")
        print("├── src/")
        print("│   ├── qloo.py")
        print("│   └── secret_manager.py")
        return None
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed")
        return None
    
    # Deploy using official method
    print("\n" + "=" * 60)
    print("OFFICIAL AGENT ENGINE DEPLOYMENT")
    print("=" * 60)
    
    remote_agent = deploy_with_official_method()
    if not remote_agent:
        print("\n❌ Deployment failed")
        return None
    
    # Test the deployment
    test_success = test_deployed_agent(remote_agent)
    
    # Final summary
    print("\n" + "=" * 60)
    print("DEPLOYMENT COMPLETE!")
    print("=" * 60)
    
    if test_success:
        print("🎉 MerchAgent successfully deployed using official method!")
    else:
        print("⚠️ MerchAgent deployed but testing had issues")
    
    print(f"\n🎯 Next steps:")
    print(f"1. Visit: https://console.cloud.google.com/vertex-ai/reasoning-engines?project={PROJECT_ID}")
    print(f"2. Find 'MerchAgent' in the list")
    print(f"3. Click to access the chat interface")
    print(f"4. Test with: 'What products for soccer fans in New York?'")
    
    print(f"\n📚 What this official method does:")
    print(f"• Uses extra_packages to include local directories")
    print(f"• Maintains original module structure")
    print(f"• Follows Google's recommended best practices")
    print(f"• Handles secrets through environment variables")
    
    return remote_agent

if __name__ == "__main__":
    # Set environment variables
    os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
    os.environ["GOOGLE_CLOUD_LOCATION"] = LOCATION
    
    print("🎯 MerchAgent → Agent Engine (Official Method)")
    print("=" * 60)
    
    remote_agent = main()
    
    if remote_agent:
        print(f"\n🎊 SUCCESS! Resource: {remote_agent.resource_name}")
    else:
        print(f"\n💥 Deployment failed. Check errors above.")