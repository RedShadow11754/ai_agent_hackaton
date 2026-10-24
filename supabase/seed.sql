-- AI Suspicious Message Investigation Agent - demo seed data
-- ---------------------------------------------------------------------------
-- Run AFTER schema.sql. Everything here is FICTIONAL (hard rule 7): reserved
-- domains (.test / .example) and 192.0.2.0/24 documentation IPs only. Never
-- seed a real company domain, a real URL, or a real credential.

-- ---------------------------------------------------------------------------
-- Guidance passages (3-6). IDs are cited verbatim by the model: it may only
-- reference IDs that exist here (enforced by validate_assessment).
-- ---------------------------------------------------------------------------
insert into guidance (id, title, body, tags) values
    (
        'SEC-01',
        'Do not click links in unexpected messages',
        'If a message asks you to sign in, pay, or open an attachment and you '
        'were not expecting it, do not click. Open the site by typing the known '
        'address yourself, or verify with the sender through a channel you '
        'already trust.',
        array['links', 'phishing', 'general']
    ),
    (
        'SEC-02',
        'Verify payment and bank-detail changes by phone',
        'Never act on new bank details sent by email or chat. Call the supplier '
        'or colleague on a number you already have on file before any payment '
        'details are changed.',
        array['payment', 'fraud', 'finance']
    ),
    (
        'SEC-03',
        'Report suspected phishing to the service desk',
        'Forward the message as an attachment to the service desk, then delete '
        'it from your mailbox. Do not reply to the sender and do not open '
        'attachments.',
        array['reporting', 'phishing', 'process']
    ),
    (
        'SEC-04',
        'Treat urgency and secrecy as warning signs',
        'Messages that demand immediate action, threaten consequences, or ask '
        'you to keep the request secret are common manipulation tactics. Slow '
        'down and verify before acting.',
        array['social-engineering', 'urgency', 'general']
    ),
    (
        'SEC-05',
        'Multi-factor codes are never shared',
        'No legitimate helpdesk, bank, or supplier will ask you to read out a '
        'one-time code, approve a push prompt, or share a password. Refuse and '
        'report it.',
        array['credentials', 'mfa', 'general']
    )
on conflict (id) do nothing;

-- ---------------------------------------------------------------------------
-- Trusted domains (3). Reserved .example TLD: safe to publish.
-- ---------------------------------------------------------------------------
insert into trusted_domains (domain, label) values
    ('intranet.example',   'Internal intranet portal'),
    ('hr-portal.example',  'Internal HR self-service'),
    ('helpdesk.example',   'Internal IT service desk')
on conflict (domain) do nothing;

-- ---------------------------------------------------------------------------
-- Domain reputation rows (~6). Mix of known_safe, known_suspicious, unknown
-- so the demo can exercise every branch. IP literal uses 192.0.2.45 (TEST-NET-1).
-- ---------------------------------------------------------------------------
insert into domain_reputation (domain, status, source, note) values
    ('intranet.example',    'known_safe',       'manual', 'Internal allow-listed portal.'),
    ('hr-portal.example',   'known_safe',       'manual', 'Internal allow-listed portal.'),
    ('example.test',        'known_safe',       'manual', 'Reserved test domain used in training material.'),
    ('secure-login.test',   'known_suspicious', 'manual', 'Lookalike used in a past phishing simulation.'),
    ('payroll-update.example', 'known_suspicious', 'manual', 'Impersonates the payroll system in simulations.'),
    ('192.0.2.45',          'unknown',          'manual', 'Documentation IP literal (TEST-NET-1); no reputation data.')
on conflict (domain) do nothing;

-- TODO: add 1-2 more suspicious rows once the demo cases are finalised.
