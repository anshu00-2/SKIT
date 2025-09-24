#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Telemedicine App
Tests all backend APIs including authentication, doctor management, and appointments
"""

import requests
import json
import uuid
from datetime import datetime, timezone, timedelta
import time

# Backend URL from environment
BACKEND_URL = "https://rural-medconnect.preview.emergentagent.com/api"

class TelemedicineBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.test_user_data = None
        self.doctor_profile_id = None
        self.appointment_id = None
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_sample_data_initialization(self):
        """Test sample doctor initialization"""
        print("\n=== Testing Sample Data Initialization ===")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/init-sample-doctors")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("Sample Data Init", True, "Sample doctors initialized successfully")
                else:
                    self.log_test("Sample Data Init", False, "API returned success=false", {"response": data})
            else:
                self.log_test("Sample Data Init", False, f"HTTP {response.status_code}", {"response": response.text})
                
        except Exception as e:
            self.log_test("Sample Data Init", False, f"Request failed: {str(e)}")
    
    def test_doctor_listing(self):
        """Test getting available doctors"""
        print("\n=== Testing Doctor Listing ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/doctors")
            
            if response.status_code == 200:
                data = response.json()
                doctors = data.get("doctors", [])
                
                if len(doctors) > 0:
                    self.log_test("Doctor Listing", True, f"Retrieved {len(doctors)} doctors", {"doctors_count": len(doctors)})
                    
                    # Verify doctor data structure
                    first_doctor = doctors[0]
                    required_fields = ["id", "user_id", "specialization", "experience_years", "consultation_fee"]
                    missing_fields = [field for field in required_fields if field not in first_doctor]
                    
                    if not missing_fields:
                        self.log_test("Doctor Data Structure", True, "Doctor data has all required fields")
                    else:
                        self.log_test("Doctor Data Structure", False, f"Missing fields: {missing_fields}")
                        
                else:
                    self.log_test("Doctor Listing", False, "No doctors found in response")
                    
            else:
                self.log_test("Doctor Listing", False, f"HTTP {response.status_code}", {"response": response.text})
                
        except Exception as e:
            self.log_test("Doctor Listing", False, f"Request failed: {str(e)}")
    
    def test_auth_endpoints_without_session(self):
        """Test authentication endpoints without valid session"""
        print("\n=== Testing Auth Endpoints (No Session) ===")
        
        # Test /auth/me without authentication
        try:
            response = self.session.get(f"{BACKEND_URL}/auth/me")
            
            if response.status_code == 401:
                self.log_test("Auth Me (No Session)", True, "Correctly returned 401 for unauthenticated request")
            else:
                self.log_test("Auth Me (No Session)", False, f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Auth Me (No Session)", False, f"Request failed: {str(e)}")
        
        # Test logout without session
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/logout")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("Logout (No Session)", True, "Logout endpoint works without session")
                else:
                    self.log_test("Logout (No Session)", False, "Logout returned success=false")
            else:
                self.log_test("Logout (No Session)", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Logout (No Session)", False, f"Request failed: {str(e)}")
    
    def test_auth_session_processing(self):
        """Test session processing with mock data (since we can't get real Emergent Auth session)"""
        print("\n=== Testing Auth Session Processing ===")
        
        # Test with missing session_id
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/session", json={})
            
            if response.status_code == 400:
                self.log_test("Auth Session (No ID)", True, "Correctly rejected request without session_id")
            else:
                self.log_test("Auth Session (No ID)", False, f"Expected 400, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Auth Session (No ID)", False, f"Request failed: {str(e)}")
        
        # Test with invalid session_id (will fail external API call)
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/session", json={"session_id": "invalid_session_123"})
            
            # This should fail because it tries to call Emergent Auth API
            if response.status_code in [401, 500]:
                self.log_test("Auth Session (Invalid ID)", True, "Correctly handled invalid session_id")
            else:
                self.log_test("Auth Session (Invalid ID)", False, f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Auth Session (Invalid ID)", False, f"Request failed: {str(e)}")
    
    def test_protected_endpoints_without_auth(self):
        """Test protected endpoints without authentication"""
        print("\n=== Testing Protected Endpoints (No Auth) ===")
        
        protected_endpoints = [
            ("POST", "/doctors/profile", {"specialization": "Test", "experience_years": 5, "license_number": "TEST123", "bio": "Test", "consultation_fee": 100}),
            ("GET", "/doctors/profile", None),
            ("PUT", "/doctors/availability", {"available": True}),
            ("POST", "/appointments", {"doctor_id": "test_id", "type": "instant"}),
            ("GET", "/appointments", None),
        ]
        
        for method, endpoint, data in protected_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{BACKEND_URL}{endpoint}")
                elif method == "POST":
                    response = self.session.post(f"{BACKEND_URL}{endpoint}", json=data)
                elif method == "PUT":
                    response = self.session.put(f"{BACKEND_URL}{endpoint}", json=data)
                
                if response.status_code == 401:
                    self.log_test(f"Protected {method} {endpoint}", True, "Correctly requires authentication")
                else:
                    self.log_test(f"Protected {method} {endpoint}", False, f"Expected 401, got {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Protected {method} {endpoint}", False, f"Request failed: {str(e)}")
    
    def test_appointment_endpoints_with_invalid_data(self):
        """Test appointment endpoints with invalid data"""
        print("\n=== Testing Appointment Endpoints (Invalid Data) ===")
        
        # Test appointment creation with non-existent doctor
        try:
            response = self.session.post(f"{BACKEND_URL}/appointments", 
                                       json={"doctor_id": "non_existent_doctor", "type": "instant"})
            
            if response.status_code == 401:
                self.log_test("Appointment (No Auth)", True, "Correctly requires authentication")
            else:
                self.log_test("Appointment (No Auth)", False, f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Appointment (No Auth)", False, f"Request failed: {str(e)}")
        
        # Test appointment join with invalid ID
        try:
            response = self.session.get(f"{BACKEND_URL}/appointments/invalid_id/join")
            
            if response.status_code == 401:
                self.log_test("Appointment Join (No Auth)", True, "Correctly requires authentication")
            else:
                self.log_test("Appointment Join (No Auth)", False, f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Appointment Join (No Auth)", False, f"Request failed: {str(e)}")
        
        # Test appointment start with invalid ID
        try:
            response = self.session.post(f"{BACKEND_URL}/appointments/invalid_id/start")
            
            if response.status_code == 401:
                self.log_test("Appointment Start (No Auth)", True, "Correctly requires authentication")
            else:
                self.log_test("Appointment Start (No Auth)", False, f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Appointment Start (No Auth)", False, f"Request failed: {str(e)}")
    
    def test_api_structure_and_responses(self):
        """Test API structure and response formats"""
        print("\n=== Testing API Structure ===")
        
        # Test CORS headers
        try:
            response = self.session.options(f"{BACKEND_URL}/doctors")
            
            if response.status_code in [200, 204]:
                cors_headers = response.headers.get('Access-Control-Allow-Origin')
                if cors_headers:
                    self.log_test("CORS Headers", True, "CORS headers present")
                else:
                    self.log_test("CORS Headers", False, "CORS headers missing")
            else:
                self.log_test("CORS Headers", False, f"OPTIONS request failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("CORS Headers", False, f"Request failed: {str(e)}")
        
        # Test API prefix routing
        try:
            # Test without /api prefix (should fail)
            response = self.session.get(f"https://rural-medconnect.preview.emergentagent.com/doctors")
            
            if response.status_code == 404:
                self.log_test("API Prefix Routing", True, "Correctly requires /api prefix")
            else:
                self.log_test("API Prefix Routing", False, f"Unexpected response without /api prefix: {response.status_code}")
                
        except Exception as e:
            self.log_test("API Prefix Routing", False, f"Request failed: {str(e)}")
    
    def test_data_validation(self):
        """Test data validation on endpoints"""
        print("\n=== Testing Data Validation ===")
        
        # Test doctor profile creation with invalid data (without auth - should fail on auth first)
        try:
            invalid_data = {
                "specialization": "",  # Empty string
                "experience_years": -1,  # Negative number
                "license_number": "",  # Empty string
                "bio": "",  # Empty string
                "consultation_fee": -50  # Negative fee
            }
            
            response = self.session.post(f"{BACKEND_URL}/doctors/profile", json=invalid_data)
            
            if response.status_code == 401:
                self.log_test("Data Validation (Auth First)", True, "Authentication checked before validation")
            else:
                self.log_test("Data Validation (Auth First)", False, f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Data Validation (Auth First)", False, f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🏥 Starting Telemedicine Backend API Tests")
        print(f"Testing against: {BACKEND_URL}")
        print("=" * 60)
        
        # Test in logical order
        self.test_sample_data_initialization()
        self.test_doctor_listing()
        self.test_auth_endpoints_without_session()
        self.test_auth_session_processing()
        self.test_protected_endpoints_without_auth()
        self.test_appointment_endpoints_with_invalid_data()
        self.test_api_structure_and_responses()
        self.test_data_validation()
        
        # Summary
        print("\n" + "=" * 60)
        print("🏥 BACKEND TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = TelemedicineBackendTester()
    results = tester.run_all_tests()
    
    # Exit with error code if tests failed
    if results["failed"] > 0:
        exit(1)
    else:
        print("🎉 All tests passed!")
        exit(0)