import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';

function RegisterPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState('student'); // Default role is 'student'
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError('');
        setMessage('');

        if (password.length < 6) {
            setError('Password must be at least 6 characters long.');
            return;
        }

        const userData = {
            email,
            password,
            role,
        };

        try {
            await axios.post('http://localhost:8000/api/register', userData);
            
            setMessage('Registration successful! Redirecting to login...');

            // Wait 2 seconds to show the success message, then redirect
            setTimeout(() => {
                navigate('/login');
            }, 2000);

        } catch (err) {
            if (err.response && err.response.data && err.response.data.detail) {
                setError(err.response.data.detail); // Show specific error from backend (e.g., "Email already registered")
            } else {
                setError('Registration failed. Please try again.');
            }
            console.error('Registration error:', err);
        }
    };

    return (
        <div className="login-page-body">
            <div className="login-container">
                <div className="logo">Create Your Account</div>
                <div className="tagline">Join the HTP Assessment Platform</div>
                
                <form id="registerForm" onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="email" className="form-label">Email Address</label>
                        <input 
                            type="email" 
                            id="email" 
                            className="form-input" 
                            placeholder="Enter your email" 
                            required 
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="password" className="form-label">Password</label>
                        <input 
                            type="password" 
                            id="password" 
                            className="form-input" 
                            placeholder="6+ characters" 
                            required 
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="role" className="form-label">I am a...</label>
                        <select 
                            id="role" 
                            className="form-input" 
                            value={role} 
                            onChange={(e) => setRole(e.target.value)}
                        >
                            <option value="student">Student</option>
                            <option value="facilitator">Facilitator</option>
                            <option value="psychologist">Psychologist</option>
                        </select>
                    </div>

                    {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
                    {message && <p style={{ color: 'green', marginTop: '10px' }}>{message}</p>}
                    
                    <button type="submit" className="login-btn">Sign Up</button>
                </form>
                
                <p style={{ marginTop: '20px' }}>
                    Already have an account? <Link to="/login">Log In</Link>
                </p>
            </div>
        </div>
    );
}

export default RegisterPage;