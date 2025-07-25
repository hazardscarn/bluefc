# setup_gcs_buckets.py
"""
Setup script to create required Google Cloud Storage buckets for image customization.
Run this once before using the image customization feature.
"""

import os
from google.cloud import storage
from google.cloud.exceptions import Conflict

def setup_gcs_buckets():
    """Create the required GCS buckets for image customization."""
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "energyagentai")
    
    if not project_id:
        print("❌ Error: GOOGLE_CLOUD_PROJECT environment variable not set")
        print("   Set it with: export GOOGLE_CLOUD_PROJECT=your-project-id")
        return False
    
    print(f"🚀 Setting up GCS buckets for project: {project_id}")
    print("=" * 60)
    
    try:
        # Initialize storage client
        storage_client = storage.Client(project=project_id)
        
        # Required buckets
        buckets_to_create = [
            f"{project_id}-bluefc-original-products",
            f"{project_id}-bluefc-customized-product"
        ]
        
        created_buckets = []
        existing_buckets = []
        
        for bucket_name in buckets_to_create:
            try:
                print(f"📦 Creating bucket: {bucket_name}")
                
                # Create bucket
                bucket = storage_client.bucket(bucket_name)
                bucket = storage_client.create_bucket(bucket, location="us-central1")
                
                # Set public read access for the customized images bucket
                if "customized-images" in bucket_name:
                    print(f"   🔓 Setting public read access...")
                    policy = bucket.get_iam_policy(requested_policy_version=3)
                    policy.bindings.append({
                        "role": "roles/storage.objectViewer",
                        "members": ["allUsers"]
                    })
                    bucket.set_iam_policy(policy)
                    print(f"   ✅ Public read access configured")
                
                created_buckets.append(bucket_name)
                print(f"   ✅ Created: {bucket_name}")
                
            except Conflict:
                existing_buckets.append(bucket_name)
                print(f"   ⚠️  Already exists: {bucket_name}")
                
                # Still try to set permissions for existing customized images bucket
                if "customized-images" in bucket_name:
                    try:
                        bucket = storage_client.bucket(bucket_name)
                        policy = bucket.get_iam_policy(requested_policy_version=3)
                        
                        # Check if public access already exists
                        has_public_access = any(
                            "allUsers" in binding.get("members", []) 
                            for binding in policy.bindings
                        )
                        
                        if not has_public_access:
                            print(f"   🔓 Adding public read access...")
                            policy.bindings.append({
                                "role": "roles/storage.objectViewer", 
                                "members": ["allUsers"]
                            })
                            bucket.set_iam_policy(policy)
                            print(f"   ✅ Public read access added")
                        else:
                            print(f"   ✅ Public read access already configured")
                            
                    except Exception as e:
                        print(f"   ⚠️  Could not verify/set permissions: {str(e)}")
                
            except Exception as e:
                print(f"   ❌ Failed to create {bucket_name}: {str(e)}")
                return False
        
        print("\n🎉 GCS Setup Complete!")
        print("=" * 60)
        
        if created_buckets:
            print("✅ Created buckets:")
            for bucket in created_buckets:
                print(f"   • {bucket}")
        
        if existing_buckets:
            print("⚠️  Existing buckets (verified):")
            for bucket in existing_buckets:
                print(f"   • {bucket}")
        
        print(f"\n📋 Bucket Summary:")
        print(f"   • Original images: gs://{project_id}-bluefc-original-products")
        print(f"   • Customized images: gs://{project_id}-bluefc-customized-product")
        print(f"   • Public access: Enabled for customized images")
        
        print(f"\n🚀 Ready to use image customization!")
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        print(f"\nMake sure you have:")
        print(f"   • Google Cloud SDK installed and authenticated")
        print(f"   • Storage Admin permissions on project {project_id}")
        print(f"   • Billing enabled on the project")
        return False


def verify_setup():
    """Verify that the setup is working correctly."""
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "energyagentai")
    
    print(f"\n🔍 Verifying setup...")
    print("-" * 40)
    
    try:
        storage_client = storage.Client(project=project_id)
        
        buckets_to_check = [
            f"{project_id}-bluefc-original-products",
            f"{project_id}-bluefc-customized-product"
        ]
        
        all_good = True
        
        for bucket_name in buckets_to_check:
            try:
                bucket = storage_client.bucket(bucket_name)
                bucket.reload()  # This will raise an exception if bucket doesn't exist
                print(f"   ✅ {bucket_name}: Accessible")
                
                # Check if we can write to the bucket
                test_blob = bucket.blob("test-access.txt")
                test_blob.upload_from_string("test")
                test_blob.delete()
                print(f"   ✅ {bucket_name}: Write access confirmed")
                
            except Exception as e:
                print(f"   ❌ {bucket_name}: {str(e)}")
                all_good = False
        
        if all_good:
            print(f"\n🎉 All systems ready for image customization!")
        else:
            print(f"\n⚠️  Some issues detected. Run setup again or check permissions.")
            
        return all_good
        
    except Exception as e:
        print(f"   ❌ Verification failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("🎨 Chelsea FC Image Customization - GCS Setup")
    print("=" * 60)
    
    success = setup_gcs_buckets()
    
    if success:
        verify_setup()
        print(f"\n💡 Next steps:")
        print(f"   1. Run your ADK agent")
        print(f"   2. Get product recommendations")
        print(f"   3. Request image customization with: 'customize product prod_XXX'")
    else:
        print(f"\n🔧 Troubleshooting:")
        print(f"   1. Ensure Google Cloud SDK is installed: gcloud --version")
        print(f"   2. Authenticate: gcloud auth application-default login") 
        print(f"   3. Set project: gcloud config set project {project_id}")
        print(f"   4. Enable Storage API: gcloud services enable storage.googleapis.com")
        print(f"   5. Check billing is enabled on your project")