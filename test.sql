USE scoring;
DELETE FROM team;
DELETE FROM service;
DELETE FROM service_check;
DELETE FROM check_input;
INSERT INTO team (name, subnet) VALUES ('Team1', '8.8.8.0');
INSERT INTO team (name, subnet) VALUES ('Team2', '192.168.2.5');
INSERT INTO service (host, port) VALUES (8, 53);
INSERT INTO service_check (name, check_function, poller, service_id) VALUES ('DNS', 'checker.dns_check.any_match', 'polling.dns_poll.DnsPoller', 1);
INSERT INTO check_input (input, expected, check_id) VALUES ('ccopy_reg\n_reconstructor\np0\n(cpolling.dns_poll\nDnsPollInput\np1\nc__builtin__\nobject\np2\nNtp3\nRp4\n(dp5\nS\'record_type\'\np6\nS\'A\'\np7\nsS\'query\'\np8\nS\'petpawzclinic.com\'\np9\nsS\'port\'\np10\nNsS\'server\'\np11\nNsb.','["198.49.23.145","198.185.159.145","198.185.159.144","198.49.23.144"]',1);

