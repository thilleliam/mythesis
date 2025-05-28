# deploy_check.py - Run this before deploying to check configuration
import os

def check_environment():
    """Check environment variables for deployment"""
    print("🔍 Checking deployment configuration...\n")
    
    # Required environment variables
    required_vars = {
        'DB_HOST': 'sql8.freesqldatabase.com',
        'DB_USER': 'sql8781735', 
        'DB_PASSWORD': 'YQ8d2QdLqV',
        'DB_NAME': 'sql8781735',
        'DB_PORT': '3306',
        'DATABASE_URL': 'mysql+pymysql://sql8781735:YQ8d2QdLqV@sql8.freesqldatabase.com:3306/sql8781735'
    }
    
    print("✅ Required environment variables for Render:")
    for var, value in required_vars.items():
        print(f"   {var}={value}")
    
    print("\n🔍 Current local environment:")
    for var in required_vars.keys():
        current_value = os.environ.get(var, "NOT SET")
        status = "✅" if current_value != "NOT SET" else "❌"
        print(f"   {status} {var}={current_value}")
    
    print("\n📋 Steps to fix Render deployment:")
    print("1. Go to Render Dashboard → Your Service → Environment")
    print("2. Add each of the required variables above")
    print("3. Click 'Save' and redeploy")
    print("4. Check logs for successful connection to sql8.freesqldatabase.com")
    
    # Check for problematic patterns in code
    print("\n🔍 Checking for hardcoded database references...")
    
    problematic_patterns = [
        "ec2-34-213-214-55.us-west-2.compute.amazonaws.com",
        "amazonaws.com"
    ]
    
    files_to_check = ['config.py', 'database.py', 'main.py']
    
    found_issues = False
    for file in files_to_check:
        if os.path.exists(file):
            with open(file, 'r') as f:
                content = f.read()
                for pattern in problematic_patterns:
                    if pattern in content:
                        print(f"❌ Found '{pattern}' in {file}")
                        found_issues = True
    
    if not found_issues:
        print("✅ No hardcoded AWS database references found")
    
    print("\n🚀 Deployment readiness:")
    if not found_issues:
        print("✅ Code appears ready for deployment")
        print("✅ Just ensure environment variables are set in Render")
    else:
        print("❌ Fix hardcoded database references before deploying")

if __name__ == "__main__":
    check_environment()