#!/usr/bin/env python3
"""
Advanced Backend Testing for Telemedicine App
Tests authenticated flows and data persistence
"""

import requests
import json
import uuid
from datetime import datetime, timezone, timedelta
import time

# Backend URL from environment
BACKEND_URL = "https://rural-medconnect.preview.emergentagent.com/api"

class AdvancedTelemedicineBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.sample_doctors = []
        
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
    
    def test_doctor_data_persistence(self):
        """Test that sample doctors are properly stored and retrievable"""
        print("\n=== Testing Doctor Data Persistence ===")
        
        try:
            # Initialize sample doctors
            init_response = self.session.post(f"{BACKEND_URL}/admin/init-sample-doctors")
            
            if init_response.status_code == 200:
                self.log_test("Sample Data Initialization", True, "Sample doctors initialized")
                
                # Get doctors list
                doctors_response = self.session.get(f"{BACKEND_URL}/doctors")
                
                if doctors_response.status_code == 200:
                    data = doctors_response.json()
                    doctors = data.get("doctors", [])
                    
                    if len(doctors) >= 3:
                        self.sample_doctors = doctors
                        self.log_test("Doctor Data Retrieval", True, f"Retrieved {len(doctors)} doctors")
                        
                        # Verify doctor specializations
                        specializations = [d.get("specialization") for d in doctors]
                        expected_specs = ["General Medicine", "Cardiology", "Pediatrics"]
                        
                        found_specs = [spec for spec in expected_specs if spec in specializations]
                        if len(found_specs) == 3:
                            self.log_test("Doctor Specializations", True, "All expected specializations found")
                        else:
                            self.log_test("Doctor Specializations", False, f"Missing specializations: {set(expected_specs) - set(found_specs)}")
                        
                        # Verify doctor has user data
                        doctors_with_user_data = [d for d in doctors if "user" in d and d["user"].get("name")]
                        if len(doctors_with_user_data) == len(doctors):
                            self.log_test("Doctor User Data", True, "All doctors have user information")
                        else:
                            self.log_test("Doctor User Data", False, f"Only {len(doctors_with_user_data)}/{len(doctors)} doctors have user data")
                            
                    else:
                        self.log_test("Doctor Data Retrieval", False, f"Expected at least 3 doctors, got {len(doctors)}")
                else:
                    self.log_test("Doctor Data Retrieval", False, f"HTTP {doctors_response.status_code}")
            else:
                self.log_test("Sample Data Initialization", False, f"HTTP {init_response.status_code}")
                
        except Exception as e:
            self.log_test("Doctor Data Persistence", False, f"Request failed: {str(e)}")
    
    def test_appointment_creation_flow(self):
        """Test appointment creation with valid doctor IDs"""
        print("\n=== Testing Appointment Creation Flow ===")
        
        if not self.sample_doctors:
            self.log_test("Appointment Creation", False, "No sample doctors available for testing")
            return
        
        try:
            # Try to create appointment without authentication (should fail)
            doctor_id = self.sample_doctors[0]["id"]
            appointment_data = {
                "doctor_id": doctor_id,
                "type": "instant"
            }
            
            response = self.session.post(f"{BACKEND_URL}/appointments", json=appointment_data)
            
            if response.status_code == 401:
                self.log_test("Appointment Creation (No Auth)", True, "Correctly requires authentication")
            else:
                self.log_test("Appointment Creation (No Auth)", False, f"Expected 401, got {response.status_code}")
            
            # Test with scheduled appointment
            scheduled_data = {
                "doctor_id": doctor_id,
                "type": "scheduled",
                "scheduled_time": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
            }
            
            response = self.session.post(f"{BACKEND_URL}/appointments", json=scheduled_data)
            
            if response.status_code == 401:
                self.log_test("Scheduled Appointment (No Auth)", True, "Correctly requires authentication")
            else:
                self.log_test("Scheduled Appointment (No Auth)", False, f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Appointment Creation Flow", False, f"Request failed: {str(e)}")
    
    def test_doctor_profile_management(self):
        """Test doctor profile creation and management"""
        print("\n=== Testing Doctor Profile Management ===")
        
        try:
            # Test doctor profile creation without auth
            profile_data = {
                "specialization": "Dermatology",
                "experience_years": 10,
                "license_number": "MD99999",
                "bio": "Experienced dermatologist specializing in telemedicine consultations.",
                "consultation_fee": 150.0
            }
            
            response = self.session.post(f"{BACKEND_URL}/doctors/profile", json=profile_data)
            
            if response.status_code == 401:
                self.log_test("Doctor Profile Creation (No Auth)", True, "Correctly requires authentication")
            else:
                self.log_test("Doctor Profile Creation (No Auth)", False, f"Expected 401, got {response.status_code}")
            
            # Test getting doctor profile without auth
            response = self.session.get(f"{BACKEND_URL}/doctors/profile")
            
            if response.status_code == 401:
                self.log_test("Doctor Profile Get (No Auth)", True, "Correctly requires authentication")
            else:
                self.log_test("Doctor Profile Get (No Auth)", False, f"Expected 401, got {response.status_code}")
            
            # Test availability update without auth
            response = self.session.put(f"{BACKEND_URL}/doctors/availability", json={"available": False})
            
            if response.status_code == 401:
                self.log_test("Doctor Availability (No Auth)", True, "Correctly requires authentication")
            else:
                self.log_test("Doctor Availability (No Auth)", False, f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Doctor Profile Management", False, f"Request failed: {str(e)}")
    
    def test_appointment_access_control(self):
        """Test appointment access control endpoints"""
        print("\n=== Testing Appointment Access Control ===")
        
        try:
            # Test joining appointment without auth
            fake_appointment_id = str(uuid.uuid4())
            response = self.session.get(f"{BACKEND_URL}/appointments/{fake_appointment_id}/join")
            
            if response.status_code == 401:
                self.log_test("Appointment Join (No Auth)", True, "Correctly requires authentication")
            else:
                self.log_test("Appointment Join (No Auth)", False, f"Expected 401, got {response.status_code}")
            
            # Test starting appointment without auth
            response = self.session.post(f"{BACKEND_URL}/appointments/{fake_appointment_id}/start")
            
            if response.status_code == 401:
                self.log_test("Appointment Start (No Auth)", True, "Correctly requires authentication")
            else:
                self.log_test("Appointment Start (No Auth)", False, f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Appointment Access Control", False, f"Request failed: {str(e)}")
    
    def test_data_consistency(self):
        """Test data consistency across multiple requests"""
        print("\n=== Testing Data Consistency ===")
        
        try:
            # Get doctors list multiple times and verify consistency
            responses = []
            for i in range(3):
                response = self.session.get(f"{BACKEND_URL}/doctors")
                if response.status_code == 200:
                    responses.append(response.json())
                time.sleep(0.1)  # Small delay between requests
            
            if len(responses) == 3:
                # Check if all responses have same number of doctors
                doctor_counts = [len(r.get("doctors", [])) for r in responses]
                
                if len(set(doctor_counts)) == 1:
                    self.log_test("Data Consistency", True, f"Consistent doctor count across requests: {doctor_counts[0]}")
                    
                    # Check if doctor IDs are consistent
                    doctor_ids_sets = [set(d["id"] for d in r.get("doctors", [])) for r in responses]
                    
                    if all(ids == doctor_ids_sets[0] for ids in doctor_ids_sets):
                        self.log_test("Doctor ID Consistency", True, "Doctor IDs consistent across requests")
                    else:
                        self.log_test("Doctor ID Consistency", False, "Doctor IDs vary between requests")
                        
                else:
                    self.log_test("Data Consistency", False, f"Inconsistent doctor counts: {doctor_counts}")
            else:
                self.log_test("Data Consistency", False, f"Only {len(responses)}/3 requests succeeded")
                
        except Exception as e:
            self.log_test("Data Consistency", False, f"Request failed: {str(e)}")
    
    def test_api_response_formats(self):
        """Test API response formats and structure"""
        print("\n=== Testing API Response Formats ===")
        
        try:
            # Test doctors endpoint response format
            response = self.session.get(f"{BACKEND_URL}/doctors")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check top-level structure
                if "doctors" in data and isinstance(data["doctors"], list):
                    self.log_test("Doctors Response Format", True, "Correct response structure")
                    
                    if data["doctors"]:
                        doctor = data["doctors"][0]
                        required_fields = ["id", "user_id", "specialization", "experience_years", "consultation_fee", "available"]
                        
                        missing_fields = [field for field in required_fields if field not in doctor]
                        if not missing_fields:
                            self.log_test("Doctor Object Structure", True, "All required fields present")
                        else:
                            self.log_test("Doctor Object Structure", False, f"Missing fields: {missing_fields}")
                        
                        # Check user data structure
                        if "user" in doctor and isinstance(doctor["user"], dict):
                            user_fields = ["name", "picture"]
                            missing_user_fields = [field for field in user_fields if field not in doctor["user"]]
                            
                            if not missing_user_fields:
                                self.log_test("Doctor User Data Structure", True, "User data structure correct")
                            else:
                                self.log_test("Doctor User Data Structure", False, f"Missing user fields: {missing_user_fields}")
                        else:
                            self.log_test("Doctor User Data Structure", False, "User data missing or invalid")
                            
                else:
                    self.log_test("Doctors Response Format", False, "Invalid response structure")
            else:
                self.log_test("Doctors Response Format", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("API Response Formats", False, f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all advanced backend tests"""
        print("🏥 Starting Advanced Telemedicine Backend API Tests")
        print(f"Testing against: {BACKEND_URL}")
        print("=" * 70)
        
        # Test in logical order
        self.test_doctor_data_persistence()
        self.test_appointment_creation_flow()
        self.test_doctor_profile_management()
        self.test_appointment_access_control()
        self.test_data_consistency()
        self.test_api_response_formats()
        
        # Summary
        print("\n" + "=" * 70)
        print("🏥 ADVANCED BACKEND TEST SUMMARY")
        print("=" * 70)
        
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
        
        print("\n" + "=" * 70)
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = AdvancedTelemedicineBackendTester()
    results = tester.run_all_tests()
    
    # Exit with error code if tests failed
    if results["failed"] > 0:
        exit(1)
    else:
        print("🎉 All advanced tests passed!")
        exit(0)