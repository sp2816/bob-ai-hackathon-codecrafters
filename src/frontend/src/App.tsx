import { Activity, CheckCircle2, Clock3, ShieldCheck, TriangleAlert, Wrench } from "lucide-react";
import { useEffect, useState } from "react";

import AppShell from "./components/layout/AppShell";
import Assets from "./pages/Assets";
import Predictions from "./pages/Predictions";
import Maintenance from "./pages/Maintenance";
import IBMBob from "./pages/IBMBob";

import {
  dashboardAssets,
  dashboardSummary,
  missionSchedule,
} from "./mocks/dashboardMock";

import type { Asset } from "./types/asset";

function StatusDot({ status }: { status: Asset["status"] }) {
  const statusTone =
    status === "OPERATIONAL"
      ? "bg-[#69784F]"
      : status === "WARNING"
        ? "bg-[#B95F46]"
        : "bg-[#A69A89]";

  return <span className={`h-2 w-2 rounded-full ${statusTone}`} />;
}

function MiniHealthChart() {
  return (
    <svg
      viewBox="0 0 220 70"
      className="h-[68px] w-full"
      preserveAspectRatio="none"
      aria-label="Fleet health trend"
    >
      <defs>
        <linearGradient id="healthFill" x1="0" y1="0" x2="0" y2="1">
          <stop
            offset="0%"
            stopColor="#69784F"
            stopOpacity="0.28"
          />
          <stop
            offset="100%"
            stopColor="#69784F"
            stopOpacity="0"
          />
        </linearGradient>
      </defs>

      <path
        d="M0 53 C18 56, 25 43, 42 46 C58 50, 64 31, 82 36 C97 40, 103 25, 120 31 C137 38, 142 19, 159 25 C177 31, 186 11, 202 17 C209 20, 214 12, 220 9 L220 70 L0 70 Z"
        fill="url(#healthFill)"
      />

      <path
        d="M0 53 C18 56, 25 43, 42 46 C58 50, 64 31, 82 36 C97 40, 103 25, 120 31 C137 38, 142 19, 159 25 C177 31, 186 11, 202 17 C209 20, 214 12, 220 9"
        fill="none"
        stroke="#69784F"
        strokeWidth="3"
        strokeLinecap="round"
      />

      <circle
        cx="220"
        cy="9"
        r="4"
        fill="#69784F"
      />
    </svg>
  );
}

function ReadinessRing() {
  const score = dashboardSummary.missionReadiness;
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - score / 100);

  return (
    <div className="relative flex h-[126px] w-[126px] items-center justify-center">
      <svg
        viewBox="0 0 126 126"
        className="absolute inset-0 h-full w-full -rotate-90"
      >
        <circle
          cx="63"
          cy="63"
          r={radius}
          fill="none"
          stroke="#E1D6C6"
          strokeWidth="9"
        />

        <circle
          cx="63"
          cy="63"
          r={radius}
          fill="none"
          stroke="#69784F"
          strokeWidth="9"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>

      <div className="relative text-center">
        <div className="text-[29px] font-light leading-none tracking-[-0.05em] text-[#3B2A20]">
          {score}%
        </div>

        <div className="mt-1 text-[7px] font-semibold uppercase tracking-[0.15em] text-[#9B8977]">
          Ready
        </div>
      </div>
    </div>
  );
}

