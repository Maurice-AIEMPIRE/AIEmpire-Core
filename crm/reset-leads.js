const Database = require('better-sqlite3');
const db = new Database('./crm.db');

// Lösche Fake-Leads
db.exec('DELETE FROM leads');

console.log('✅ Fake-Leads gelöscht');

// Erstelle echte Lead-Struktur
db.exec(`
  DROP TABLE IF EXISTS leads_v2;
  CREATE TABLE leads_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    company TEXT,
    role TEXT,
    email TEXT,
    phone TEXT,
    linkedin TEXT,
    budget TEXT,
    authority TEXT,
    need TEXT,
    timeline TEXT,
    bant_score INTEGER DEFAULT 0,
    source TEXT,
    signal TEXT,
    signal_date DATE,
    engagement_score INTEGER DEFAULT 0,
    stage TEXT DEFAULT 'new',
    next_action TEXT,
    next_action_date DATE,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
`);

console.log('✅ Leads V2 Tabelle erstellt (BANT + Signal-basiert)');

// Füge Anleitungs-Leads ein
const stmt = db.prepare(`
  INSERT INTO leads_v2 (name, company, role, source, signal, need, bant_score, stage, notes)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

stmt.run(
  '👉 DEIN ERSTER ECHTER LEAD',
  'Trage hier echte Firma ein',
  'Entscheider-Rolle',
  'Woher kennst du ihn?',
  'Was war das Kaufsignal?',
  'Welches Problem hat er?',
  0,
  'new',
  'BANT ausfüllen: Budget? Authority? Need? Timeline?'
);

console.log('');
console.log('═══════════════════════════════════════════');
console.log('  DIRK KREUTER LEAD-SYSTEM AKTIVIERT');
console.log('═══════════════════════════════════════════');
console.log('');
console.log('ECHTE LEADS kommen von:');
console.log('1. Deinem bestehenden Netzwerk (16 Jahre BMA!)');
console.log('2. LinkedIn-Kommentatoren auf deine Posts');
console.log('3. Empfehlungen von zufriedenen Kunden');
console.log('4. Webinar/Content Inbound');
console.log('');
console.log('JEDER Lead braucht:');
console.log('- Konkretes KAUFSIGNAL (nicht nur Firmenname)');
console.log('- BANT Score (Budget, Authority, Need, Timeline)');
console.log('- Nächste Aktion + Datum');
console.log('');
console.log('❌ BMW, Siemens, VW = KEINE Leads');
console.log('✅ "Thomas, Elektromeister, fragte nach AI" = LEAD');
console.log('');

db.close();
