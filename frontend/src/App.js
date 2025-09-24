import React, { useEffect, useState, useRef } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        withCredentials: true
      });
      setUser(response.data.user);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = (redirectUrl) => {
    const authUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
    window.location.href = authUrl;
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
      setUser(null);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const processSession = async (sessionId) => {
    try {
      const response = await axios.post(`${API}/auth/session`, 
        { session_id: sessionId },
        { withCredentials: true }
      );
      setUser(response.data.user);
      return true;
    } catch (error) {
      console.error('Session processing error:', error);
      return false;
    }
  };

  useEffect(() => {
    // Check for session_id in URL fragment
    const fragment = window.location.hash.substring(1);
    const params = new URLSearchParams(fragment);
    const sessionId = params.get('session_id');

    if (sessionId) {
      setLoading(true);
      processSession(sessionId).then((success) => {
        if (success) {
          // Clean URL fragment
          window.history.replaceState({}, document.title, window.location.pathname);
        }
        setLoading(false);
      });
    } else {
      checkAuth();
    }
  }, []);

  const value = {
    user,
    loading,
    login,
    logout,
    checkAuth
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Components
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  return user ? children : <Navigate to="/login" />;
};

const LandingPage = () => {
  const { user } = useAuth();
  
  if (user) {
    return <Navigate to="/dashboard" />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <div className="flex-shrink-0 flex items-center">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">M</span>
                </div>
                <span className="ml-2 text-xl font-bold text-gray-900">MedConnect</span>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <LoginButton />
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Healthcare for
            <span className="text-blue-600"> Rural Communities</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Connect with qualified doctors through secure video consultations. 
            Quality healthcare, accessible anywhere, anytime.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <LoginButton className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition duration-200" />
            <button className="border border-gray-300 hover:border-gray-400 text-gray-700 px-8 py-3 rounded-lg font-semibold transition duration-200">
              Learn More
            </button>
          </div>
        </div>

        {/* Features */}
        <div className="mt-20 grid md:grid-cols-3 gap-8">
          <div className="text-center p-6 bg-white rounded-xl shadow-sm">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Video Consultations</h3>
            <p className="text-gray-600">HD video calls with doctors from the comfort of your home</p>
          </div>

          <div className="text-center p-6 bg-white rounded-xl shadow-sm">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Qualified Doctors</h3>
            <p className="text-gray-600">Access to licensed physicians across various specializations</p>
          </div>

          <div className="text-center p-6 bg-white rounded-xl shadow-sm">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">24/7 Availability</h3>
            <p className="text-gray-600">Schedule appointments or connect instantly with available doctors</p>
          </div>
        </div>
      </div>
    </div>
  );
};

const LoginButton = ({ className = "" }) => {
  const { login } = useAuth();
  
  const handleLogin = () => {
    const redirectUrl = `${window.location.origin}/dashboard`;
    login(redirectUrl);
  };

  return (
    <button 
      onClick={handleLogin}
      className={className || "bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition duration-200"}
    >
      Sign In with Google
    </button>
  );
};

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('appointments');
  const [doctors, setDoctors] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [showDoctorForm, setShowDoctorForm] = useState(false);

  useEffect(() => {
    fetchDoctors();
    fetchAppointments();
    initializeSampleDoctors();
  }, []);

  const fetchDoctors = async () => {
    try {
      const response = await axios.get(`${API}/doctors`);
      setDoctors(response.data.doctors);
    } catch (error) {
      console.error('Error fetching doctors:', error);
    }
  };

  const fetchAppointments = async () => {
    try {
      const response = await axios.get(`${API}/appointments`, {
        withCredentials: true
      });
      setAppointments(response.data.appointments);
    } catch (error) {
      console.error('Error fetching appointments:', error);
    }
  };

  const initializeSampleDoctors = async () => {
    try {
      await axios.post(`${API}/admin/init-sample-doctors`);
    } catch (error) {
      console.error('Error initializing sample doctors:', error);
    }
  };

  const bookAppointment = async (doctorId, type = 'instant') => {
    try {
      await axios.post(`${API}/appointments`, {
        doctor_id: doctorId,
        type: type,
        scheduled_time: type === 'instant' ? null : new Date()
      }, {
        withCredentials: true
      });
      fetchAppointments();
      alert('Appointment booked successfully!');
    } catch (error) {
      console.error('Error booking appointment:', error);
      alert('Error booking appointment');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">M</span>
              </div>
              <span className="ml-2 text-xl font-bold text-gray-900">MedConnect</span>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <img src={user.picture} alt={user.name} className="w-8 h-8 rounded-full" />
                <span className="text-sm font-medium text-gray-700">{user.name}</span>
                <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                  {user.role}
                </span>
              </div>
              <button 
                onClick={logout}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation Tabs */}
        <div className="flex space-x-8 border-b border-gray-200 mb-8">
          <button
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'appointments' 
                ? 'border-blue-500 text-blue-600' 
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('appointments')}
          >
            My Appointments
          </button>
          <button
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'doctors' 
                ? 'border-blue-500 text-blue-600' 
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('doctors')}
          >
            Find Doctors
          </button>
          {user.role === 'patient' && (
            <button
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'become-doctor' 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => setActiveTab('become-doctor')}
            >
              Become a Doctor
            </button>
          )}
        </div>

        {/* Tab Content */}
        {activeTab === 'appointments' && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">My Appointments</h2>
            {appointments.length === 0 ? (
              <div className="text-center py-12">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 8h6m-6 0a2 2 0 01-2-2V9a2 2 0 012-2h4a2 2 0 012 2v6a2 2 0 01-2 2" />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No appointments</h3>
                <p className="mt-1 text-sm text-gray-500">Get started by booking your first consultation.</p>
              </div>
            ) : (
              <div className="grid gap-6">
                {appointments.map((appointment) => (
                  <AppointmentCard key={appointment.id} appointment={appointment} />
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'doctors' && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Available Doctors</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {doctors.map((doctor) => (
                <DoctorCard key={doctor.id} doctor={doctor} onBook={bookAppointment} />
              ))}
            </div>
          </div>
        )}

        {activeTab === 'become-doctor' && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Join as a Doctor</h2>
            <DoctorRegistrationForm onSuccess={() => {
              setActiveTab('appointments');
              window.location.reload();
            }} />
          </div>
        )}
      </div>
    </div>
  );
};

const DoctorCard = ({ doctor, onBook }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center mb-4">
        <img 
          src={doctor.user?.picture || 'https://via.placeholder.com/60'} 
          alt={doctor.user?.name}
          className="w-12 h-12 rounded-full"
        />
        <div className="ml-3">
          <h3 className="font-semibold text-gray-900">{doctor.user?.name}</h3>
          <p className="text-sm text-gray-600">{doctor.specialization}</p>
        </div>
      </div>
      
      <div className="mb-4">
        <p className="text-sm text-gray-700 mb-2">{doctor.bio}</p>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Experience: {doctor.experience_years} years</span>
          <span className="font-medium text-green-600">${doctor.consultation_fee}</span>
        </div>
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => onBook(doctor.id, 'instant')}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg text-sm font-medium transition duration-200"
        >
          Book Instantly
        </button>
        <button
          onClick={() => onBook(doctor.id, 'scheduled')}
          className="flex-1 border border-gray-300 hover:border-gray-400 text-gray-700 py-2 px-4 rounded-lg text-sm font-medium transition duration-200"
        >
          Schedule
        </button>
      </div>
    </div>
  );
};

