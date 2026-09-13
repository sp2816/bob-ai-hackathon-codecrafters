import {
  CalendarClock,
  CheckCircle2,
  Clock3,
  ClipboardCheck,
  Wrench,
  TriangleAlert,
} from "lucide-react";

interface MaintenanceTask {
  id: string;
  asset: string;
  component: string;
  type: string;
  due: string;
  priority: "Critical" | "High" | "Routine";
  status: "Due now" | "Upcoming" | "Scheduled";
  technician: string;
  recommendation: string;
}

const tasks: MaintenanceTask[] = [
  {
    id: "MT-2041",
    asset: "AS-1032",
    component: "Engine Assembly",
    type: "Inspection",
    due: "Today",
    priority: "Critical",
    status: "Due now",
    technician: "Maintenance Team A",
    recommendation:
      "Inspect engine vibration, temperature, and lubrication before next mission cycle.",
  },
  {
    id: "MT-2038",
    asset: "AS-1088",
    component: "Hydraulic System",
    type: "Preventive Service",
    due: "18 Sep 2026",
    priority: "High",
    status: "Upcoming",
    technician: "Maintenance Team B",
    recommendation:
      "Review hydraulic pressure and fluid condition; replace filter if readings remain elevated.",
  },
  {
    id: "MT-2027",
    asset: "AS-1047",
    component: "Main Bearing",
    type: "Routine Inspection",
    due: "26 Sep 2026",
    priority: "Routine",
    status: "Scheduled",
    technician: "Maintenance Team A",
    recommendation:
      "Continue standard inspection cycle and verify bearing temperature trend.",
  },
];

function priorityText(priority: MaintenanceTask["priority"]) {
  if (priority === "Critical") return "text-[#B95F46]";
  if (priority === "High") return "text-[#9A7650]";
  return "text-[#69784F]";
}

function priorityBg(priority: MaintenanceTask["priority"]) {
  if (priority === "Critical") return "bg-[#F1D9D0]";
  if (priority === "High") return "bg-[#EFE3CE]";
  return "bg-[#E0E7D6]";
}

