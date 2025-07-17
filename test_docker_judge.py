#!/usr/bin/env python3
"""
Simple test script to verify Docker-in-Docker functionality works correctly.
This script directly tests the judge functions without Django setup.
"""

import sys
import os
import tempfile

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the judge functions directly
from judge_core.judge import judge_python, judge_cpp, judge_java

def test_python_hello():
    """Test Python Hello World"""
    print("Testing Python Hello World...")
    
    code = """
print("Hello, World!")
"""
    
    stdout, stderr, verdict, exec_time, memory = judge_python(code, "", 5, 256)
    
    print(f"  Verdict: {verdict}")
    print(f"  Output: '{stdout.strip()}'")
    print(f"  Error: '{stderr.strip()}'")
    
    success = verdict == "success" and stdout.strip() == "Hello, World!"
    print(f"  Result: {'✅ PASS' if success else '❌ FAIL'}")
    return success

def test_cpp_hello():
    """Test C++ Hello World"""
    print("\nTesting C++ Hello World...")
    
    code = """
#include <iostream>
using namespace std;

int main() {
    cout << "Hello, World!" << endl;
    return 0;
}
"""
    
    stdout, stderr, verdict, exec_time, memory = judge_cpp(code, "", 5, 256)
    
    print(f"  Verdict: {verdict}")
    print(f"  Output: '{stdout.strip()}'")
    print(f"  Error: '{stderr.strip()}'")
    
    success = verdict == "success" and stdout.strip() == "Hello, World!"
    print(f"  Result: {'✅ PASS' if success else '❌ FAIL'}")
    return success

def test_java_hello():
    """Test Java Hello World"""
    print("\nTesting Java Hello World...")
    
    code = """
public class Solution {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
"""
    
    stdout, stderr, verdict, exec_time, memory = judge_java(code, "", 5, 256)
    
    print(f"  Verdict: {verdict}")
    print(f"  Output: '{stdout.strip()}'")
    print(f"  Error: '{stderr.strip()}'")
    
    success = verdict == "success" and stdout.strip() == "Hello, World!"
    print(f"  Result: {'✅ PASS' if success else '❌ FAIL'}")
    return success

def test_docker_availability():
    """Test if Docker is available"""
    print("Testing Docker availability...")
    
    import subprocess
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"  Docker version: {result.stdout.strip()}")
            print("  Result: ✅ Docker is available")
            return True
        else:
            print(f"  Docker command failed: {result.stderr}")
            print("  Result: ❌ Docker not available")
            return False
    except Exception as e:
        print(f"  Exception: {e}")
        print("  Result: ❌ Docker not available")
        return False

if __name__ == "__main__":
    print("="*60)
    print("DOCKER-IN-DOCKER JUDGE SYSTEM TEST")
    print("="*60)
    
    # Test Docker availability first
    docker_ok = test_docker_availability()
    
    if not docker_ok:
        print("\n❌ Docker is not available. Cannot run tests.")
        sys.exit(1)
    
    # Test all languages
    results = []
    results.append(test_python_hello())
    results.append(test_cpp_hello())
    results.append(test_java_hello())
    
    print("\n" + "="*60)
    print("FINAL RESULTS:")
    print("="*60)
    
    if all(results):
        print("🎉 ALL TESTS PASSED! Docker-in-Docker execution is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check the output above.")
        sys.exit(1)
