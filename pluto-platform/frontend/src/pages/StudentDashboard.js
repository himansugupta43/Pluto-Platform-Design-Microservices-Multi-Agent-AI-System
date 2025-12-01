import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { ReactSketchCanvas } from 'react-sketch-canvas';
import { useNavigate } from 'react-router-dom';

const API_URL = 'http://localhost:8000';

// Helper to convert the canvas's Data URL output to a Blob for file upload
function dataURLtoBlob(dataurl) {
    const arr = dataurl.split(',');
    if (arr.length < 2) return null;
    
    const mimeMatch = arr[0].match(/:(.*?);/);
    if (!mimeMatch || mimeMatch.length < 2) return null;
    
    const mime = mimeMatch[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
        u8arr[n] = bstr.charCodeAt(n);
    }
    return new Blob([u8arr], { type: mime });
}

function StudentDashboard() {
    const navigate = useNavigate();
    const [view, setView] = useState('choice'); // 'choice', 'upload', 'draw', 'submitted'
    const [selectedFile, setSelectedFile] = useState(null);
    const [fileName, setFileName] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submissions, setSubmissions] = useState([]);
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');
    const [user, setUser] = useState(null);
    const [selectedNotes, setSelectedNotes] = useState(null);
    const canvasRef = useRef(null);

    const fetchSubmissions = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await axios.get(`${API_URL}/api/my-submissions`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setSubmissions(response.data);
        } catch (err) {
            console.error("Could not fetch submissions", err);
        }
    };

    useEffect(() => {
        const loggedInUser = localStorage.getItem('user');
        if (loggedInUser) {
            setUser(JSON.parse(loggedInUser));
        }
        fetchSubmissions();
    }, []);

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file) {
            setSelectedFile(file);
            setFileName(`Selected: ${file.name}`);
            setMessage('');
            setError('');
        }
    };
    
    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        navigate('/login');
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        let fileToUpload = selectedFile;
        let uploadFileName = selectedFile ? selectedFile.name : 'drawing.png';

        if (view === 'draw') {
            try {
                const canvasData = await canvasRef.current.exportImage('png');
                fileToUpload = dataURLtoBlob(canvasData);
                uploadFileName = `canvas-drawing-${Date.now()}.png`;
            } catch (e) {
                setError('Could not get image from canvas. Please draw something first.');
                console.error(e);
                return;
            }
        }

        if (!fileToUpload) {
            setError('Please select or create a drawing to upload.');
            return;
        }

        setIsSubmitting(true);
        setError('');
        setMessage('');

        const formData = new FormData();
        formData.append('file', fileToUpload, uploadFileName);

        try {
            const token = localStorage.getItem('token');
            await axios.post(`${API_URL}/api/drawings/upload`, formData, {
                headers: { 'Content-Type': 'multipart/form-data', 'Authorization': `Bearer ${token}` }
            });
            setView('submitted');
            fetchSubmissions();
            setSelectedFile(null);
            setFileName('');
        } catch (err) {
            setError('Upload failed. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const resetToChoice = () => {
        setView('choice');
        setSelectedFile(null);
        setFileName('');
        setError('');
        setMessage('');
        if(canvasRef.current) {
            canvasRef.current.clearCanvas();
        }
    };

    const renderHistory = () => (
        <div className="history-card">
            <h2>Your Submission History</h2>
            <table className="submissions-table">
                <thead><tr><th>Submission ID</th><th>Date</th><th>Status</th><th>Action</th></tr></thead>
                <tbody>
                    {submissions.length > 0 ? submissions.map(sub => (
                        <tr key={sub.id}>
                            <td>{sub.id.substring(0, 8)}...</td>
                            <td>{new Date(sub.submitted_at).toLocaleDateString()}</td>
                            <td><span className={`status-badge status-${sub.status.replace('_', '-')}`}>{sub.status}</span></td>
                            <td>
                                {sub.status === 'reviewed' && sub.evaluation?.notes ? (
                                    <button className="btn btn-primary" onClick={() => setSelectedNotes(sub.evaluation.notes)}>View Notes</button>
                                ) : ( <span>-</span> )}
                            </td>
                        </tr>
                    )) : <tr><td colSpan="4" style={{textAlign: 'center'}}>No submissions yet.</td></tr>}
                </tbody>
            </table>
        </div>
    );
    
    const renderContent = () => {
        switch (view) {
            case 'upload':
            case 'draw':
                return (
                    <div className="student-dashboard-grid">
                        <div className="welcome-card">
                            <h1 className="welcome-title">Welcome to your HTP Drawing Assessment</h1>
                            <p className="welcome-subtitle">You will be asked to create a drawing of a Person. Please upload your drawing below.</p>
                            <div className="session-info"><strong>Session ID:</strong> A-124321<br /><strong>Date:</strong> October 2, 2025</div>
                        </div>
                        <div className="drawing-area">
                            <form onSubmit={handleSubmit}>
                                {view === 'upload' ? (
                                    <>
                                        <h2 className="drawing-title">Upload Your Drawing</h2>
                                        <label htmlFor="fileUpload" className="upload-box">
                                            <div className="upload-icon">
                                                📤
                                            </div>
                                            <p>Click here to select your file</p>
                                            <input type="file" id="fileUpload" onChange={handleFileChange} accept="image/*" style={{ display: 'none' }} />
                                        </label>
                                        <p id="fileName">{fileName}</p>
                                    </>
                                ) : (
                                    <>
                                        <h2 className="drawing-title">Draw a Person</h2>
                                        <ReactSketchCanvas
                                            ref={canvasRef}
                                            strokeWidth={4}
                                            strokeColor="black"
                                            canvasColor="white"
                                            height="300px"
                                            width="100%"
                                            style={{ border: '2px dashed #ccc', borderRadius: '15px' }}
                                        />
                                        <div style={{textAlign: 'center', marginTop: '10px'}}>
                                            <button type="button" className="btn btn-secondary" onClick={() => canvasRef.current.clearCanvas()}>Clear</button>
                                            <button type="button" className="btn btn-secondary" style={{marginLeft: '10px'}} onClick={() => canvasRef.current.undo()}>Undo</button>
                                        </div>
                                    </>
                                )}
                                <button type="submit" className="submit-btn" disabled={isSubmitting || (view === 'upload' && !selectedFile)}>
                                    {isSubmitting ? 'Submitting...' : "I'm Finished!"}
                                </button>
                            </form>
                            {error && <p style={{ color: 'red', textAlign: 'center', marginTop: '10px' }}>{error}</p>}
                        </div>
                        <div className="instructions-panel">
                            <h3 className="instructions-title">Instructions</h3>
                            <div className="instruction-step"><div className="step-number">Step 1</div>Draw a person on a piece of paper as well as you can.</div>
                            <div className="instruction-step"><div className="step-number">Step 2</div>Take a clear photo or scan of your drawing.</div>
                            <div className="instruction-step"><div className="step-number">Step 3</div>Click the upload box to select your image file.</div>
                            <div className="instruction-step"><div className="step-number">Step 4</div>Click "I'm Finished!" to submit your drawing for analysis.</div>
                        </div>
                    </div>
                );
            case 'submitted':
                return (
                    <>
                        <div className="confirmation-message" style={{background: 'white', border: 'none', boxShadow: 'var(--shadow)', borderRadius: '20px', gridColumn: '1 / -1'}}>
                            <h2>🎉 Great Job!</h2><p>Your drawing has been submitted.</p>
                        </div>
                        {renderHistory()}
                        <div className="home-button-container" style={{marginTop: '20px', gridColumn: '1 / -1'}}>
                            <button className="btn btn-primary" onClick={resetToChoice}>Submit Another Drawing</button>
                        </div>
                    </>
                );
            case 'choice':
            default:
                return (
                    <>
                        <div className="welcome-card" style={{gridColumn: '1 / -1'}}>
                            <h1 className="welcome-title">Welcome to your HTP Drawing Assessment</h1>
                            <p className="welcome-subtitle">Please choose how you would like to submit your drawing.</p>
                        </div>
                        <div id="choiceSection" className="choice-card" style={{background: 'none', boxShadow: 'none', gridColumn: '1 / -1'}}>
                            <div className="choice-buttons" style={{ display: 'flex', justifyContent: 'center', gap: '30px' }}>
                                <button className="btn btn-primary" style={{padding: '50px', fontSize: '20px'}} onClick={() => setView('draw')}>🎨 Draw on Screen</button>
                                <button className="btn btn-primary" style={{padding: '50px', fontSize: '20px'}} onClick={() => setView('upload')}>⬆️ Upload Drawing</button>
                            </div>
                        </div>
                        {renderHistory()}
                    </>
                );
        }
    };
    
    return (
        <div className="student-dashboard-body">
            {selectedNotes && (
                <div style={{position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000}}>
                    <div style={{background: 'white', padding: '30px', borderRadius: '10px', width: '90%', maxWidth: '500px'}}>
                        <h2>Psychologist's Notes</h2>
                        <p style={{marginTop: '15px', whiteSpace: 'pre-wrap'}}>{selectedNotes}</p>
                        <button className="btn-primary" style={{marginTop: '20px'}} onClick={() => setSelectedNotes(null)}>Close</button>
                    </div>
                </div>
            )}
            <nav className="navbar">
                <div className="navbar-logo logo">My Drawing Space</div>
                <div className="navbar-user-info user-info">
                    <span>{user ? user.email : 'Student'}</span>
                    <div className="user-avatar">{user ? user.email.charAt(0).toUpperCase() : 'S'}</div>
                    <button onClick={handleLogout} className="btn btn-secondary">Logout</button>
                </div>
            </nav>
            <div className="dashboard-container">
                {renderContent()}
            </div>
        </div>
    );
}

export default StudentDashboard;