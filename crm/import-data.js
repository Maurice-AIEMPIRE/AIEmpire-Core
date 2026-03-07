// Import existing leads and partners from files
const Database = require('better-sqlite3');
const db = new Database('./crm.db');

// 100 Leads from LEADS_20260208.md
const leads = [
  // Tier 1: Enterprise (€24,900+)
  { company: 'Siemens AG', industry: 'Industrie 4.0', contact_name: 'Dr. Roland Busch', email: 'info@siemens.com', status: 'qualified', priority: 'high', potential_revenue: 250000, pain_points: 'Legacy automation, manual processes' },
  { company: 'BASF SE', industry: 'Chemie', contact_name: 'Martin Brudermüller', email: 'info@basf.com', status: 'new', priority: 'high', potential_revenue: 180000, pain_points: 'Process optimization, documentation' },
  { company: 'Deutsche Telekom', industry: 'Telekommunikation', contact_name: 'Tim Höttges', email: 'info@telekom.de', status: 'new', priority: 'high', potential_revenue: 200000, pain_points: 'Customer service automation' },
  { company: 'BMW Group', industry: 'Automotive', contact_name: 'Oliver Zipse', email: 'info@bmw.de', status: 'new', priority: 'high', potential_revenue: 300000, pain_points: 'Production line AI' },
  { company: 'Volkswagen AG', industry: 'Automotive', contact_name: 'Oliver Blume', email: 'info@vw.de', status: 'new', priority: 'high', potential_revenue: 280000, pain_points: 'Supply chain optimization' },
  { company: 'SAP SE', industry: 'Software', contact_name: 'Christian Klein', email: 'info@sap.com', status: 'qualified', priority: 'high', potential_revenue: 150000, pain_points: 'AI integration' },
  { company: 'Allianz SE', industry: 'Versicherung', contact_name: 'Oliver Bäte', email: 'info@allianz.de', status: 'new', priority: 'high', potential_revenue: 220000, pain_points: 'Claims automation' },
  { company: 'Deutsche Bank', industry: 'Finanz', contact_name: 'Christian Sewing', email: 'info@db.com', status: 'new', priority: 'high', potential_revenue: 190000, pain_points: 'Fraud detection AI' },
  { company: 'Bayer AG', industry: 'Pharma', contact_name: 'Bill Anderson', email: 'info@bayer.com', status: 'new', priority: 'high', potential_revenue: 175000, pain_points: 'Research automation' },
  { company: 'Bosch GmbH', industry: 'Industrie', contact_name: 'Stefan Hartung', email: 'info@bosch.com', status: 'qualified', priority: 'high', potential_revenue: 260000, pain_points: 'IoT + AI integration' },

  // Tier 2: Mittelstand (€12,900)
  { company: 'Würth Group', industry: 'Handel', status: 'new', priority: 'medium', potential_revenue: 85000, pain_points: 'Inventory AI' },
  { company: 'Trumpf GmbH', industry: 'Maschinenbau', status: 'new', priority: 'medium', potential_revenue: 95000, pain_points: 'Predictive maintenance' },
  { company: 'Zeiss AG', industry: 'Optik', status: 'new', priority: 'medium', potential_revenue: 78000, pain_points: 'Quality control AI' },
  { company: 'Heraeus', industry: 'Technologie', status: 'new', priority: 'medium', potential_revenue: 72000, pain_points: 'Material optimization' },
  { company: 'Viessmann', industry: 'Heizung', status: 'new', priority: 'high', potential_revenue: 88000, pain_points: 'Smart home AI' },
  { company: 'Stihl', industry: 'Werkzeuge', status: 'new', priority: 'medium', potential_revenue: 65000, pain_points: 'Production optimization' },
  { company: 'Miele', industry: 'Haushaltsgeräte', status: 'new', priority: 'medium', potential_revenue: 70000, pain_points: 'Smart appliances AI' },
  { company: 'Festo', industry: 'Automatisierung', status: 'qualified', priority: 'high', potential_revenue: 110000, pain_points: 'AI training systems' },
  { company: 'Kärcher', industry: 'Reinigung', status: 'new', priority: 'medium', potential_revenue: 55000, pain_points: 'Autonomous cleaning' },
  { company: 'Hansgrohe', industry: 'Sanitär', status: 'new', priority: 'medium', potential_revenue: 48000, pain_points: 'Smart water AI' },

  // Tier 3: KMU (€4,900)
  { company: 'TechStart GmbH', industry: 'IT', status: 'new', priority: 'medium', potential_revenue: 25000, pain_points: 'Development automation' },
  { company: 'Digital Solutions AG', industry: 'IT', status: 'new', priority: 'medium', potential_revenue: 28000, pain_points: 'Client automation' },
  { company: 'Smart Factory Köln', industry: 'Produktion', status: 'new', priority: 'medium', potential_revenue: 32000, pain_points: 'Production AI' },
  { company: 'Innovation Hub Berlin', industry: 'Startup', status: 'new', priority: 'medium', potential_revenue: 22000, pain_points: 'Rapid prototyping' },
  { company: 'CloudFirst GmbH', industry: 'Cloud', status: 'new', priority: 'medium', potential_revenue: 35000, pain_points: 'Infrastructure AI' },
  { company: 'DataDriven AG', industry: 'Analytics', status: 'qualified', priority: 'high', potential_revenue: 42000, pain_points: 'Advanced analytics' },
  { company: 'AutomateNow', industry: 'Automatisierung', status: 'new', priority: 'medium', potential_revenue: 38000, pain_points: 'Workflow automation' },
  { company: 'SecureIT GmbH', industry: 'Security', status: 'new', priority: 'medium', potential_revenue: 29000, pain_points: 'Security AI' },
  { company: 'GreenTech Solutions', industry: 'Umwelt', status: 'new', priority: 'medium', potential_revenue: 26000, pain_points: 'Sustainability AI' },
  { company: 'HealthTech Pro', industry: 'Gesundheit', status: 'new', priority: 'high', potential_revenue: 45000, pain_points: 'Medical AI' },

  // BMA-Branche (Maurice's Expertise!)
  { company: 'Siemens Fire Safety', industry: 'BMA', status: 'qualified', priority: 'high', potential_revenue: 120000, pain_points: 'BMA AI automation' },
  { company: 'Bosch Sicherheitssysteme', industry: 'BMA', status: 'qualified', priority: 'high', potential_revenue: 115000, pain_points: 'Fire detection AI' },
  { company: 'Honeywell Building', industry: 'BMA', status: 'new', priority: 'high', potential_revenue: 95000, pain_points: 'Smart building AI' },
  { company: 'Hekatron', industry: 'BMA', status: 'qualified', priority: 'high', potential_revenue: 85000, pain_points: 'Detector AI' },
  { company: 'Esser by Honeywell', industry: 'BMA', status: 'new', priority: 'high', potential_revenue: 78000, pain_points: 'System integration' },
  { company: 'Notifier Deutschland', industry: 'BMA', status: 'new', priority: 'medium', potential_revenue: 65000, pain_points: 'Installation AI' },
  { company: 'Labor Strauss', industry: 'BMA', status: 'new', priority: 'medium', potential_revenue: 55000, pain_points: 'Documentation AI' },
  { company: 'Minimax GmbH', industry: 'BMA', status: 'new', priority: 'high', potential_revenue: 88000, pain_points: 'Fire protection AI' },
  { company: 'Tyco Fire Protection', industry: 'BMA', status: 'new', priority: 'medium', potential_revenue: 72000, pain_points: 'Monitoring AI' },
  { company: 'Securiton GmbH', industry: 'BMA', status: 'new', priority: 'medium', potential_revenue: 58000, pain_points: 'Alarm AI' },

  // E-Commerce
  { company: 'Otto Group', industry: 'E-Commerce', status: 'new', priority: 'high', potential_revenue: 145000, pain_points: 'Customer AI' },
  { company: 'Zalando SE', industry: 'E-Commerce', status: 'new', priority: 'high', potential_revenue: 165000, pain_points: 'Fashion AI' },
  { company: 'About You', industry: 'E-Commerce', status: 'new', priority: 'medium', potential_revenue: 68000, pain_points: 'Recommendation AI' },
  { company: 'MediaMarktSaturn', industry: 'Retail', status: 'new', priority: 'high', potential_revenue: 125000, pain_points: 'Retail AI' },
  { company: 'Douglas', industry: 'Beauty', status: 'new', priority: 'medium', potential_revenue: 55000, pain_points: 'Beauty advisor AI' },

  // Logistik
  { company: 'DHL Express', industry: 'Logistik', status: 'qualified', priority: 'high', potential_revenue: 180000, pain_points: 'Route optimization AI' },
  { company: 'Kühne+Nagel', industry: 'Logistik', status: 'new', priority: 'high', potential_revenue: 135000, pain_points: 'Supply chain AI' },
  { company: 'DB Schenker', industry: 'Logistik', status: 'new', priority: 'high', potential_revenue: 155000, pain_points: 'Logistics AI' },
  { company: 'Hellmann Worldwide', industry: 'Logistik', status: 'new', priority: 'medium', potential_revenue: 75000, pain_points: 'Tracking AI' },
  { company: 'Rhenus Logistics', industry: 'Logistik', status: 'new', priority: 'medium', potential_revenue: 68000, pain_points: 'Warehouse AI' },

  // Energie
  { company: 'E.ON SE', industry: 'Energie', status: 'new', priority: 'high', potential_revenue: 195000, pain_points: 'Grid AI' },
  { company: 'RWE AG', industry: 'Energie', status: 'new', priority: 'high', potential_revenue: 175000, pain_points: 'Energy prediction' },
  { company: 'EnBW', industry: 'Energie', status: 'new', priority: 'high', potential_revenue: 145000, pain_points: 'Smart meter AI' },
  { company: 'Vattenfall', industry: 'Energie', status: 'new', priority: 'medium', potential_revenue: 88000, pain_points: 'Renewable AI' },
  { company: 'Ørsted Deutschland', industry: 'Energie', status: 'new', priority: 'medium', potential_revenue: 72000, pain_points: 'Wind farm AI' },

  // Gesundheit
  { company: 'Fresenius SE', industry: 'Healthcare', status: 'new', priority: 'high', potential_revenue: 185000, pain_points: 'Medical AI' },
  { company: 'Helios Kliniken', industry: 'Healthcare', status: 'new', priority: 'high', potential_revenue: 165000, pain_points: 'Hospital AI' },
  { company: 'Asklepios Kliniken', industry: 'Healthcare', status: 'new', priority: 'high', potential_revenue: 155000, pain_points: 'Patient AI' },
  { company: 'Charité Berlin', industry: 'Healthcare', status: 'new', priority: 'high', potential_revenue: 125000, pain_points: 'Research AI' },
  { company: 'Schön Kliniken', industry: 'Healthcare', status: 'new', priority: 'medium', potential_revenue: 78000, pain_points: 'Therapy AI' },

  // Versicherungen
  { company: 'Munich Re', industry: 'Versicherung', status: 'new', priority: 'high', potential_revenue: 210000, pain_points: 'Risk AI' },
  { company: 'Hannover Rück', industry: 'Versicherung', status: 'new', priority: 'high', potential_revenue: 175000, pain_points: 'Underwriting AI' },
  { company: 'ERGO Group', industry: 'Versicherung', status: 'new', priority: 'high', potential_revenue: 145000, pain_points: 'Claims AI' },
  { company: 'R+V Versicherung', industry: 'Versicherung', status: 'new', priority: 'medium', potential_revenue: 85000, pain_points: 'Customer service AI' },
  { company: 'HUK-Coburg', industry: 'Versicherung', status: 'new', priority: 'medium', potential_revenue: 78000, pain_points: 'Pricing AI' },

  // Immobilien
  { company: 'Vonovia SE', industry: 'Immobilien', status: 'new', priority: 'high', potential_revenue: 155000, pain_points: 'Property AI' },
  { company: 'Deutsche Wohnen', industry: 'Immobilien', status: 'new', priority: 'medium', potential_revenue: 95000, pain_points: 'Tenant AI' },
  { company: 'LEG Immobilien', industry: 'Immobilien', status: 'new', priority: 'medium', potential_revenue: 72000, pain_points: 'Maintenance AI' },
  { company: 'TAG Immobilien', industry: 'Immobilien', status: 'new', priority: 'medium', potential_revenue: 58000, pain_points: 'Valuation AI' },
  { company: 'Grand City Properties', industry: 'Immobilien', status: 'new', priority: 'medium', potential_revenue: 52000, pain_points: 'Portfolio AI' },

  // Bauwesen
  { company: 'Hochtief AG', industry: 'Bau', status: 'new', priority: 'high', potential_revenue: 175000, pain_points: 'Construction AI' },
  { company: 'Strabag SE', industry: 'Bau', status: 'new', priority: 'high', potential_revenue: 145000, pain_points: 'Project AI' },
  { company: 'Goldbeck', industry: 'Bau', status: 'new', priority: 'medium', potential_revenue: 88000, pain_points: 'BIM AI' },
  { company: 'Züblin', industry: 'Bau', status: 'new', priority: 'medium', potential_revenue: 72000, pain_points: 'Site AI' },
  { company: 'Max Bögl', industry: 'Bau', status: 'new', priority: 'medium', potential_revenue: 65000, pain_points: 'Prefab AI' },

  // Chemie/Pharma
  { company: 'Merck KGaA', industry: 'Pharma', status: 'new', priority: 'high', potential_revenue: 195000, pain_points: 'Drug discovery AI' },
  { company: 'Boehringer Ingelheim', industry: 'Pharma', status: 'new', priority: 'high', potential_revenue: 185000, pain_points: 'Research AI' },
  { company: 'Evonik', industry: 'Chemie', status: 'new', priority: 'high', potential_revenue: 145000, pain_points: 'Process AI' },
  { company: 'Lanxess', industry: 'Chemie', status: 'new', priority: 'medium', potential_revenue: 85000, pain_points: 'Quality AI' },
  { company: 'Wacker Chemie', industry: 'Chemie', status: 'new', priority: 'medium', potential_revenue: 78000, pain_points: 'Production AI' },

  // Medien
  { company: 'Axel Springer', industry: 'Medien', status: 'qualified', priority: 'high', potential_revenue: 125000, pain_points: 'Content AI' },
  { company: 'Bertelsmann', industry: 'Medien', status: 'new', priority: 'high', potential_revenue: 165000, pain_points: 'Media AI' },
  { company: 'ProSiebenSat.1', industry: 'Medien', status: 'new', priority: 'high', potential_revenue: 135000, pain_points: 'Advertising AI' },
  { company: 'RTL Group', industry: 'Medien', status: 'new', priority: 'medium', potential_revenue: 95000, pain_points: 'Streaming AI' },
  { company: 'Burda Media', industry: 'Medien', status: 'new', priority: 'medium', potential_revenue: 72000, pain_points: 'Publishing AI' },

  // Food & Beverage
  { company: 'Nestlé Deutschland', industry: 'Food', status: 'new', priority: 'high', potential_revenue: 145000, pain_points: 'Supply chain AI' },
  { company: 'Dr. Oetker', industry: 'Food', status: 'new', priority: 'medium', potential_revenue: 75000, pain_points: 'Recipe AI' },
  { company: 'Schwarz Gruppe', industry: 'Retail', status: 'new', priority: 'high', potential_revenue: 195000, pain_points: 'Retail AI' },
  { company: 'Aldi Süd', industry: 'Retail', status: 'new', priority: 'high', potential_revenue: 165000, pain_points: 'Logistics AI' },
  { company: 'REWE Group', industry: 'Retail', status: 'new', priority: 'high', potential_revenue: 175000, pain_points: 'Customer AI' },

  // Tech/Software
  { company: 'TeamViewer', industry: 'Software', status: 'qualified', priority: 'high', potential_revenue: 95000, pain_points: 'Remote AI' },
  { company: 'Software AG', industry: 'Software', status: 'new', priority: 'high', potential_revenue: 115000, pain_points: 'Integration AI' },
  { company: 'Celonis', industry: 'Software', status: 'qualified', priority: 'high', potential_revenue: 85000, pain_points: 'Process mining AI' },
  { company: 'Personio', industry: 'HR Tech', status: 'new', priority: 'medium', potential_revenue: 55000, pain_points: 'HR AI' },
  { company: 'Contentful', industry: 'CMS', status: 'new', priority: 'medium', potential_revenue: 48000, pain_points: 'Content AI' },

  // Weitere
  { company: 'Lufthansa Group', industry: 'Aviation', status: 'new', priority: 'high', potential_revenue: 225000, pain_points: 'Operations AI' },
  { company: 'TUI Group', industry: 'Tourism', status: 'new', priority: 'high', potential_revenue: 145000, pain_points: 'Booking AI' },
  { company: 'Fraport', industry: 'Aviation', status: 'new', priority: 'high', potential_revenue: 125000, pain_points: 'Airport AI' },
  { company: 'Deutsche Bahn', industry: 'Transport', status: 'new', priority: 'high', potential_revenue: 185000, pain_points: 'Scheduling AI' },
  { company: 'Flixbus', industry: 'Transport', status: 'new', priority: 'medium', potential_revenue: 65000, pain_points: 'Route AI' },
];

