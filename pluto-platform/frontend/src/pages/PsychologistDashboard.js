import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { useNavigate } from 'react-router-dom';

const API_URL = 'http://localhost:8000';

function PsychologistDashboard() {
    const navigate = useNavigate();
    const [submissions, setSubmissions] = useState([]);
    const [selected, setSelected] = useState(null);
    const [notes, setNotes] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [user, setUser] = useState(null);

    const fetchSubmissions = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const response = await axios.get(`${API_URL}/api/assessments/psychologist`, { headers: { Authorization: `Bearer ${token}` } });
            setSubmissions(response.data);

            if (response.data.length > 0) {
                const firstSub = response.data.find(s => s.status === 'in_review') || response.data[0];
                setSelected(firstSub);
                setNotes(firstSub.evaluation?.notes || '');
            }
        } catch (err) {
            setError('Failed to fetch data. Please log in again.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const loggedInUser = localStorage.getItem('user');
        if (loggedInUser) {
            setUser(JSON.parse(loggedInUser));
        }
        fetchSubmissions();
    }, []);

    const handleSelectSubmission = (sub) => {
        setSelected(sub);
        setNotes(sub.evaluation?.notes || '');
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        navigate('/login');
    };
    
    const handleSaveEvaluation = async () => {
        if (!selected) return;
        try {
            const token = localStorage.getItem('token');
            await axios.post(`${API_URL}/api/drawings/${selected.id}/evaluate`, { notes }, {
                 headers: { Authorization: `Bearer ${token}` }
            });
            alert('Evaluation saved successfully!');
            fetchSubmissions();
        } catch (err) {
            alert('Failed to save evaluation.');
            console.error(err);
        }
    };

    if (loading) return <div style={{padding: '2rem'}}>Loading assigned cases...</div>;
    if (error) return <div style={{padding: '2rem', color: 'red'}}>{error}</div>;

    return (
        <div style={{ background: 'var(--background-color)', height: '100vh', display: 'flex', flexDirection: 'column' }}>
            <nav className="navbar">
                <div className="logo">Psychologist Portal</div>
                <div className="user-info">
                    <span>{user ? (user.email || '').split('@')[0] : 'Psychologist'}</span>
                    <div className="user-avatar">P</div>
                    <button onClick={handleLogout} className="btn btn-secondary">Logout</button>
                </div>
            </nav>
            <div className="psychologist-dashboard-container">
                <div className="panel submissions-panel">
                    <div className="panel-header"><h2>Submissions for Review</h2></div>
                    <div className="panel-content">
                        {submissions.length > 0 ? submissions.map((sub) => (
                            <div key={sub.id} className={`submission-item ${selected?.id === sub.id ? 'selected' : ''}`} onClick={() => handleSelectSubmission(sub)}>
                                <span>{(sub.student?.email || '').split('@')[0]}</span>
                                <span className={`status-badge status-${sub.status.replace('_', '-')}`}>{sub.status}</span>
                            </div>
                        )) : <p>No submissions assigned to you.</p>}
                    </div>
                </div>

                <div className="panel review-panel">
                    <div className="panel-header">
                        <h2>
                            Drawing Review - {(() => {
                                const s = selected?.student;
                                if (!s) return '';
                                const name = s.name || [s.first_name, s.last_name].filter(Boolean).join(' ');
                                if (name) return name;
                                return (s.email || '').split('@')[0] || '';
                            })()}
                        </h2>
                    </div>
                    <div className="panel-content">
                        {selected ? (
                            <>
                                <div className="drawing-viewer">
                                    <img src={`${API_URL}/${selected.file_path}`} alt="HTP Drawing" style={{ width: '100%', height: '100%', objectFit: 'contain' }}/>
                                </div>
                                <div className="ai-summary">
                                    <div className="ai-summary-header"><span>Initial Observations</span></div>
                                    <div className="ai-summary-content">
                                        <ReactMarkdown>{selected.ai_analysis?.analysis_data?.final || 'Analysis is pending or failed...'}</ReactMarkdown>
                                    </div>
                                </div>
                            </>
                        ) : <p style={{textAlign: 'center', color: '#6b7280'}}>Select a submission from the left to begin your review.</p>}
                    </div>
                </div>

                <div className="panel evaluation-panel">
                    <div className="panel-header"><h2>Evaluation</h2></div>
                    <div className="panel-content">
                        {selected ? (
                            <>
                                <label htmlFor="analysis-notes" style={{display: 'block', marginBottom: '8px', fontWeight: '500'}}>Your Professional Notes:</label>
                                <textarea id="analysis-notes" className="notes-textarea" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Enter your evaluation notes here..." style={{width: '100%', minHeight: '120px', marginBottom: '1rem'}}></textarea>
                                <button className="save-btn" onClick={handleSaveEvaluation} disabled={!selected || !notes || selected.status !== 'in_review'}>Save Evaluation</button>
                            </>
                        ) : <p>Write your Evaluation notes in the Professional Notes section after selecting a submission.</p>}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default PsychologistDashboard;