#!/usr/bin/env python3
"""
OWASP ZAP Baseline Security Scan for RPSLS Application
This script performs automated security testing using ZAP proxy
"""

import subprocess
import sys
import os
import json
from datetime import datetime

# Configuration
WEB_URL = os.getenv('WEB_URL', 'http://192.168.64.153:30081')
API_URL = os.getenv('API_URL', 'http://192.168.64.153:30080')
ZAP_PORT = os.getenv('ZAP_PORT', '8090')
REPORT_DIR = 'reports/security'

def run_zap_baseline(target_url, report_name):
    """Run ZAP baseline scan against target URL"""
    print(f"🔍 Starting ZAP baseline scan for {target_url}")
    
    # Ensure report directory exists
    os.makedirs(REPORT_DIR, exist_ok=True)
    
    # ZAP baseline scan command
    cmd = [
        'docker', 'run', '--rm',
        '-v', f'{os.getcwd()}/{REPORT_DIR}:/zap/wrk:rw',
        '-u', 'zap',
        'ghcr.io/zaproxy/zaproxy:stable',
        'zap-baseline.py',
        '-t', target_url,
        '-r', f'{report_name}_baseline.html',
        '-J', f'{report_name}_baseline.json',
        '-x', f'{report_name}_baseline.xml',
        '-w', f'{report_name}_baseline.md',
        '--hook=/zap/auth_hook.py',
        '-z', '-config api.key=rpsls-security-test'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        print(f"✅ ZAP scan completed for {target_url}")
        print(f"📊 Reports saved to {REPORT_DIR}/")
        
        # Parse JSON report for summary
        try:
            with open(f'{REPORT_DIR}/{report_name}_baseline.json', 'r') as f:
                report_data = json.load(f)
                print_scan_summary(report_data, report_name)
        except FileNotFoundError:
            print(f"⚠️  JSON report not found for {report_name}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"❌ ZAP scan timeout for {target_url}")
        return False
    except Exception as e:
        print(f"❌ ZAP scan failed for {target_url}: {str(e)}")
        return False

def print_scan_summary(report_data, scan_name):
    """Print summary of scan results"""
    print(f"\n📋 {scan_name.upper()} SCAN SUMMARY")
    print("=" * 40)
    
    if 'site' in report_data:
        for site in report_data['site']:
            alerts = site.get('alerts', [])
            
            # Count alerts by risk level
            risk_counts = {'High': 0, 'Medium': 0, 'Low': 0, 'Informational': 0}
            for alert in alerts:
                risk = alert.get('riskdesc', '').split(' ')[0]
                if risk in risk_counts:
                    risk_counts[risk] += 1
            
            print(f"🎯 Target: {site.get('@name', 'Unknown')}")
            print(f"🔴 High Risk: {risk_counts['High']}")
            print(f"🟡 Medium Risk: {risk_counts['Medium']}")
            print(f"🟢 Low Risk: {risk_counts['Low']}")
            print(f"ℹ️  Informational: {risk_counts['Informational']}")
            print(f"📊 Total Alerts: {len(alerts)}")
            
            # Show high/medium risk alerts
            if risk_counts['High'] > 0 or risk_counts['Medium'] > 0:
                print("\n⚠️  CRITICAL ISSUES FOUND:")
                for alert in alerts:
                    risk = alert.get('riskdesc', '').split(' ')[0]
                    if risk in ['High', 'Medium']:
                        print(f"  • {alert.get('name', 'Unknown')} ({risk} Risk)")

def create_auth_hook():
    """Create authentication hook for ZAP"""
    auth_hook_content = '''
# Authentication hook for RPSLS application
def authenticate(self, helper, paramsValues, credentials):
    """
    This hook can be used to authenticate to the RPSLS application
    Currently, the app doesn't require authentication for basic functionality
    """
    pass

def getRequiredParamsNames():
    return []

def getOptionalParamsNames():
    return []

def getCredentialsParamsNames():
    return []
'''
    
    with open(f'{REPORT_DIR}/auth_hook.py', 'w') as f:
        f.write(auth_hook_content)

def run_security_tests():
    """Run complete security test suite"""
    print("🛡️  RPSLS Security Test Suite")
    print("=" * 50)
    
    # Create auth hook
    create_auth_hook()
    
    # Test results
    results = {}
    
    # Test 1: Web Application Security
    print("\n🌐 Testing Web Application Security...")
    results['web'] = run_zap_baseline(WEB_URL, 'web_app')
    
    # Test 2: API Security
    print("\n🔌 Testing API Security...")
    results['api'] = run_zap_baseline(API_URL, 'api')
    
    # Test 3: Swagger UI Security (if accessible)
    print("\n📚 Testing Swagger UI Security...")
    results['swagger'] = run_zap_baseline(f"{API_URL}/swagger", 'swagger')
    
    # Generate summary report
    generate_summary_report(results)
    
    return all(results.values())

def generate_summary_report(results):
    """Generate HTML summary report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>RPSLS Security Test Summary</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
            .test-result {{ margin: 20px 0; padding: 15px; border-radius: 5px; }}
            .pass {{ background: #d4edda; border-left: 5px solid #28a745; }}
            .fail {{ background: #f8d7da; border-left: 5px solid #dc3545; }}
            .timestamp {{ color: #6c757d; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛡️ RPSLS Security Test Summary</h1>
            <p class="timestamp">Generated: {timestamp}</p>
        </div>
        
        <h2>Test Results</h2>
    '''
    
    for test_name, passed in results.items():
        status_class = 'pass' if passed else 'fail'
        status_icon = '✅' if passed else '❌'
        status_text = 'PASSED' if passed else 'FAILED'
        
        html_content += f'''
        <div class="test-result {status_class}">
            <h3>{status_icon} {test_name.upper()} Security Scan - {status_text}</h3>
            <p>Detailed reports available in: reports/security/{test_name}_baseline.*</p>
        </div>
        '''
    
    html_content += '''
        <h2>Security Recommendations</h2>
        <ul>
            <li>Review all HIGH and MEDIUM risk findings</li>
            <li>Implement security headers (CSP, HSTS, etc.)</li>
            <li>Ensure proper input validation</li>
            <li>Regular security scanning in CI/CD pipeline</li>
            <li>Consider implementing authentication for sensitive endpoints</li>
        </ul>
        
        <h2>Next Steps</h2>
        <ol>
            <li>Review detailed ZAP reports</li>
            <li>Address critical security findings</li>
            <li>Implement security fixes</li>
            <li>Re-run security tests</li>
        </ol>
    </body>
    </html>
    '''
    
    with open(f'{REPORT_DIR}/security_summary.html', 'w') as f:
        f.write(html_content)
    
    print(f"\n📋 Security summary report: {REPORT_DIR}/security_summary.html")

if __name__ == "__main__":
    success = run_security_tests()
    sys.exit(0 if success else 1)
