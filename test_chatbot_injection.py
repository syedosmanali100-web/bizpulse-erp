"""Test script to verify chatbot is injected into the main page"""
import requests

# Test the main page
url = 'http://localhost:5000/'

try:
    response = requests.get(url)
    html = response.text
    
    print("=" * 60)
    print("CHATBOT INJECTION TEST")
    print("=" * 60)
    
    # Check for chatbot elements
    checks = {
        'Chatbot Button': 'chatbot-button' in html,
        'Chatbot Window': 'chatbot-window' in html,
        'Toggle Function': 'toggleChatbot()' in html,
        'BizPulse Assistant': 'BizPulse Assistant' in html,
        'Quick Replies': 'quick-replies' in html,
        'Send Message Function': 'sendChatMessage()' in html
    }
    
    print("\nChatbot Elements Found:")
    print("-" * 60)
    for check, found in checks.items():
        status = "✅ FOUND" if found else "❌ MISSING"
        print(f"{check:.<40} {status}")
    
    print("\n" + "=" * 60)
    
    if all(checks.values()):
        print("✅ SUCCESS! Chatbot is properly injected!")
    else:
        print("❌ FAILED! Some chatbot elements are missing!")
        
    print("=" * 60)
    
    # Count occurrences
    print(f"\nTotal 'chatbot' mentions: {html.lower().count('chatbot')}")
    print(f"Page size: {len(html)} characters")
    
except Exception as e:
    print(f"❌ Error: {e}")
