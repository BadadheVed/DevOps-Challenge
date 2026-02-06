#!/usr/bin/env python3
"""
Test script to test the @instrument decorator with FastAPI
Run this after starting the FastAPI server with: python main.py
"""

import requests
import json
from tabulate import tabulate
import time


BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_single_endpoint():
    """Test single instrumented function endpoint"""
    print_section("Testing: GET /api/user/{user_id}")
    
    user_id = 1
    try:
        response = requests.get(f"{BASE_URL}/api/user/{user_id}")
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")


def test_posts_endpoint():
    """Test another single instrumented function endpoint"""
    print_section("Testing: GET /api/user/{user_id}/posts")
    
    user_id = 1
    try:
        response = requests.get(f"{BASE_URL}/api/user/{user_id}/posts")
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")


def test_complex_endpoint():
    """Test orchestrated endpoint calling multiple instrumented functions"""
    print_section("Testing: POST /api/user-profile/{user_id} (Main Test)")
    
    user_id = 42
    try:
        response = requests.post(f"{BASE_URL}/api/user-profile/{user_id}")
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")


def test_metrics():
    """Fetch and display Prometheus metrics"""
    print_section("Prometheus Metrics")
    
    try:
        response = requests.get(f"{BASE_URL}/metrics")
        print("Raw Metrics (first 1500 chars):")
        metrics_text = response.text
        print(metrics_text[:1500])
        print("\n... (truncated)")
        
        print("\n\nKey Metrics Summary:")
        lines = metrics_text.split('\n')
        relevant_metrics = [line for line in lines if 'function' in line.lower() and not line.startswith('#')]
        for metric in relevant_metrics[:20]:
            if metric.strip():
                print(f"  {metric}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_health():
    """Test health endpoint"""
    print_section("Testing: GET /health")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")


def test_load_multiple_calls():
    """Test multiple sequential calls to see instrumentation accumulate"""
    print_section("Load Test: Multiple Sequential Calls")
    
    print("Making 3 sequential calls to test instrumentation...")
    
    start_time = time.time()
    
    for i in range(3):
        try:
            print(f"\n  Call {i+1}/3...")
            response = requests.post(f"{BASE_URL}/api/user-profile/{i+100}")
            print(f"    ✓ Status: {response.status_code}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        if i < 2:
            time.sleep(0.5)
    
    elapsed = time.time() - start_time
    print(f"\n  Total time: {elapsed:.2f}s")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("  PROMETHEUS INSTRUMENTATION TEST SUITE")
    print("="*60)
    print("\nMake sure FastAPI server is running: python main.py")
    print(f"Testing against: {BASE_URL}\n")
    
    try:
        # Test health first
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("❌ Server is not responding correctly!")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Make sure to run: python main.py")
        print(f"   Error: {e}\n")
        return
    
    print("✓ Server is running!\n")
    
    # Run all tests
    test_health()
    test_single_endpoint()
    test_posts_endpoint()
    test_complex_endpoint()
    test_load_multiple_calls()
    test_metrics()
    
    print("\n" + "="*60)
    print("  TEST SUITE COMPLETED")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
