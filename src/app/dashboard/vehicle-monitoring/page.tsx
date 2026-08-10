// Vehicle Monitoring Dashboard — self-contained static report served from
// /public/vehicle-monitoring-dashboard.html and shown in an iframe (same
// pattern as the Music Monitor). Built from OneLap GPS vehicle-tracking data:
// each vehicle's route, outlet stops, drive/halt times and a full trip log.
export default function VehicleMonitoringPage() {
  return (
    <iframe
      src="/vehicle-monitoring-dashboard.html"
      title="Vehicle Monitoring Dashboard"
      className="block w-full border-0 bg-white"
      style={{ height: 'calc(100vh - 3.5rem)' }}
    />
  );
}
