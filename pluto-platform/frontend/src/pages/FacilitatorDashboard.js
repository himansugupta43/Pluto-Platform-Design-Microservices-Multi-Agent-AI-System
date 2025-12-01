import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const API_URL = 'http://localhost:8000';

function FacilitatorDashboard() {
    const navigate = useNavigate();
    const [submissions, setSubmissions] = useState([]);
    const [psychologists, setPsychologists] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [assigning, setAssigning] = useState(null);
    const [user, setUser] = useState(null);
    const [batchMode, setBatchMode] = useState(false);
    const [selectedDrawings, setSelectedDrawings] = useState([]);
    const [batchPsychologist, setBatchPsychologist] = useState('');

    const fetchData = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const [subResponse, psychResponse] = await Promise.all([
                axios.get(`${API_URL}/api/assessments/facilitator`, { headers: { Authorization: `Bearer ${token}` } }),
                axios.get(`${API_URL}/api/psychologists`, { headers: { Authorization: `Bearer ${token}` } })
            ]);
            setSubmissions(subResponse.data);
            setPsychologists(psychResponse.data);
        } catch (err) {
            setError('Failed to fetch data.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const loggedInUser = localStorage.getItem('user');
        if (loggedInUser) {
            setUser(JSON.parse(loggedInUser));
        }
        fetchData();
    }, []);
    
    const handleAssign = async (drawingId, psychologistId) => {
        if (!psychologistId) return;
        try {
            const token = localStorage.getItem('token');
            await axios.put(`${API_URL}/api/drawings/${drawingId}/assign/${psychologistId}`, {}, {
                 headers: { Authorization: `Bearer ${token}` }
            });
            setAssigning(null);
            fetchData();
        } catch (err) {
            alert('Failed to assign drawing.');
        }
    };

    const handleBatchAssign = async () => {
        if (!batchPsychologist || selectedDrawings.length === 0) {
            alert('Please select a psychologist and at least one drawing.');
            return;
        }
        try {
            const token = localStorage.getItem('token');
            await Promise.all(
                selectedDrawings.map(drawingId =>
                    axios.put(`${API_URL}/api/drawings/${drawingId}/assign/${batchPsychologist}`, {}, {
                        headers: { Authorization: `Bearer ${token}` }
                    })
                )
            );
            alert(`Successfully assigned ${selectedDrawings.length} drawing(s)`);
            setBatchMode(false);
            setSelectedDrawings([]);
            setBatchPsychologist('');
            fetchData();
        } catch (err) {
            alert('Failed to assign drawings.');
        }
    };

    const handleSelectDrawing = (drawingId) => {
        setSelectedDrawings(prev =>
            prev.includes(drawingId) ? prev.filter(id => id !== drawingId) : [...prev, drawingId]
        );
    };

    const handleSelectAll = () => {
        const unassignedDrawings = submissions.filter(s => s.status === 'submitted').map(s => s.id);
        if (selectedDrawings.length === unassignedDrawings.length) {
            setSelectedDrawings([]);
        } else {
            setSelectedDrawings(unassignedDrawings);
        }
    };

    if (loading) return <div>Loading...</div>;
    if (error) return <div>{error}</div>;

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        navigate('/login');
    };

    const stats = {
        total: submissions.length,
        pending: submissions.filter(s => s.status === 'submitted').length,
        completed: submissions.filter(s => s.status === 'reviewed').length,
        failed: submissions.filter(s => s.status === 'failed').length,
    };

    return (
        <div>
            <nav className="navbar">
                <div className="navbar-logo logo">Facilitator Portal</div>
                <div className="navbar-user-info user-info">
                    <span>{user ? user.email : 'Facilitator'}</span>
                    <div className="user-avatar">F</div>
                    <button onClick={handleLogout} className="btn btn-secondary">Logout</button>
                </div>
            </nav>
            <div className="dashboard-container">
                <h1 className="page-title">Dashboard</h1>
                <p className="page-subtitle">Monitor student progress and manage assessments.</p>

                <div className="stats-grid">
                    <div className="stat-card"><div className="stat-number">{stats.total}</div><div className="stat-label">Total Submissions</div></div>
                    <div className="stat-card"><div className="stat-number">{stats.pending}</div><div className="stat-label">Pending Reviews</div></div>
                    <div className="stat-card"><div className="stat-number">{stats.completed}</div><div className="stat-label">Completed Assessments</div></div>
                    <div className="stat-card"><div className="stat-number">{stats.failed}</div><div className="stat-label">Failed Analyses</div></div>
                </div>

                <div className="content-section">
                    <div className="section-header">
                        <h2 className="section-title">Recent Submissions</h2>
                        <button 
                            className="btn btn-primary" 
                            onClick={() => {
                                setBatchMode(!batchMode);
                                setSelectedDrawings([]);
                                setBatchPsychologist('');
                            }}
                        >
                            {batchMode ? 'Cancel Batch Mode' : 'Batch Assignment'}
                        </button>
                    </div>
                    
                    {batchMode && (
                        <div style={{marginBottom: '1rem', padding: '1rem', background: '#f3f4f6', borderRadius: '8px'}}>
                            <div style={{display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap'}}>
                                <button className="btn btn-secondary" onClick={handleSelectAll}>
                                    {selectedDrawings.length === submissions.filter(s => s.status === 'submitted').length ? 'Deselect All' : 'Select All'}
                                </button>
                                <select 
                                    value={batchPsychologist} 
                                    onChange={(e) => setBatchPsychologist(e.target.value)}
                                    style={{padding: '0.5rem', borderRadius: '4px', border: '1px solid #d1d5db'}}
                                >
                                    <option value="">Select Psychologist...</option>
                                    {psychologists.map(p => <option key={p.id} value={p.id}>{p.email}</option>)}
                                </select>
                                <button 
                                    className="btn btn-primary" 
                                    onClick={handleBatchAssign}
                                    disabled={!batchPsychologist || selectedDrawings.length === 0}
                                >
                                    Assign {selectedDrawings.length} Drawing(s)
                                </button>
                            </div>
                        </div>
                    )}
                    
                    <table className="submissions-table">
                        <thead>
                            <tr>
                                {batchMode && <th>Select</th>}
                                <th>Student</th>
                                <th>Submitted At</th>
                                <th>Status</th>
                                <th>Assigned To</th>
                                {!batchMode && <th>Action</th>}
                            </tr>
                        </thead>
                        <tbody>
                            {submissions.map((sub) => (
                                <tr key={sub.id}>
                                    {batchMode && (
                                        <td>
                                            {sub.status === 'submitted' && (
                                                <input 
                                                    type="checkbox" 
                                                    checked={selectedDrawings.includes(sub.id)}
                                                    onChange={() => handleSelectDrawing(sub.id)}
                                                />
                                            )}
                                        </td>
                                    )}
                                    <td>{sub.student.email}</td>
                                    <td>{new Date(sub.submitted_at).toLocaleString()}</td>
                                    <td><span className={`status-badge status-${sub.status.replace('_', '-')}`}>{sub.status}</span></td>
                                    <td>{sub.psychologist ? sub.psychologist.email : 'Unassigned'}</td>
                                    {!batchMode && (
                                        <td>
                                            {sub.status === 'submitted' ? (
                                                assigning === sub.id ? (
                                                    <select onChange={(e) => handleAssign(sub.id, e.target.value)} onBlur={() => setAssigning(null)} defaultValue="">
                                                        <option value="" disabled>Select...</option>
                                                        {psychologists.map(p => <option key={p.id} value={p.id}>{p.email}</option>)}
                                                    </select>
                                                ) : (
                                                    <button className="btn btn-primary" onClick={() => setAssigning(sub.id)}>Assign</button>
                                                )
                                            ) : ' - '}
                                        </td>
                                    )}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

export default FacilitatorDashboard;