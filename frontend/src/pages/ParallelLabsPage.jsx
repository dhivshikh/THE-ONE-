import { useState, useEffect } from 'react';
import {
    parallelLabBasketsApi,
    departmentsApi,
    subjectsApi,
    teachersApi,
    roomsApi,
    semestersApi,
} from '../services/api';
import { Plus, Trash2, Save, X, Edit2, Upload, Download, CheckCircle, AlertCircle } from 'lucide-react';
import './ParallelLabsPage.css';

const emptySubject = {
    subject_id: '',
    batch_name: '',
    component_type: 'lab',
    theory_teacher_id: '',
    lab_teacher_ids: ['', '', ''],
    room_id: '',
    hours: 2,
};

const emptyForm = (deptId = '') => ({
    name: '',
    code: '',
    dept_id: deptId,
    year: 1,
    section: 'A',
    semester_number: '',
    class_ids: [],
    subjects: [{ ...emptySubject }],
});

export default function ParallelLabsPage() {
    const [baskets, setBaskets] = useState([]);
    const [departments, setDepartments] = useState([]);
    const [selectedDeptId, setSelectedDeptId] = useState('');
    const [showForm, setShowForm] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [formData, setFormData] = useState(emptyForm());
    const [allSubjects, setAllSubjects] = useState([]);
    const [allTeachers, setAllTeachers] = useState([]);
    const [allRooms, setAllRooms] = useState([]);
    const [allSemesters, setAllSemesters] = useState([]);
    const [importFile, setImportFile] = useState(null);
    const [importResult, setImportResult] = useState(null);
    const [importLoading, setImportLoading] = useState(false);
    const [importCommitting, setImportCommitting] = useState(false);

    useEffect(() => {
        fetchDepartments();
        fetchAllFormData();
    }, []);

    useEffect(() => {
        fetchBaskets();
    }, [selectedDeptId]);

    const fetchDepartments = async () => {
        try {
            const res = await departmentsApi.getAll();
            setDepartments(res.data);
            if (res.data.length > 0) {
                setSelectedDeptId(res.data[0].id);
                setFormData(emptyForm(res.data[0].id));
            }
        } catch (err) {
            console.error('Failed to fetch departments:', err);
        }
    };

    const fetchAllFormData = async () => {
        try {
            const [subjRes, teachRes, roomRes, semRes] = await Promise.all([
                subjectsApi.getAll(),
                teachersApi.getAll(),
                roomsApi.getAll(),
                semestersApi.getAll(),
            ]);
            setAllSubjects(subjRes.data);
            setAllTeachers(teachRes.data);
            setAllRooms(roomRes.data);
            setAllSemesters(semRes.data);
        } catch (err) {
            console.error('Failed to fetch form data details:', err);
        }
    };

    const fetchBaskets = async () => {
        try {
            const res = await parallelLabBasketsApi.getAll(selectedDeptId);
            setBaskets(res.data);
        } catch (err) {
            console.error('Failed to fetch baskets:', err);
        }
    };

    const teacherName = (id) => allTeachers.find(t => Number(t.id) === Number(id))?.name || `Teacher ${id}`;
    const subjectLabel = (id) => {
        const subject = allSubjects.find(s => Number(s.id) === Number(id));
        return subject ? `${subject.code} - ${subject.name}` : `Subject ${id}`;
    };
    const roomName = (id) => allRooms.find(r => Number(r.id) === Number(id))?.name || `Room ${id}`;
    const classLabel = (id) => {
        const semester = allSemesters.find(s => Number(s.id) === Number(id));
        return semester ? `${semester.code} - ${semester.name}` : `Class ${id}`;
    };

    const filteredClasses = allSemesters.filter((sem) => !formData.dept_id || Number(sem.dept_id) === Number(formData.dept_id));
    const labRooms = allRooms.filter((room) => room.room_type === 'lab');

    const handleDelete = async (id) => {
        if (!confirm('Are you sure you want to delete this parallel basket?')) return;
        try {
            await parallelLabBasketsApi.delete(id);
            fetchBaskets();
        } catch (err) {
            alert('Failed to delete basket.');
        }
    };

    const normalizeSubjectForForm = (s) => ({
        subject_id: s.subject_id || '',
        batch_name: s.batch_name || '',
        component_type: s.component_type || 'lab',
        theory_teacher_id: s.theory_teacher_id || '',
        lab_teacher_ids: [
            ...(s.lab_teacher_ids || (s.teacher_id ? [s.teacher_id] : [])),
            '',
            '',
            '',
        ].slice(0, 3),
        room_id: s.room_id || '',
        hours: s.hours || 2,
    });

    const handleEdit = (basket) => {
        setEditingId(basket.id);
        setFormData({
            name: basket.name || '',
            code: basket.code || '',
            dept_id: basket.dept_id,
            year: basket.year,
            section: basket.section || 'A',
            semester_number: basket.semester_number || '',
            class_ids: basket.class_ids || [],
            subjects: basket.basket_subjects?.length
                ? basket.basket_subjects.map(normalizeSubjectForForm)
                : [{ ...emptySubject }],
        });
        setShowForm(true);
    };

    const handleCancel = () => {
        setShowForm(false);
        setEditingId(null);
        setFormData(emptyForm(selectedDeptId));
    };

    const addSubjectRow = () => {
        setFormData({
            ...formData,
            subjects: [...formData.subjects, { ...emptySubject }],
        });
    };

    const updateSubjectRow = (index, field, value) => {
        const newSubjects = [...formData.subjects];
        newSubjects[index] = { ...newSubjects[index], [field]: value };
        setFormData({ ...formData, subjects: newSubjects });
    };

    const updateLabTeacher = (index, teacherIndex, value) => {
        const newSubjects = [...formData.subjects];
        const ids = [...(newSubjects[index].lab_teacher_ids || ['', '', ''])];
        ids[teacherIndex] = value;
        newSubjects[index] = { ...newSubjects[index], lab_teacher_ids: ids };
        setFormData({ ...formData, subjects: newSubjects });
    };

    const removeSubjectRow = (index) => {
        const newSubjects = [...formData.subjects];
        newSubjects.splice(index, 1);
        setFormData({ ...formData, subjects: newSubjects });
    };

    const toggleClass = (classId) => {
        const id = Number(classId);
        const exists = formData.class_ids.map(Number).includes(id);
        const classIds = exists
            ? formData.class_ids.filter(cid => Number(cid) !== id)
            : [...formData.class_ids, id];
        const firstClass = allSemesters.find(s => Number(s.id) === Number(classIds[0]));
        setFormData({
            ...formData,
            class_ids: classIds,
            year: firstClass?.year || formData.year,
            section: firstClass?.section || formData.section,
            semester_number: firstClass?.semester_number || formData.semester_number,
        });
    };

    const buildPayload = () => ({
        ...formData,
        dept_id: Number(formData.dept_id),
        year: Number(formData.year),
        semester_number: formData.semester_number ? Number(formData.semester_number) : null,
        class_ids: formData.class_ids.map(Number),
        subjects: formData.subjects.map(s => {
            const labTeacherIds = (s.lab_teacher_ids || []).filter(Boolean).map(Number);
            return {
                subject_id: Number(s.subject_id),
                batch_name: s.batch_name || '',
                component_type: s.component_type,
                theory_teacher_id: s.theory_teacher_id ? Number(s.theory_teacher_id) : null,
                lab_teacher_ids: labTeacherIds,
                teacher_id: labTeacherIds[0] || null,
                room_id: s.room_id ? Number(s.room_id) : null,
                hours: Number(s.hours || 2),
            };
        }),
    });

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const payload = buildPayload();
            if (editingId) {
                await parallelLabBasketsApi.update(editingId, payload);
            } else {
                await parallelLabBasketsApi.create(payload);
            }
            setShowForm(false);
            setEditingId(null);
            setFormData(emptyForm(selectedDeptId));
            fetchBaskets();
        } catch (err) {
            console.error(err);
            alert(err.response?.data?.detail || 'Failed to save basket. Check required faculty and room fields.');
        }
    };

    const uploadImport = async () => {
        if (!importFile) return;
        setImportLoading(true);
        try {
            const res = await parallelLabBasketsApi.uploadImport(importFile);
            setImportResult(res.data);
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to validate import file.');
        } finally {
            setImportLoading(false);
        }
    };

    const commitImport = async () => {
        if (!importResult?.batch_id) return;
        setImportCommitting(true);
        try {
            const res = await parallelLabBasketsApi.commitImport(importResult.batch_id);
            setImportResult(res.data);
            fetchBaskets();
        } catch (err) {
            alert(err.response?.data?.detail || 'Failed to commit import.');
        } finally {
            setImportCommitting(false);
        }
    };

    return (
        <div className="parallel-labs-page">
            <div className="page-header">
                <div>
                    <h1>Parallel Baskets</h1>
                    <p>Manage separate theory and lab faculty for coordinated batches</p>
                </div>
                <button className="btn btn-primary" onClick={() => {
                    handleCancel();
                    setShowForm(true);
                }}>
                    <Plus size={16} /> New Basket
                </button>
            </div>

            <div className="filters card">
                <div className="form-group">
                    <label>Department</label>
                    <select value={selectedDeptId} onChange={(e) => setSelectedDeptId(e.target.value)} className="form-input">
                        <option value="">All Departments</option>
                        {departments.map(d => (
                            <option key={d.id} value={d.id}>{d.name} ({d.code})</option>
                        ))}
                    </select>
                </div>
                <div className="import-panel">
                    <input
                        type="file"
                        accept=".xlsx,.xls,.csv"
                        onChange={(e) => {
                            setImportFile(e.target.files?.[0] || null);
                            setImportResult(null);
                        }}
                    />
                    <button className="btn btn-secondary" type="button" onClick={uploadImport} disabled={!importFile || importLoading}>
                        <Upload size={16} /> {importLoading ? 'Validating' : 'Import'}
                    </button>
                    <a className="btn btn-secondary" href={parallelLabBasketsApi.getImportTemplateUrl()}>
                        <Download size={16} /> Template
                    </a>
                </div>
            </div>

            {importResult && (
                <div className="card import-result">
                    <div className="import-summary">
                        {importResult.failed ? <AlertCircle size={18} /> : <CheckCircle size={18} />}
                        <span>{importResult.total_rows || 0} rows, {importResult.failed || 0} invalid</span>
                        {importResult.created_baskets !== undefined && (
                            <span>{importResult.created_baskets} baskets, {importResult.created_entries} new entries, {importResult.updated_entries} updated</span>
                        )}
                    </div>
                    {importResult.batch_id && (importResult.total_rows - importResult.failed > 0) && (
                        <button className="btn btn-primary" onClick={commitImport} disabled={importCommitting}>
                            <Save size={16} /> {importCommitting ? 'Committing' : 'Commit Valid Rows'}
                        </button>
                    )}
                </div>
            )}

            {showForm && (
                <div className="card form-card">
                    <form onSubmit={handleSubmit}>
                        <h3>{editingId ? 'Edit' : 'Create'} Parallel Basket</h3>
                        <div className="form-grid">
                            <div className="form-group">
                                <label>Basket Name</label>
                                <input className="form-input" value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} required />
                            </div>
                            <div className="form-group">
                                <label>Basket Code</label>
                                <input className="form-input" value={formData.code} onChange={e => setFormData({ ...formData, code: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Department</label>
                                <select
                                    className="form-input"
                                    value={formData.dept_id}
                                    onChange={e => setFormData({ ...formData, dept_id: Number(e.target.value), class_ids: [] })}
                                    required
                                >
                                    <option value="">Select Dept</option>
                                    {departments.map(d => <option key={d.id} value={d.id}>{d.code}</option>)}
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Semester</label>
                                <input type="number" className="form-input" min="1" max="8" value={formData.semester_number} onChange={e => setFormData({ ...formData, semester_number: e.target.value })} />
                            </div>
                        </div>

                        <div className="class-picker">
                            {filteredClasses.map(sem => (
                                <label key={sem.id} className="class-chip">
                                    <input
                                        type="checkbox"
                                        checked={formData.class_ids.map(Number).includes(Number(sem.id))}
                                        onChange={() => toggleClass(sem.id)}
                                    />
                                    <span>{sem.code}</span>
                                </label>
                            ))}
                        </div>

                        <div className="section-title">
                            <h4>Subject Entries</h4>
                            <button type="button" className="btn btn-secondary" onClick={addSubjectRow}>
                                <Plus size={16} /> Add Subject
                            </button>
                        </div>

                        <div className="subjects-list">
                            {formData.subjects.map((subj, idx) => (
                                <div key={idx} className="subject-row">
                                    <select className="form-input" required value={subj.subject_id} onChange={e => updateSubjectRow(idx, 'subject_id', e.target.value)}>
                                        <option value="">Subject</option>
                                        {allSubjects.map(s => <option key={s.id} value={s.id}>{s.code} - {s.name}</option>)}
                                    </select>
                                    <select className="form-input" value={subj.component_type} onChange={e => updateSubjectRow(idx, 'component_type', e.target.value)}>
                                        <option value="lab">Lab</option>
                                        <option value="theory">Theory</option>
                                        <option value="both">Both</option>
                                    </select>
                                    <input type="text" className="form-input" placeholder="Batch" value={subj.batch_name} onChange={e => updateSubjectRow(idx, 'batch_name', e.target.value)} />
                                    <input type="number" className="form-input hours-input" min="1" max="10" value={subj.hours} onChange={e => updateSubjectRow(idx, 'hours', e.target.value)} />

                                    {(subj.component_type === 'theory' || subj.component_type === 'both') && (
                                        <select className="form-input" required value={subj.theory_teacher_id} onChange={e => updateSubjectRow(idx, 'theory_teacher_id', e.target.value)}>
                                            <option value="">Theory Faculty</option>
                                            {allTeachers.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                                        </select>
                                    )}

                                    {(subj.component_type === 'lab' || subj.component_type === 'both') && (
                                        <>
                                            {[0, 1, 2].map((teacherIdx) => (
                                                <select
                                                    key={teacherIdx}
                                                    className="form-input"
                                                    required={teacherIdx === 0}
                                                    value={subj.lab_teacher_ids?.[teacherIdx] || ''}
                                                    onChange={e => updateLabTeacher(idx, teacherIdx, e.target.value)}
                                                >
                                                    <option value="">Lab Faculty {teacherIdx + 1}</option>
                                                    {allTeachers.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                                                </select>
                                            ))}
                                            <select className="form-input" required value={subj.room_id} onChange={e => updateSubjectRow(idx, 'room_id', e.target.value)}>
                                                <option value="">Lab Room</option>
                                                {(labRooms.length ? labRooms : allRooms).map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
                                            </select>
                                        </>
                                    )}

                                    <button type="button" className="btn btn-icon btn-danger" onClick={() => removeSubjectRow(idx)} disabled={formData.subjects.length === 1}>
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            ))}
                        </div>

                        <div className="form-actions">
                            <button type="button" className="btn btn-secondary" onClick={handleCancel}><X size={16} /> Cancel</button>
                            <button type="submit" className="btn btn-primary"><Save size={16} /> {editingId ? 'Update' : 'Save'} Basket</button>
                        </div>
                    </form>
                </div>
            )}

            <div className="baskets-grid card">
                <table className="table">
                    <thead>
                        <tr>
                            <th>Basket</th>
                            <th>Classes</th>
                            <th>Subject Entries</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {baskets.length === 0 ? (
                            <tr><td colSpan="4" className="text-center text-muted">No baskets found.</td></tr>
                        ) : baskets.map(b => (
                            <tr key={b.id}>
                                <td>
                                    <strong>{b.name}</strong>
                                    <span className="muted-line">{b.code}</span>
                                </td>
                                <td>
                                    {(b.class_ids || []).length
                                        ? b.class_ids.map(classLabel).join(', ')
                                        : `Dept ${b.dept_id} / Yr ${b.year} / Sec ${b.section}`}
                                </td>
                                <td>
                                    <div className="entry-list">
                                        {b.basket_subjects.map(s => (
                                            <div key={s.id} className="entry-line">
                                                <strong>{s.subject?.code || subjectLabel(s.subject_id)}</strong>
                                                <span>{s.component_type}</span>
                                                {s.batch_name && <span>{s.batch_name}</span>}
                                                {s.theory_teacher_id && <span>Theory: {teacherName(s.theory_teacher_id)}</span>}
                                                {s.lab_teacher_ids?.length > 0 && <span>Lab: {s.lab_teacher_ids.map(teacherName).join(', ')}</span>}
                                                {s.room_id && <span>{roomName(s.room_id)}</span>}
                                            </div>
                                        ))}
                                    </div>
                                </td>
                                <td>
                                    <div className="action-row">
                                        <button className="btn btn-icon btn-secondary" onClick={() => handleEdit(b)}>
                                            <Edit2 size={16} />
                                        </button>
                                        <button className="btn btn-icon btn-danger" onClick={() => handleDelete(b.id)}>
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
