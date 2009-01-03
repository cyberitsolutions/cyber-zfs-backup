--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

--
-- Data for Name: companies; Type: TABLE DATA; Schema: public; Owner: pete
--

COPY companies (name, long_name) FROM stdin;
pete_inc	Pete, Inc.
abc	Apple Banana Company
freepers	Free Republic Wingnuts
\.


--
-- Data for Name: shares; Type: TABLE DATA; Schema: public; Owner: pete
--

COPY shares (name, company_name) FROM stdin;
invoices	pete_inc
misc	pete_inc
accounting	abc
porn	freepers
accounting	freepers
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: pete
--

COPY users (username, full_name, company_name, hashed_password) FROM stdin;
pete	Peter Wright	pete_inc	d41d8cd98f00b204e9800998ecf8427e
bob	Bob the Builder	abc	d41d8cd98f00b204e9800998ecf8427e
joe	Joe the Plumber	freepers	d41d8cd98f00b204e9800998ecf8427e
\.


--
-- PostgreSQL database dump complete
--

