-- vehicle_movement — the daily vehicle report table for the Operations dashboard project.
-- Run once in Supabase → SQL Editor. Safe to re-run.
--
-- One row per LEG. The daily job deletes and re-inserts a date's rows on every run,
-- so re-running a day is always idempotent.

create table if not exists public.vehicle_movement (
  id             bigint generated always as identity primary key,
  run_date       date        not null,
  sr_no          integer,

  vehicle        text,          -- registration from Pulse (DL1LAH-8906) when matched,
                                -- otherwise the OneLap tracker name
  device_name    text,          -- the OneLap tracker name, always ("Factory vehicle 2")
  driver         text,          -- the actual driver, if ops fills it in
  attendant      text,

  start_dest     text,
  finish_dest    text,
  dispatch_time  text,

  loc_30   text,  time_30  text,
  loc_60   text,  time_60  text,
  loc_90   text,  time_90  text,
  loc_120  text,  time_120 text,

  outlet_reached text,
  total_travel   text,
  time_at_outlet text,
  remarks        text,

  -- Pulse Pro "Device Tracking Schedule" merge
  planned_route  text,          -- planned stop sequence, " → " separated
  plan_status    text,          -- On plan (stop 2 of 3) / Unplanned stop / Depot / … missed: …
  recorded_by    text,          -- the Pulse auditor who filed the checklist (NOT the driver)

  created_at     timestamptz not null default now()
);

-- Columns added after the first version — no-ops on a fresh create.
alter table public.vehicle_movement add column if not exists device_name   text;
alter table public.vehicle_movement add column if not exists planned_route text;
alter table public.vehicle_movement add column if not exists plan_status   text;
alter table public.vehicle_movement add column if not exists recorded_by   text;

create index if not exists vehicle_movement_run_date_idx on public.vehicle_movement (run_date);
create index if not exists vehicle_movement_date_sr_idx  on public.vehicle_movement (run_date, sr_no);

-- The daily job writes with the SERVICE ROLE key, which bypasses RLS. Enabling RLS with
-- no policy therefore keeps the job working while blocking anonymous reads.
alter table public.vehicle_movement enable row level security;

-- Only if you later want the website to read this table directly with the anon key
-- (the dashboard currently reads public/vehicle-monitoring-data.json instead):
--
--   create policy "vehicle_movement_public_read" on public.vehicle_movement
--     for select using (true);
