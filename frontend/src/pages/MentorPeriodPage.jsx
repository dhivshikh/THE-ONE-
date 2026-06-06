import { useState, useEffect } from 'react';
import axios from 'axios';
import { Save, AlertTriangle } from 'lucide-react';
import { useDepartmentContext } from '../context/DepartmentContext';

export default function MentorPeriodPage() {
    const { departments } = useDepartmentContext();
    const [settings, setSettings] = useState({
        is_enabled: false,
        departments: [],
        years: [],
        classes: []
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [semesters, setSemesters] = useState([]);

    useEffect(() => {
        fetchSettings();
        fetchSemesters();
    }, []);

    const fetchSettings = async () => {
        try {
            const res = await axios.get('http://localhost:8000/api/mentor-period');
            const data = res.data;
            setSettings({
                is_enabled: data.is_enabled,
                departments: Array.isArray(data.departments) ? data.departments : (data.departments ? data.departments.split(',').map(Number) : []),
                years: Array.isArray(data.years) ? data.years : (data.years ? data.years.split(',').map(Number) : []),
                classes: Array.isArray(data.classes) ? data.classes : (data.classes ? data.classes.split(',').map(Number) : [])
            });
            setError(null);
        } catch (err) {
            setError('Failed to load Mentor Period settings.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const fetchSemesters = async () => {
        try {
            const res = await axios.get('http://localhost:8000/api/semesters');
            setSemesters(res.data);
        } catch (err) {
            console.error('Failed to load semesters', err);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const payload = {
                is_enabled: settings.is_enabled,
                departments: settings.departments,
                years: settings.years,
                classes: settings.classes
            };
            await axios.post('http://localhost:8000/api/mentor-period', payload);
            alert('Settings saved successfully! You must re-generate the timetable for changes to take effect.');
            setError(null);
        } catch (err) {
            setError('Failed to save settings.');
            console.error(err);
        } finally {
            setSaving(false);
        }
    };

    const toggleSelection = (type, id) => {
        setSettings(prev => {
            const current = prev[type];
            if (current.includes(id)) {
                return { ...prev, [type]: current.filter(x => x !== id) };
            } else {
                return { ...prev, [type]: [...current, id] };
            }
        });
    };

    if (loading) return <div className="loading">Loading...</div>;

    return (
        <div className="page-container">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Mentor Period</h1>
                    <p className="page-subtitle">Configure global scheduling rule for Mentor Period</p>
                </div>
                <button 
                    className="btn btn-primary"
                    onClick={handleSave}
                    disabled={saving}
                >
                    <Save size={18} />
                    {saving ? 'Saving...' : 'Save Settings'}
                </button>
            </div>

            {error && <div className="error-banner">{error}</div>}

            <div className="card mb-6">
                <div className="card-header">
                    <h2 className="card-title">Enable Mentor Period</h2>
                </div>
                <div className="card-body">
                    <div className="flex items-center gap-3">
                        <input 
                            type="checkbox" 
                            id="enable_mentor"
                            checked={settings.is_enabled}
                            onChange={(e) => setSettings({...settings, is_enabled: e.target.checked})}
                            style={{width: '20px', height: '20px'}}
                        />
                        <label htmlFor="enable_mentor" className="font-medium text-lg">
                            Enable Global Mentor Period
                        </label>
                    </div>
                    <p className="text-muted mt-2 text-sm">
                        When enabled, the generator will attempt to find a single common free slot across all selected classes and allocate it as "Mentor Period".
                    </p>
                </div>
            </div>

            <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
                {/* DEPARTMENTS */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Target Departments</h2>
                        <p className="text-muted text-xs">Leave empty to target all departments</p>
                    </div>
                    <div className="card-body" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                        {departments.map(dept => (
                            <div key={dept.id} className="flex items-center gap-2 mb-2">
                                <input 
                                    type="checkbox" 
                                    id={`dept_${dept.id}`}
                                    checked={settings.departments.includes(dept.id)}
                                    onChange={() => toggleSelection('departments', dept.id)}
                                />
                                <label htmlFor={`dept_${dept.id}`}>{dept.name} ({dept.code})</label>
                            </div>
                        ))}
                    </div>
                </div>

                {/* YEARS */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Target Years</h2>
                        <p className="text-muted text-xs">Leave empty to target all years</p>
                    </div>
                    <div className="card-body" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                        {[1, 2, 3, 4].map(year => (
                            <div key={year} className="flex items-center gap-2 mb-2">
                                <input 
                                    type="checkbox" 
                                    id={`year_${year}`}
                                    checked={settings.years.includes(year)}
                                    onChange={() => toggleSelection('years', year)}
                                />
                                <label htmlFor={`year_${year}`}>Year {year}</label>
                            </div>
                        ))}
                    </div>
                </div>

                {/* CLASSES */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Target Specific Classes</h2>
                        <p className="text-muted text-xs">Leave empty to use Department/Year rules</p>
                    </div>
                    <div className="card-body" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                        {semesters.map(sem => (
                            <div key={sem.id} className="flex items-center gap-2 mb-2">
                                <input 
                                    type="checkbox" 
                                    id={`class_${sem.id}`}
                                    checked={settings.classes.includes(sem.id)}
                                    onChange={() => toggleSelection('classes', sem.id)}
                                />
                                <label htmlFor={`class_${sem.id}`}>{sem.name} ({sem.code})</label>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <div className="card mt-6 bg-yellow-50 border-yellow-200">
                <div className="card-body flex gap-3">
                    <AlertTriangle className="text-yellow-600 flex-shrink-0 mt-1" />
                    <div>
                        <h3 className="font-semibold text-yellow-800">Important Notes</h3>
                        <ul className="list-disc pl-5 mt-2 text-sm text-yellow-700 space-y-1">
                            <li>You must re-generate the timetable for these changes to take effect.</li>
                            <li>Mentor Period will only be scheduled if a common free slot is available across all targeted classes.</li>
                            <li>If no common slot is found, an error will be reported in the generator logs and the period will not be scheduled.</li>
                            <li>All teachers will remain free during the chosen Mentor Period slot.</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
}
