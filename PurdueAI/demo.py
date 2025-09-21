#!/usr/bin/env python3
"""
Demo script for PurdueAI API
Shows how to interact with the chatbot programmatically
"""

import requests
import json
import time

def test_purdueai_api():
    """Test the PurdueAI API with various questions"""
    
    base_url = "http://localhost:5001"
    
    # Test questions
    test_questions = [
        "where is tarkington hall",
        "how far is it from hawkins hall to memorial union",
        "directions from purdue to indianapolis airport",
        "what's the weather like today",  # Should be filtered out
        "tell me about purdue university",
        "hello"  # Should be filtered out
    ]
    
    print("🚂 PurdueAI API Demo")
    print("=" * 50)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Question: {question}")
        print("-" * 30)
        
        try:
            response = requests.post(
                f"{base_url}/api/chat",
                json={"message": question},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"Answer: {data['response']}")
            else:
                print(f"Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        
        time.sleep(1)  # Be nice to the API
    
    print("\n" + "=" * 50)
    print("Demo completed! 🎉")

if __name__ == "__main__":
    test_purdueai_api()