const AppointmentCard = ({ appointment }) => {
  const [videoRoom, setVideoRoom] = useState(null);

  const startVideoCall = async () => {
    try {
      const response = await axios.post(`${API}/appointments/${appointment.id}/start`, {}, {
        withCredentials: true
      });
      setVideoRoom(response.data.video_room_id);
    } catch (error) {
      console.error('Error starting video call:', error);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Instant consultation';
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center">
          <img 
            src={appointment.doctor?.picture || appointment.patient?.picture || 'https://via.placeholder.com/50'} 
            alt=""
            className="w-10 h-10 rounded-full"
          />
          <div className="ml-3">
            <h3 className="font-semibold text-gray-900">
              {appointment.doctor?.name || appointment.patient?.name}
            </h3>
            <p className="text-sm text-gray-600">
              {appointment.doctor?.specialization || 'Patient'}
            </p>
          </div>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          appointment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
          appointment.status === 'active' ? 'bg-green-100 text-green-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {appointment.status}
        </span>
      </div>

      <div className="flex justify-between items-center">
        <div>
          <p className="text-sm text-gray-600">
            {formatDate(appointment.scheduled_time)}
          </p>
          <p className="text-sm text-gray-600">Type: {appointment.type}</p>
        </div>

        {appointment.status === 'pending' && (
          <button
            onClick={startVideoCall}
            className="bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-lg text-sm font-medium transition duration-200 flex items-center"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            Start Video Call
          </button>
        )}
      </div>

      {videoRoom && (
        <div className="mt-4">
          <VideoCall roomId={videoRoom} />
        </div>
      )}
    </div>
  );
};

const DoctorRegistrationForm = ({ onSuccess }) => {
  const [formData, setFormData] = useState({
    specialization: '',
    experience_years: '',
    license_number: '',
    bio: '',
    consultation_fee: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/doctors/profile`, {
        ...formData,
        experience_years: parseInt(formData.experience_years),
        consultation_fee: parseFloat(formData.consultation_fee)
      }, {
        withCredentials: true
      });
      onSuccess();
    } catch (error) {
      console.error('Error creating doctor profile:', error);
      alert('Error creating doctor profile');
    }
  };

  return (
    <div className="max-w-2xl">
      <form onSubmit={handleSubmit} className="space-y-6 bg-white p-8 rounded-lg shadow-sm">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Specialization
          </label>
          <input
            type="text"
            required
            value={formData.specialization}
            onChange={(e) => setFormData({...formData, specialization: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., General Medicine, Cardiology"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Years of Experience
          </label>
          <input
            type="number"
            required
            min="0"
            value={formData.experience_years}
            onChange={(e) => setFormData({...formData, experience_years: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Medical License Number
          </label>
          <input
            type="text"
            required
            value={formData.license_number}
            onChange={(e) => setFormData({...formData, license_number: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Bio
          </label>
          <textarea
            required
            value={formData.bio}
            onChange={(e) => setFormData({...formData, bio: e.target.value})}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Tell patients about your experience and approach to healthcare..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Consultation Fee ($)
          </label>
          <input
            type="number"
            required
            min="0"
            step="0.01"
            value={formData.consultation_fee}
            onChange={(e) => setFormData({...formData, consultation_fee: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <button
          type="submit"
          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg font-medium transition duration-200"
        >
          Register as Doctor
        </button>
      </form>
    </div>
  );
};

// Simple WebRTC Video Call Component
const VideoCall = ({ roomId }) => {
  const localVideoRef = useRef();
  const remoteVideoRef = useRef();
  const [isConnected, setIsConnected] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(false);

  useEffect(() => {
    initializeWebRTC();
    return () => {
      // Cleanup
    };
  }, [roomId]);

  const initializeWebRTC = async () => {
    try {
      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      });
      
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }

      setIsConnected(true);
    } catch (error) {
      console.error('Error accessing media devices:', error);
    }
  };

  const toggleMute = () => {
    if (localVideoRef.current && localVideoRef.current.srcObject) {
      const audioTracks = localVideoRef.current.srcObject.getAudioTracks();
      audioTracks.forEach(track => {
        track.enabled = !track.enabled;
      });
      setIsMuted(!isMuted);
    }
  };

  const toggleVideo = () => {
    if (localVideoRef.current && localVideoRef.current.srcObject) {
      const videoTracks = localVideoRef.current.srcObject.getVideoTracks();
      videoTracks.forEach(track => {
        track.enabled = !track.enabled;
      });
      setIsVideoOff(!isVideoOff);
    }
  };

  return (
    <div className="bg-black rounded-lg overflow-hidden">
      <div className="relative h-96">
        {/* Remote Video (main view) */}
        <video
          ref={remoteVideoRef}
          autoPlay
          playsInline
          className="w-full h-full object-cover"
        />
        
        {/* Local Video (picture-in-picture) */}
        <div className="absolute top-4 right-4 w-32 h-24 bg-gray-800 rounded-lg overflow-hidden">
          <video
            ref={localVideoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />
        </div>

        {/* Controls */}
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-4">
          <button
            onClick={toggleMute}
            className={`p-3 rounded-full ${isMuted ? 'bg-red-600' : 'bg-gray-600'} text-white hover:opacity-80 transition-opacity`}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isMuted ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              )}
            </svg>
          </button>

          <button
            onClick={toggleVideo}
            className={`p-3 rounded-full ${isVideoOff ? 'bg-red-600' : 'bg-gray-600'} text-white hover:opacity-80 transition-opacity`}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </button>

          <button className="p-3 rounded-full bg-red-600 text-white hover:opacity-80 transition-opacity">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M3 3l18 18" />
            </svg>
          </button>
        </div>
      </div>

      <div className="p-4 bg-gray-900 text-white">
        <div className="flex justify-between items-center">
          <div>
            <p className="font-medium">Video Consultation</p>
            <p className="text-sm text-gray-400">Room ID: {roomId}</p>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm">{isConnected ? 'Connected' : 'Connecting...'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LandingPage />} />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/" element={<LandingPage />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;