function MissionReadinessChart() {
  return (
    <div className="mt-8">
      <div className="relative h-[310px]">

        <div className="absolute inset-x-0 top-0 flex justify-between border-t border-[#E6DCCE] pt-2">
          <span className="text-[10px] text-[#806B59]">
            100%
          </span>
        </div>

        <div className="absolute inset-x-0 top-1/4 border-t border-[#E9E0D4]" />
        <div className="absolute inset-x-0 top-1/2 border-t border-[#E9E0D4]" />
        <div className="absolute inset-x-0 top-3/4 border-t border-[#E9E0D4]" />

        <div className="absolute inset-x-0 bottom-0 flex justify-between border-b border-[#D9CDBD] pb-2">
          <span className="text-[10px] font-medium text-[#4A3528]">
            0%
          </span>
        </div>

        <svg
          viewBox="0 0 1000 300"
          preserveAspectRatio="none"
          className="absolute inset-0 h-full w-full"
        >
          <defs>
            <linearGradient
              id="riskArea"
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop
                offset="0%"
                stopColor="#B95F46"
                stopOpacity="0.7"
              />
              <stop
                offset="100%"
                stopColor="#D9967F"
                stopOpacity="0.2"
              />
            </linearGradient>

            <linearGradient
              id="sandArea"
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop
                offset="0%"
                stopColor="#D6B787"
                stopOpacity="0.7"
              />
              <stop
                offset="100%"
                stopColor="#E6D1AE"
                stopOpacity="0.18"
              />
            </linearGradient>

            <linearGradient
              id="mossArea"
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop
                offset="0%"
                stopColor="#69784F"
                stopOpacity="0.72"
              />
              <stop
                offset="100%"
                stopColor="#AAB98A"
                stopOpacity="0.18"
              />
            </linearGradient>
          </defs>

          <path
            d="M0 250
              C35 245 65 247 90 235
              C125 220 150 228 180 216
              C215 203 240 214 270 197
              C305 180 335 191 365 174
              C400 155 430 170 460 153
              C500 133 525 148 555 131
              C590 111 620 127 650 108
              C685 89 715 108 745 91
              C780 70 810 84 840 65
              C875 45 905 57 935 40
              C960 29 980 31 1000 22
              L1000 300 L0 300 Z"
            fill="url(#riskArea)"
          />

          <path
            d="M0 210
              C35 202 65 205 90 193
              C125 177 150 184 180 170
              C215 155 240 165 270 151
              C305 134 335 145 365 128
              C400 110 430 125 460 108
              C500 89 525 104 555 89
              C590 72 620 87 650 70
              C685 52 715 70 745 53
              C780 35 810 48 840 32
              C875 18 905 29 935 17
              C960 10 980 12 1000 7
              L1000 22
              C980 31 960 29 935 40
              C905 57 875 45 840 65
              C810 84 780 70 745 91
              C715 108 685 89 650 108
              C620 127 590 111 555 131
              C525 148 500 133 460 153
              C430 170 400 155 365 174
              C335 191 305 180 270 197
              C240 214 215 203 180 216
              C150 228 125 220 90 235
              C65 247 35 245 0 250 Z"
            fill="url(#sandArea)"
          />

          <path
            d="M0 155
              C35 147 65 151 90 138
              C125 121 150 130 180 115
              C215 97 240 108 270 94
              C305 77 335 88 365 72
              C400 54 430 69 460 52
              C500 34 525 49 555 35
              C590 19 620 34 650 20
              C685 5 715 18 745 8
              C780 0 810 5 840 0
              C875 0 905 0 935 0
              C960 0 980 0 1000 0
              L1000 7
              C980 12 960 10 935 17
              C905 29 875 18 840 32
              C810 48 780 35 745 53
              C715 70 685 52 650 70
              C620 87 590 72 555 89
              C525 104 500 89 460 108
              C430 125 400 110 365 128
              C335 145 305 134 270 151
              C240 165 215 155 180 170
              C150 184 125 177 90 193
              C65 205 35 202 0 210 Z"
            fill="url(#mossArea)"
          />
        </svg>

        <div className="absolute bottom-[-28px] left-0 right-0 flex justify-between">
          {[
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
          ].map((month) => (
            <span
              key={month}
              className="text-[10px] font-medium text-[#4A3528]"
            >
              {month}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-12 flex flex-wrap items-center justify-center gap-6">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-[#69784F]" />
          <span className="text-[10px] text-[#725B49]">
            Operational
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-[#D6B787]" />
          <span className="text-[10px] text-[#725B49]">
            Degraded
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-[#B95F46]" />
          <span className="text-[10px] text-[#725B49]">
            At Risk
          </span>
        </div>
      </div>
    </div>
  );
}

function Dashboard() {
  const operationalMetrics = [
    {
      label: "Progress",
      value: dashboardSummary.operationalProgress,
      tone: "terracotta",
    },
    {
      label: "Breakdown",
      value: dashboardSummary.breakdown,
      tone: "moss",
    },
    {
      label: "Active Alert",
      value: dashboardSummary.activeAlerts,
      tone: "terracotta",
    },
    {
      label: "Maintenance",
      value: dashboardSummary.maintenance,
      tone: "moss",
    },
    {
      label: "Online Assets",
      value: dashboardSummary.onlineAssets,
      tone: "moss",
    },
  ];

  return (
    <>
      <div className="space-y-7">

        <section className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
          <div>
            <p className="eyebrow">
              Mission Control
            </p>

            <h1 className="mt-2 text-[42px] font-semibold leading-none tracking-[-0.055em] text-[#3B2A20] sm:text-[48px]">
              Dashboard
            </h1>

            <p className="mt-3 max-w-xl text-[13px] leading-6 text-[#806B59]">
              Fleet health, mission readiness, predictive risk, and
              maintenance intelligence in one operational view.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="rounded-full border border-[#D8CBB9] bg-[#EEE5D7] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#806B59]">
              Patrol Mission
            </span>

            <span className="rounded-full border border-[#C2CEAE] bg-[#DDE5D1] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#596842]">
              Live
            </span>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-3">

          <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
            <div className="flex items-start justify-between">
              <div>
                <p className="eyebrow">
                  Fleet Health
                </p>

                <h2 className="mt-4 text-[15px] font-semibold text-[#4A3528]">
                  Overall asset health
                </h2>
              </div>

              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#E0E7D6]">
                <Activity
                  className="h-4 w-4 text-[#69784F]"
                  strokeWidth={1.7}
                />
              </div>
            </div>

            <div className="mt-5 flex items-end justify-between gap-4">
              <div>
                <div className="text-[44px] font-light leading-none tracking-[-0.06em] text-[#3B2A20]">
                  {dashboardSummary.fleetHealth}%
                </div>

                <div className="mt-3 flex items-center gap-2">
                  <span className="moss-dot" />
                  <span className="text-[10px] text-[#69784F]">
                    +1.2% from last week
                  </span>
                </div>
              </div>

              <div className="w-[48%]">
                <MiniHealthChart />
              </div>
            </div>
          </article>

          <article className="rounded-2xl border-2 border-[#C96D52] bg-[#FBF4EE] p-6 shadow-[0_8px_30px_rgba(155,75,50,0.05)]">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#A85B45]">
                  Active Alerts
                </p>

                <h2 className="mt-4 text-[15px] font-semibold text-[#4A3528]">
                  Fleet attention
                </h2>
              </div>

              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#F0D8CF]">
                <TriangleAlert
                  className="h-4 w-4 text-[#B95F46]"
                  strokeWidth={1.7}
                />
              </div>
            </div>

            <div className="mt-5">
              <div className="text-[44px] font-light leading-none tracking-[-0.06em] text-[#B95F46]">
                {dashboardSummary.activeAlerts}{" "}
                <span className="text-[30px] font-normal">
                  ({dashboardSummary.activeAlertLevel})
                </span>
              </div>

              <div className="mt-4 flex items-center gap-2">
                <span className="terracotta-dot" />

                <span className="text-[10px] text-[#A85B45]">
                  No critical alerts
                </span>
              </div>
            </div>
          </article>

          <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
            <div className="flex items-start justify-between">
              <div>
                <p className="eyebrow">
                  Mission Readiness
                </p>

                <h2 className="mt-4 text-[15px] font-semibold text-[#4A3528]">
                  Patrol assessment
                </h2>
              </div>

              <ShieldCheck
                className="h-5 w-5 text-[#69784F]"
                strokeWidth={1.6}
              />
            </div>

            <div className="mt-2 flex items-center justify-between">
              <div>
                <div className="text-[44px] font-light leading-none tracking-[-0.06em] text-[#3B2A20]">
                  {dashboardSummary.missionReadiness}%
                </div>

                <div className="mt-3 flex items-center gap-2">
                  <span className="moss-dot" />

                  <span className="text-[10px] text-[#69784F]">
                    +3% from last week
                  </span>
                </div>
              </div>

              <ReadinessRing />
            </div>
          </article>
        </section>

        <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_330px]">

          <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)] sm:p-7 lg:p-8">
            <div>
              <p className="eyebrow">
                Readiness Analytics
              </p>

              <h2 className="mt-2 text-[21px] font-semibold tracking-[-0.025em] text-[#4A3528]">
                Mission Readiness over time
              </h2>

              <p className="mt-2 text-[11px] text-[#9B8977]">
                Operational readiness trend across the mission cycle.
              </p>
            </div>

            <MissionReadinessChart />
          </article>

          <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
            <div className="flex items-start justify-between">
              <div>
                <p className="eyebrow">
                  Operations
                </p>

                <h2 className="mt-2 text-[21px] font-semibold tracking-[-0.025em] text-[#4A3528]">
                  Operational Status
                </h2>
              </div>

              <CheckCircle2
                className="h-4 w-4 text-[#69784F]"
                strokeWidth={1.7}
              />
            </div>

            <div className="mt-6">
              {operationalMetrics.map((metric, index) => (
                <div
                  key={metric.label}
                  className={`py-4 ${
                    index !== 0
                      ? "border-t border-[#E8DED1]"
                      : ""
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[12px] font-medium text-[#5D4535]">
                      {metric.label}
                    </span>

                    <span className="text-[13px] font-semibold text-[#4A3528]">
                      {metric.value}%
                    </span>
                  </div>

                  <div className="mt-3 soft-progress">
                    <div
                      className={
                        metric.tone === "terracotta"
                          ? "terracotta-progress"
                          : "moss-progress"
                      }
                      style={{
                        width: `${Math.max(metric.value, 5)}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">

          <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
            <div className="flex items-center justify-between px-6 py-5">
              <div>
                <p className="eyebrow">
                  Fleet
                </p>

                <h2 className="mt-2 text-[17px] font-semibold text-[#4A3528]">
                  Asset health
                </h2>
              </div>

              <Activity
                className="h-5 w-5 text-[#806B59]"
                strokeWidth={1.5}
              />
            </div>

            <div>
              {dashboardAssets.map((asset) => {
                const displayHealth =
                  asset.asset_id === "AS-1047"
                    ? 98
                    : asset.asset_id === "AS-1032"
                      ? 81
                      : 88;

                const displayStatus =
                  asset.status === "OPERATIONAL"
                    ? asset.asset_id === "AS-1032"
                      ? "Warning"
                      : asset.asset_id === "AS-1088"
                        ? "Standby"
                        : "Healthy"
                    : asset.status;

                return (
                  <div
                    key={asset.asset_id}
                    className="border-t border-[#E8DED1] px-6 py-5"
                  >
                    <div className="flex items-start justify-between gap-5">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <StatusDot
                            status={
                              displayStatus === "Warning"
                                ? "WARNING"
                                : displayStatus === "Standby"
                                  ? "STANDBY"
                                  : "OPERATIONAL"
                            }
                          />

                          <span className="font-mono text-[11px] font-semibold text-[#4A3528]">
                            {asset.asset_id}
                          </span>

                          <span className="hidden text-[10px] text-[#9B8977] sm:inline">
                            {asset.name}
                          </span>
                        </div>

                        <p className="mt-2 text-[10px] text-[#806B59]">
                          {asset.component_name ??
                            "Component monitoring"}
                        </p>
                      </div>

                      <div className="text-right">
                        <span className="text-[20px] font-light tracking-[-0.04em] text-[#3B2A20]">
                          {displayHealth}%
                        </span>

                        <p
                          className={`mt-1 text-[8px] font-semibold uppercase tracking-[0.1em] ${
                            displayStatus === "Healthy"
                              ? "text-[#69784F]"
                              : displayStatus === "Warning"
                                ? "text-[#B95F46]"
                                : "text-[#A69A89]"
                          }`}
                        >
                          {displayStatus}
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 soft-progress">
                      <div
                        className={
                          displayStatus === "Warning"
                            ? "terracotta-progress"
                            : "moss-progress"
                        }
                        style={{
                          width: `${displayHealth}%`,
                        }}
                      />
                    </div>

                    <div className="mt-2 flex justify-between">
                      <span className="text-[8px] text-[#A39484]">
                        Last service{" "}
                        {asset.last_service ?? "Not available"}
                      </span>

                      <span className="text-[8px] text-[#A39484]">
                        Health index
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </article>

          <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
            <div className="flex items-center justify-between px-6 py-5">
              <div>
                <p className="eyebrow">
                  Schedule
                </p>

                <h2 className="mt-2 text-[17px] font-semibold text-[#4A3528]">
                  Mission schedule
                </h2>
              </div>

              <Clock3
                className="h-5 w-5 text-[#806B59]"
                strokeWidth={1.5}
              />
            </div>

            <div>
              {missionSchedule.map((mission, index) => (
                <div
                  key={mission.mission_id}
                  className="grid grid-cols-[48px_1fr_auto] items-center gap-3 border-t border-[#E8DED1] px-6 py-5"
                >
                  <span className="font-mono text-[10px] text-[#9B8977]">
                    {index === 0
                      ? "08:30"
                      : index === 1
                        ? "11:00"
                        : "16:30"}
                  </span>

                  <div>
                    <p className="text-[12px] font-semibold text-[#4A3528]">
                      {mission.name}
                    </p>

                    <p className="mt-1 text-[9px] text-[#A39484]">
                      {mission.mission_id}
                    </p>
                  </div>

                  <div className="text-right">
                    <span
                      className={`rounded-full border px-2 py-1 text-[7px] font-semibold uppercase tracking-[0.1em] ${
                        mission.priority === "HIGH"
                          ? "border-[#D8A394] bg-[#F0D8CF] text-[#B95F46]"
                          : mission.priority === "MEDIUM"
                            ? "border-[#D8C8A9] bg-[#EEE2CD] text-[#876D47]"
                            : "border-[#C8D2B7] bg-[#E2E8D9] text-[#69784F]"
                      }`}
                    >
                      {mission.priority}
                    </span>

                    <p
                      className={`mt-2 text-[7px] font-semibold uppercase tracking-[0.12em] ${
                        mission.readiness_status === "READY"
                          ? "text-[#69784F]"
                          : mission.readiness_status === "NOT_READY"
                            ? "text-[#B95F46]"
                            : "text-[#927B66]"
                      }`}
                    >
                      {mission.readiness_status ===
                      "CONDITIONALLY_READY"
                        ? "CONDITIONAL"
                        : mission.readiness_status.replace(
                            "_",
                            " ",
                          )}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="grid overflow-hidden rounded-2xl border border-[#DED2C0] bg-[#EEE5D7] sm:grid-cols-3">
          <div className="flex items-center gap-3 border-b border-[#DED2C0] px-5 py-4 sm:border-b-0 sm:border-r">
            <CheckCircle2
              className="h-5 w-5 text-[#69784F]"
              strokeWidth={1.5}
            />

            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#6F5B4A]">
                Telemetry
              </p>

              <p className="mt-1 text-[10px] text-[#978575]">
                99.8% signal availability
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 border-b border-[#DED2C0] px-5 py-4 sm:border-b-0 sm:border-r">
            <Wrench
              className="h-5 w-5 text-[#B95F46]"
              strokeWidth={1.5}
            />

            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#6F5B4A]">
                Maintenance
              </p>

              <p className="mt-1 text-[10px] text-[#978575]">
                3 inspections in queue
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 px-5 py-4">
            <ShieldCheck
              className="h-5 w-5 text-[#69784F]"
              strokeWidth={1.5}
            />

            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#6F5B4A]">
                Evidence Layer
              </p>

              <p className="mt-1 text-[10px] text-[#978575]">
                All recommendations traceable
              </p>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}

/* Temporary pages for the other sidebar buttons.
   These keep the same application shell/design and prevent blank pages.
*/
function PlaceholderPage({
  title,
  eyebrow,
  description,
}: {
  title: string;
  eyebrow: string;
  description: string;
}) {
  return (
    <>
      <div className="space-y-7">
        <section>
          <p className="eyebrow">{eyebrow}</p>

          <h1 className="mt-2 text-[42px] font-semibold leading-none tracking-[-0.055em] text-[#3B2A20] sm:text-[48px]">
            {title}
          </h1>

          <p className="mt-3 max-w-xl text-[13px] leading-6 text-[#806B59]">
            {description}
          </p>
        </section>

        <section className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-8 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          <div className="flex items-center gap-3">
            <CheckCircle2
              className="h-5 w-5 text-[#69784F]"
              strokeWidth={1.5}
            />

            <div>
              <p className="text-[13px] font-semibold text-[#4A3528]">
                Module connected
              </p>

              <p className="mt-1 text-[11px] text-[#9B8977]">
                This workspace is ready for the module content.
              </p>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}

type Page =
  | "dashboard"
  | "assets"
  | "predictions"
  | "maintenance"
  | "ibm-bob";

function getPageFromPath(pathname: string): Page {
  const path = pathname.replace(/^\/+/, "").split("/")[0];

  if (path === "assets") {
    return "assets";
  }

  if (path === "predictions") {
    return "predictions";
  }

  if (path === "maintenance") {
    return "maintenance";
  }

  if (path === "ibm-bob") {
    return "ibm-bob";
  }

  return "dashboard";
}
function App() {
  const [currentPage, setCurrentPage] = useState("dashboard");

  const renderPage = () => {
    switch (currentPage) {
      case "assets":
        return <Assets />;

      case "predictions":
        return (
          <div className="space-y-7">
            <section>
              <p className="eyebrow">Prediction Intelligence</p>

              <h1 className="mt-2 text-[42px] font-semibold leading-none tracking-[-0.055em] text-[#3B2A20] sm:text-[48px]">
                Predictions
              </h1>

              <p className="mt-3 max-w-xl text-[13px] leading-6 text-[#806B59]">
                Monitor predicted asset failures, risk signals, and
                confidence levels.
              </p>
            </section>

            <section className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-8">
              <p className="text-[13px] font-semibold text-[#4A3528]">
                Prediction Intelligence
              </p>

              <p className="mt-2 text-[11px] leading-5 text-[#9B8977]">
                Prediction monitoring module is ready for the next integration
                step.
              </p>
            </section>
          </div>
        );

      case "maintenance":
        return <Maintenance />;

      case "ibm-bob":
        return <IBMBob />;

      case "dashboard":
      default:
        return <Dashboard />;
    }
  };

  return (
    <AppShell
      currentPage={currentPage}
      onNavigate={setCurrentPage}
    >
      {renderPage()}
    </AppShell>
  );
}

export default App;