function Maintenance() {
  const dueNow = tasks.filter((task) => task.status === "Due now").length;
  const upcoming = tasks.filter((task) => task.status === "Upcoming").length;
  const scheduled = tasks.filter((task) => task.status === "Scheduled").length;

  return (
    <div className="space-y-7">
      <section className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="eyebrow">Fleet Maintenance</p>
          <h1 className="mt-2 text-[42px] font-semibold leading-none tracking-[-0.055em] text-[#3B2A20] sm:text-[48px]">
            Maintenance
          </h1>
          <p className="mt-3 max-w-xl text-[13px] leading-6 text-[#806B59]">
            Coordinate inspections, preventive service, and corrective work
            before maintenance events affect mission readiness.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="rounded-full border border-[#D8CBB9] bg-[#EEE5D7] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#806B59]">
            Maintenance Control
          </span>
          <span className="rounded-full border border-[#C2CEAE] bg-[#DDE5D1] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#596842]">
            Operational
          </span>
        </div>
      </section>

      <section className="grid gap-5 md:grid-cols-3">
        <article className="rounded-2xl border border-[#E1B7A9] bg-[#FBF3EF] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">Due Now</p>
              <div className="mt-4 text-[42px] font-light leading-none tracking-[-0.06em] text-[#B95F46]">
                {dueNow}
              </div>
              <p className="mt-3 text-[10px] text-[#A66B5A]">
                Immediate attention required
              </p>
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#F1D9D0]">
              <TriangleAlert className="h-4 w-4 text-[#B95F46]" strokeWidth={1.7} />
            </div>
          </div>
        </article>

        <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">Upcoming</p>
              <div className="mt-4 text-[42px] font-light leading-none tracking-[-0.06em] text-[#9A7650]">
                {upcoming}
              </div>
              <p className="mt-3 text-[10px] text-[#9B8977]">
                Planned maintenance events
              </p>
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#EFE3CE]">
              <CalendarClock className="h-4 w-4 text-[#9A7650]" strokeWidth={1.7} />
            </div>
          </div>
        </article>

        <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">Scheduled</p>
              <div className="mt-4 text-[42px] font-light leading-none tracking-[-0.06em] text-[#69784F]">
                {scheduled}
              </div>
              <p className="mt-3 text-[10px] text-[#9B8977]">
                Within planned service cycle
              </p>
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#E0E7D6]">
              <CheckCircle2 className="h-4 w-4 text-[#69784F]" strokeWidth={1.7} />
            </div>
          </div>
        </article>
      </section>

      <section className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
        <div className="flex items-center justify-between px-6 py-5">
          <div>
            <p className="eyebrow">Maintenance Queue</p>
            <h2 className="mt-2 text-[21px] font-semibold tracking-[-0.025em] text-[#4A3528]">
              Service schedule
            </h2>
            <p className="mt-2 text-[11px] text-[#9B8977]">
              Prioritized maintenance actions across the active fleet.
            </p>
          </div>
          <Wrench className="h-5 w-5 text-[#806B59]" strokeWidth={1.5} />
        </div>

        <div>
          {tasks.map((task) => (
            <article
              key={task.id}
              className="border-t border-[#E8DED1] px-6 py-6"
            >
              <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-3">
                    <ClipboardCheck
                      className={`h-4 w-4 ${priorityText(task.priority)}`}
                      strokeWidth={1.7}
                    />

                    <div>
                      <p className="font-mono text-[12px] font-semibold text-[#4A3528]">
                        {task.id}
                      </p>
                      <p className="mt-1 text-[10px] text-[#9B8977]">
                        {task.asset} · {task.component}
                      </p>
                    </div>

                    <span
                      className={`rounded-full px-3 py-1.5 text-[8px] font-semibold uppercase tracking-[0.12em] ${priorityBg(
                        task.priority,
                      )} ${priorityText(task.priority)}`}
                    >
                      {task.priority}
                    </span>

                    <span className="rounded-full border border-[#D8CBB9] bg-[#F5EEE4] px-3 py-1.5 text-[8px] font-semibold uppercase tracking-[0.12em] text-[#806B59]">
                      {task.status}
                    </span>
                  </div>

                  <div className="mt-5 grid gap-4 sm:grid-cols-3">
                    <div>
                      <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
                        Maintenance type
                      </p>
                      <p className="mt-2 text-[12px] text-[#5D4535]">
                        {task.type}
                      </p>
                    </div>

                    <div>
                      <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
                        Due
                      </p>
                      <div className="mt-2 flex items-center gap-2">
                        <Clock3
                          className="h-4 w-4 text-[#806B59]"
                          strokeWidth={1.5}
                        />
                        <p className="text-[12px] text-[#5D4535]">
                          {task.due}
                        </p>
                      </div>
                    </div>

                    <div>
                      <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
                        Assigned team
                      </p>
                      <p className="mt-2 text-[12px] text-[#5D4535]">
                        {task.technician}
                      </p>
                    </div>
                  </div>

                  <div className="mt-5 rounded-xl border border-[#E4D8C9] bg-[#F5EEE4] px-4 py-3">
                    <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
                      Recommended action
                    </p>
                    <p className="mt-1 text-[11px] leading-5 text-[#5D4535]">
                      {task.recommendation}
                    </p>
                  </div>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-0 overflow-hidden rounded-2xl border border-[#DED2C0] bg-[#EEE5D7] md:grid-cols-2">
        <div className="flex items-center gap-3 px-6 py-5">
          <CheckCircle2
            className="h-5 w-5 text-[#69784F]"
            strokeWidth={1.5}
          />
          <div>
            <p className="text-[13px] font-semibold text-[#4A3528]">
              Maintenance control operational
            </p>
            <p className="mt-1 text-[11px] text-[#9B8977]">
              Active maintenance events are synchronized with fleet status.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 border-t border-[#DED2C0] px-6 py-5 md:border-l md:border-t-0">
          <CalendarClock
            className="h-5 w-5 text-[#69784F]"
            strokeWidth={1.5}
          />
          <div>
            <p className="text-[13px] font-semibold text-[#4A3528]">
              Preventive scheduling active
            </p>
            <p className="mt-1 text-[11px] text-[#9B8977]">
              Planned service is being tracked against operational readiness.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Maintenance;