// 50 Partners
const partners = [
  // System Integratoren
  { name: 'Accenture', type: 'System Integrator', status: 'prospect', potential_value: 500000 },
  { name: 'Capgemini', type: 'System Integrator', status: 'prospect', potential_value: 450000 },
  { name: 'IBM Consulting', type: 'System Integrator', status: 'prospect', potential_value: 400000 },
  { name: 'Deloitte Digital', type: 'System Integrator', status: 'prospect', potential_value: 380000 },
  { name: 'PwC Digital', type: 'System Integrator', status: 'prospect', potential_value: 350000 },
  { name: 'KPMG Digital', type: 'System Integrator', status: 'prospect', potential_value: 320000 },
  { name: 'EY Digital', type: 'System Integrator', status: 'prospect', potential_value: 300000 },
  { name: 'McKinsey Digital', type: 'System Integrator', status: 'prospect', potential_value: 280000 },
  { name: 'BCG Digital', type: 'System Integrator', status: 'prospect', potential_value: 260000 },
  { name: 'Bain Digital', type: 'System Integrator', status: 'prospect', potential_value: 240000 },

  // Cloud Provider
  { name: 'AWS Partner', type: 'Cloud', status: 'prospect', potential_value: 350000 },
  { name: 'Azure Partner', type: 'Cloud', status: 'prospect', potential_value: 320000 },
  { name: 'Google Cloud Partner', type: 'Cloud', status: 'prospect', potential_value: 280000 },
  { name: 'Snowflake', type: 'Cloud', status: 'prospect', potential_value: 150000 },
  { name: 'Databricks', type: 'Cloud', status: 'prospect', potential_value: 180000 },

  // AI Platforms
  { name: 'OpenAI', type: 'AI Platform', status: 'prospect', potential_value: 250000 },
  { name: 'Anthropic', type: 'AI Platform', status: 'active', potential_value: 300000 },
  { name: 'Hugging Face', type: 'AI Platform', status: 'prospect', potential_value: 120000 },
  { name: 'Cohere', type: 'AI Platform', status: 'prospect', potential_value: 100000 },
  { name: 'Together AI', type: 'AI Platform', status: 'prospect', potential_value: 80000 },

  // BMA Partner (Maurice's Network!)
  { name: 'Siemens Partner Program', type: 'BMA', status: 'prospect', potential_value: 200000 },
  { name: 'Bosch SI Partner', type: 'BMA', status: 'prospect', potential_value: 180000 },
  { name: 'Honeywell Partner', type: 'BMA', status: 'prospect', potential_value: 150000 },
  { name: 'Hekatron Partner', type: 'BMA', status: 'prospect', potential_value: 100000 },
  { name: 'VdS Certified', type: 'BMA', status: 'active', potential_value: 50000 },

  // Tech Partner
  { name: 'GitHub', type: 'Tech', status: 'active', potential_value: 80000 },
  { name: 'GitLab', type: 'Tech', status: 'prospect', potential_value: 60000 },
  { name: 'Atlassian', type: 'Tech', status: 'prospect', potential_value: 70000 },
  { name: 'Slack', type: 'Tech', status: 'prospect', potential_value: 50000 },
  { name: 'Notion', type: 'Tech', status: 'prospect', potential_value: 40000 },

  // Automation
  { name: 'n8n', type: 'Automation', status: 'active', potential_value: 60000 },
  { name: 'Zapier', type: 'Automation', status: 'prospect', potential_value: 80000 },
  { name: 'Make', type: 'Automation', status: 'prospect', potential_value: 50000 },
  { name: 'Activepieces', type: 'Automation', status: 'prospect', potential_value: 30000 },
  { name: 'Pipedream', type: 'Automation', status: 'prospect', potential_value: 25000 },

  // Reseller
  { name: 'Computacenter', type: 'Reseller', status: 'prospect', potential_value: 200000 },
  { name: 'Bechtle', type: 'Reseller', status: 'prospect', potential_value: 180000 },
  { name: 'Cancom', type: 'Reseller', status: 'prospect', potential_value: 150000 },
  { name: 'SoftwareONE', type: 'Reseller', status: 'prospect', potential_value: 120000 },
  { name: 'Allgeier', type: 'Reseller', status: 'prospect', potential_value: 100000 },

  // Training
  { name: 'DataCamp', type: 'Training', status: 'prospect', potential_value: 40000 },
  { name: 'Coursera', type: 'Training', status: 'prospect', potential_value: 50000 },
  { name: 'Udemy Business', type: 'Training', status: 'prospect', potential_value: 30000 },
  { name: 'LinkedIn Learning', type: 'Training', status: 'prospect', potential_value: 35000 },
  { name: 'Pluralsight', type: 'Training', status: 'prospect', potential_value: 25000 },

  // Investor
  { name: 'High-Tech Gründerfonds', type: 'Investor', status: 'prospect', potential_value: 500000 },
  { name: 'Earlybird VC', type: 'Investor', status: 'prospect', potential_value: 400000 },
  { name: 'HV Capital', type: 'Investor', status: 'prospect', potential_value: 350000 },
  { name: 'Lakestar', type: 'Investor', status: 'prospect', potential_value: 300000 },
  { name: 'Point Nine', type: 'Investor', status: 'prospect', potential_value: 250000 },
];

