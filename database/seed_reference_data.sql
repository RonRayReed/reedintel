INSERT INTO sources (source_name, source_type, city, country, manual_url, api_endpoint, auth_required, refresh_frequency)
VALUES
  ('ProZorro',                'procurement',          'Kyiv',      'Ukraine', 'https://prozorro.gov.ua/en',                                              'https://public.api.openprocurement.org/api/2.5/tenders', false, '30 minutes'),
  ('MTender',                 'procurement',          'Chisinau',  'Moldova', 'https://mtender.gov.md/',                                                 '',                                                       false, '60 minutes'),
  ('ANAF',                    'tax',                  'Bucharest', 'Romania', 'https://www.anaf.ro/',                                                    '',                                                       true,  'daily'),
  ('ONRC',                    'registry',             'Bucharest', 'Romania', 'https://www.onrc.ro/index.php/en/',                                       '',                                                       true,  'daily'),
  ('Lviv Open Data',          'municipal-open-data',  'Lviv',      'Ukraine', 'https://opendata.city-adm.lviv.ua/',                                      '',                                                       false, 'daily'),
  ('Odesa Open Data',         'municipal-open-data',  'Odesa',     'Ukraine', 'https://data.gov.ua/organization/odeska-miska-rada',                      '',                                                       false, 'daily'),
  ('Ukrainian Sea Ports Authority', 'port-notices',   'Odesa',     'Ukraine', 'https://www.uspa.gov.ua/en/',                                             '',                                                       false, 'daily'),
  ('Lviv IT Cluster',         'industry-cluster',     'Lviv',      'Ukraine', 'https://itcluster.lviv.ua/en/',                                           '',                                                       false, 'weekly')
ON CONFLICT DO NOTHING;
