-- Pulse Pro merge — extra columns on the daily vehicle movement table.
-- Run once in Supabase → SQL Editor. Safe to re-run.
--
-- vehicle        : now holds the REGISTRATION from Pulse (e.g. DL1LAH-3132) when the
--                  tracker matched a Pulse schedule row; the OneLap tracker name moves
--                  to device_name so the join stays traceable.
-- planned_route  : the planned stop sequence from the Pulse "Device Tracking Schedule".
-- plan_status    : per-leg comparison of actual vs planned ("On plan (stop 2 of 3)",
--                  "Unplanned stop", "Depot", "… · missed: <outlets>").
-- recorded_by    : the Pulse auditor who filed that day's schedule.

alter table public.vehicle_movement add column if not exists device_name   text;
alter table public.vehicle_movement add column if not exists planned_route text;
alter table public.vehicle_movement add column if not exists plan_status   text;
alter table public.vehicle_movement add column if not exists recorded_by   text;

create index if not exists vehicle_movement_run_date_idx on public.vehicle_movement (run_date);
