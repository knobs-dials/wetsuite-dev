--
-- PostgreSQL database dump
--

-- Dumped from database version 10.22 (Ubuntu 10.22-0ubuntu0.18.04.1)
-- Dumped by pg_dump version 12.12 (Ubuntu 12.12-0ubuntu0.20.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pgpool_catalog; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA pgpool_catalog;


ALTER SCHEMA pgpool_catalog OWNER TO postgres;

--
-- Name: plpgsql_call_handler(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.plpgsql_call_handler() RETURNS language_handler
    LANGUAGE c
    AS '$libdir/plpgsql', 'plpgsql_call_handler';


ALTER FUNCTION public.plpgsql_call_handler() OWNER TO postgres;

SET default_tablespace = '';

--
-- Name: dist_def; Type: TABLE; Schema: pgpool_catalog; Owner: postgres
--

CREATE TABLE pgpool_catalog.dist_def (
    dbname text NOT NULL,
    schema_name text NOT NULL,
    table_name text NOT NULL,
    col_name text NOT NULL,
    col_list text[] NOT NULL,
    type_list text[] NOT NULL,
    dist_def_func text NOT NULL,
    CONSTRAINT dist_def_check CHECK ((col_name = ANY (col_list)))
);


ALTER TABLE pgpool_catalog.dist_def OWNER TO postgres;

--
-- Name: query_cache; Type: TABLE; Schema: pgpool_catalog; Owner: postgres
--

CREATE TABLE pgpool_catalog.query_cache (
    hash text NOT NULL,
    query text,
    value bytea,
    dbname text NOT NULL,
    create_time timestamp with time zone
);


ALTER TABLE pgpool_catalog.query_cache OWNER TO postgres;

--
-- Name: replicate_def; Type: TABLE; Schema: pgpool_catalog; Owner: postgres
--

CREATE TABLE pgpool_catalog.replicate_def (
    dbname text NOT NULL,
    schema_name text NOT NULL,
    table_name text NOT NULL,
    col_list text[] NOT NULL,
    type_list text[] NOT NULL
);


ALTER TABLE pgpool_catalog.replicate_def OWNER TO postgres;

--
-- Name: bwb; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bwb (
    bwbr text NOT NULL,
    toestand_url text NOT NULL,
    wti_url text,
    manifest_url text,
    geldig_begin text,
    geldig_eind text,
    meta jsonb,
    plaintext text,
    intitule text,
    toestand_bytesize integer,
    soort text,
    citeertitel text,
    version_dates text[]
);


ALTER TABLE public.bwb OWNER TO postgres;

--
-- Name: fetched; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fetched (
    url text NOT NULL,
    data bytea NOT NULL,
    content_type text,
    content_length integer
);


ALTER TABLE public.fetched OWNER TO postgres;

--
-- Name: dist_def dist_def_pkey; Type: CONSTRAINT; Schema: pgpool_catalog; Owner: postgres
--

ALTER TABLE ONLY pgpool_catalog.dist_def
    ADD CONSTRAINT dist_def_pkey PRIMARY KEY (dbname, schema_name, table_name);


--
-- Name: query_cache query_cache_pkey; Type: CONSTRAINT; Schema: pgpool_catalog; Owner: postgres
--

ALTER TABLE ONLY pgpool_catalog.query_cache
    ADD CONSTRAINT query_cache_pkey PRIMARY KEY (hash, dbname);


--
-- Name: replicate_def replicate_def_pkey; Type: CONSTRAINT; Schema: pgpool_catalog; Owner: postgres
--

ALTER TABLE ONLY pgpool_catalog.replicate_def
    ADD CONSTRAINT replicate_def_pkey PRIMARY KEY (dbname, schema_name, table_name);


--
-- Name: fetched fetched_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fetched
    ADD CONSTRAINT fetched_pkey PRIMARY KEY (url);


--
-- Name: bwb pk_bwbr; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bwb
    ADD CONSTRAINT pk_bwbr PRIMARY KEY (bwbr);


--
-- PostgreSQL database dump complete
--

