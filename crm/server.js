const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const Database = require('better-sqlite3');
const cors = require('cors');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: '*' } });

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// SQLite Database
const db = new Database('./crm.db');

// Create Tables
db.exec(`
  CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    industry TEXT,
    contact_name TEXT,
    email TEXT,
    phone TEXT,
    status TEXT DEFAULT 'new',
    priority TEXT DEFAULT 'medium',
    potential_revenue INTEGER,
    pain_points TEXT,
    notes TEXT,
    source TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS partners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT,
    contact_email TEXT,
    status TEXT DEFAULT 'prospect',
    potential_value INTEGER,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER,
    title TEXT NOT NULL,
    value INTEGER,
    stage TEXT DEFAULT 'qualification',
    probability INTEGER DEFAULT 10,
    close_date DATE,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id)
  );

  CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT,
    entity_id INTEGER,
    action TEXT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS gold_nuggets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    category TEXT,
    monetization_potential TEXT,
    source TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT,
    status TEXT DEFAULT 'idle',
    tasks_completed INTEGER DEFAULT 0,
    last_active DATETIME
  );
`);

// API Routes

// LEADS
app.get('/api/leads', (req, res) => {
  const leads = db.prepare('SELECT * FROM leads ORDER BY created_at DESC').all();
  res.json(leads);
});

app.post('/api/leads', (req, res) => {
  const { company, industry, contact_name, email, phone, status, priority, potential_revenue, pain_points, notes, source } = req.body;
  const stmt = db.prepare('INSERT INTO leads (company, industry, contact_name, email, phone, status, priority, potential_revenue, pain_points, notes, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)');
  const result = stmt.run(company, industry, contact_name, email, phone, status || 'new', priority || 'medium', potential_revenue, pain_points, notes, source);
  io.emit('lead_added', { id: result.lastInsertRowid, company });
  res.json({ id: result.lastInsertRowid, success: true });
});

app.put('/api/leads/:id', (req, res) => {
  const { id } = req.params;
  const { status, priority, notes } = req.body;
  db.prepare('UPDATE leads SET status = ?, priority = ?, notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?').run(status, priority, notes, id);
  io.emit('lead_updated', { id });
  res.json({ success: true });
});

// PARTNERS
app.get('/api/partners', (req, res) => {
  const partners = db.prepare('SELECT * FROM partners ORDER BY created_at DESC').all();
  res.json(partners);
});

app.post('/api/partners', (req, res) => {
  const { name, type, contact_email, status, potential_value, notes } = req.body;
  const stmt = db.prepare('INSERT INTO partners (name, type, contact_email, status, potential_value, notes) VALUES (?, ?, ?, ?, ?, ?)');
  const result = stmt.run(name, type, contact_email, status, potential_value, notes);
  res.json({ id: result.lastInsertRowid, success: true });
});

// DEALS
app.get('/api/deals', (req, res) => {
  const deals = db.prepare(`
    SELECT d.*, l.company as lead_company
    FROM deals d
    LEFT JOIN leads l ON d.lead_id = l.id
    ORDER BY d.created_at DESC
  `).all();
  res.json(deals);
});

app.post('/api/deals', (req, res) => {
  const { lead_id, title, value, stage, probability, close_date, notes } = req.body;
  const stmt = db.prepare('INSERT INTO deals (lead_id, title, value, stage, probability, close_date, notes) VALUES (?, ?, ?, ?, ?, ?, ?)');
  const result = stmt.run(lead_id, title, value, stage, probability, close_date, notes);
  res.json({ id: result.lastInsertRowid, success: true });
});

// GOLD NUGGETS
app.get('/api/nuggets', (req, res) => {
  const nuggets = db.prepare('SELECT * FROM gold_nuggets ORDER BY created_at DESC').all();
  res.json(nuggets);
});

app.post('/api/nuggets', (req, res) => {
  const { title, content, category, monetization_potential, source } = req.body;
  const stmt = db.prepare('INSERT INTO gold_nuggets (title, content, category, monetization_potential, source) VALUES (?, ?, ?, ?, ?)');
  const result = stmt.run(title, content, category, monetization_potential, source);
  res.json({ id: result.lastInsertRowid, success: true });
});

// AGENTS
app.get('/api/agents', (req, res) => {
  const agents = db.prepare('SELECT * FROM agents ORDER BY last_active DESC').all();
  res.json(agents);
});

// DASHBOARD STATS
app.get('/api/stats', (req, res) => {
  const leadCount = db.prepare('SELECT COUNT(*) as count FROM leads').get();
  const dealValue = db.prepare('SELECT SUM(value) as total FROM deals').get();
  const partnerCount = db.prepare('SELECT COUNT(*) as count FROM partners').get();
  const nuggetCount = db.prepare('SELECT COUNT(*) as count FROM gold_nuggets').get();

  const pipeline = db.prepare(`
    SELECT stage, COUNT(*) as count, SUM(value) as value
    FROM deals GROUP BY stage
  `).all();

  res.json({
    leads: leadCount.count,
    dealValue: dealValue.total || 0,
    partners: partnerCount.count,
    nuggets: nuggetCount.count,
    pipeline
  });
});

// BULK IMPORT
app.post('/api/import/leads', (req, res) => {
  const { leads } = req.body;
  const stmt = db.prepare('INSERT INTO leads (company, industry, contact_name, email, status, priority, potential_revenue, pain_points, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)');

  const insertMany = db.transaction((items) => {
    for (const lead of items) {
      stmt.run(lead.company, lead.industry, lead.contact_name, lead.email, lead.status || 'new', lead.priority || 'medium', lead.potential_revenue, lead.pain_points, lead.source || 'import');
    }
  });

  insertMany(leads);
  res.json({ success: true, count: leads.length });
});

// Socket.IO
io.on('connection', (socket) => {
  console.log('Client connected');
  socket.on('disconnect', () => console.log('Client disconnected'));
});

const PORT = process.env.PORT || 3500;
server.listen(PORT, () => {
  console.log(`AI Empire CRM running on http://localhost:${PORT}`);
});