// Gold Nuggets
const nuggets = [
  { title: '16 RAG Types', content: 'Standard, Agentic, Graph, Modular, Memory-Augmented, Multi-Modal, Federated, Streaming, ODQA, Contextual, Knowledge-Enhanced, Domain-Specific, Hybrid, Self-RAG, HyDE, Recursive', category: 'AI Architecture', monetization_potential: 'RAG Consulting Service €50k+', source: 'X/Twitter' },
  { title: 'YieldClaw x402', content: 'Autonomous DeFi yield agent with HTTP 402 micropayments', category: 'DeFi', monetization_potential: 'Passive DeFi income', source: 'GitHub' },
  { title: 'ClawdBot Architecture', content: '2 local GLM agents + 2 cloud agents = $300k ARR', category: 'Business Model', monetization_potential: 'ClawHub Skills €100k+/year', source: 'Alex Finn' },
  { title: 'Kimi vs OpenAI Costs', content: 'Kimi 1/20 cost of OpenAI for same quality', category: 'Cost Optimization', monetization_potential: 'Cost savings €50k+/year', source: 'Research' },
  { title: 'BMA + AI', content: '16 Jahre Expertise + AI = unschlagbare Kombination', category: 'Domain Expertise', monetization_potential: 'BMA AI Suite €500k+', source: 'Maurice' },
];

// Insert data
const insertLead = db.prepare('INSERT INTO leads (company, industry, contact_name, email, status, priority, potential_revenue, pain_points, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)');
const insertPartner = db.prepare('INSERT INTO partners (name, type, status, potential_value) VALUES (?, ?, ?, ?)');
const insertNugget = db.prepare('INSERT INTO gold_nuggets (title, content, category, monetization_potential, source) VALUES (?, ?, ?, ?, ?)');

console.log('Importing 100 leads...');
leads.forEach(l => insertLead.run(l.company, l.industry, l.contact_name || null, l.email || null, l.status, l.priority, l.potential_revenue, l.pain_points, 'AI Agent Swarm'));

console.log('Importing 50 partners...');
partners.forEach(p => insertPartner.run(p.name, p.type, p.status, p.potential_value));

console.log('Importing Gold Nuggets...');
nuggets.forEach(n => insertNugget.run(n.title, n.content, n.category, n.monetization_potential, n.source));

console.log('✅ Import complete!');
console.log(`   - ${leads.length} Leads`);
console.log(`   - ${partners.length} Partners`);
console.log(`   - ${nuggets.length} Gold Nuggets`);

db.close();
