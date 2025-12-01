import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';

function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError('');
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        try {
            const response = await axios.post('http://localhost:8000/api/token', formData);
            const { access_token, user } = response.data;
            localStorage.setItem('token', access_token);
            localStorage.setItem('user', JSON.stringify(user));

            switch (user.role) {
                case 'student': navigate('/student-dashboard'); break;
                case 'facilitator': navigate('/facilitator-dashboard'); break;
                case 'psychologist': navigate('/psychologist-dashboard'); break;
                default: setError('Unknown user role.');
            }
        } catch (err) {
            setError('Login failed. Please check credentials.');
        }
    };

    return (
        <div className="login-page-body">
            <div className="login-container">
                <div className="logo">HTP Platform</div>
                <div className="tagline">Drawing Analysis for Social Innovation</div>
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="email" className="form-label">Email Address</label>
                        <input type="email" id="email" className="form-input" required value={email} onChange={(e) => setEmail(e.target.value)} />
                    </div>
                    <div className="form-group">
                        <label htmlFor="password" className="form-label">Password</label>
                        <input type="password" id="password" className="form-input" required value={password} onChange={(e) => setPassword(e.target.value)} />
                    </div>
                    {error && <p style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
                    <button type="submit" className="login-btn">Login</button>
                </form>
                <p style={{ marginTop: '20px' }}>Don't have an account? <Link to="/register">Sign Up</Link></p>
                 <div className="demo-info">
                    {/* <p><b>Test Users (password is 'password'):</b></p> */}
                    {/* <p></p> */}
                </div>
            </div>
        </div>
    );
}
export default LoginPage;