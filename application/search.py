# find_aws_refs.py - Find all AWS database references
import os
import re

def search_for_aws_references():
    """Search for AWS database references in all Python files"""
    aws_patterns = [
        r'ec2-34-213-214-55\.us-west-2\.compute\.amazonaws\.com',
        r'amazonaws\.com',
        r'mysql\+pymysql://[^@]*@ec2-[^/]*',
        r'DATABASE_URL.*amazonaws',
        r'DB_HOST.*amazonaws',
        r'host.*=.*ec2-'
    ]
    
    found_references = []
    
    # Search in all Python files
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['__pycache__', '.git', 'venv', 'node_modules']):
            continue
            
        for file in files:
            if file.endswith(('.py', '.env', '.yaml', '.yml')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        
                    for line_num, line in enumerate(lines, 1):
                        for pattern in aws_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                found_references.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'content': line.strip(),
                                    'pattern': pattern
                                })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return found_references

def check_environment_variables():
    """Check current environment variables"""
    env_vars = ['DATABASE_URL', 'DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    
    print("🔍 Current Environment Variables:")
    for var in env_vars:
        value = os.environ.get(var, "NOT SET")
        if "amazonaws" in str(value).lower():
            print(f"❌ {var}={value} (CONTAINS AWS REFERENCE!)")
        elif value != "NOT SET":
            print(f"✅ {var}={value}")
        else:
            print(f"⚪ {var}=NOT SET")

if __name__ == "__main__":
    print("🔍 Searching for AWS database references...")
    
    # Check environment variables first
    check_environment_variables()
    
    # Search files
    references = search_for_aws_references()
    
    if references:
        print(f"\n❌ Found {len(references)} AWS database references:")
        for ref in references:
            print(f"\nFile: {ref['file']}")
            print(f"Line {ref['line']}: {ref['content']}")
            print(f"Pattern: {ref['pattern']}")
    else:
        print("\n✅ No AWS database references found in files!")
    
    print("\n📋 Next steps:")
    print("1. Fix any AWS references found above")
    print("2. Set correct environment variables in Render:")
    print("   DB_HOST=sql8.freesqldatabase.com")
    print("   DATABASE_URL=mysql+pymysql://sql8781735:YQ8d2QdLqV@sql8.freesqldatabase.com:3306/sql8781735")
    print("3. Update model imports to use 'from application.database import Base'")
    print("4. Redeploy")
    