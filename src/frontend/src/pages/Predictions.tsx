import {
  Activity,
  ArrowUpRight,
  CheckCircle2,
  Clock3,
  ShieldAlert,
  TriangleAlert,
} from "lucide-react";

interface Prediction {
  id: string;
  component: string;
  health: number;
  risk: "Low" | "Moderate" | "High";
  failureWindow: string;
  confidence: number;
  trend: string;
  recommendation: string;
}

const predictions: Prediction[] = [
  {
    id: "AS-1047",
    component: "Main Bearing",
    health: 98,
    risk: "Low",
    failureWindow: "90+ days",
    confidence: 94,
    trend: "Stable",
    recommendation: "Continue normal monitoring and scheduled service.",
  },
  {
    id: "AS-1032",
    component: "Engine Assembly",
    health: 81,
    risk: "High",
    failureWindow: "14–21 days",
    confidence: 91,
    trend: "Declining",
    recommendation: "Inspect engine assembly and prioritize corrective maintenance.",
  },
  {
    id: "AS-1088",
    component: "Hydraulic System",
    health: 88,
    risk: "Moderate",
    failureWindow: "30–45 days",
    confidence: 86,
    trend: "Watch",
    recommendation: "Increase monitoring frequency and review hydraulic service history.",
  },
];

function riskTextColor(risk: Prediction["risk"]) {
  if (risk === "High") {
    return "text-[#B95F46]";
  }

  if (risk === "Moderate") {
    return "text-[#9A7650]";
  }

  return "text-[#69784F]";
}

function riskBgColor(risk: Prediction["risk"]) {
  if (risk === "High") {
    return "bg-[#F1D9D0]";
  }

  if (risk === "Moderate") {
    return "bg-[#EFE3CE]";
  }

  return "bg-[#E0E7D6]";
}

function riskIcon(risk: Prediction["risk"]) {
  if (risk === "High") {
    return (
      <TriangleAlert
        className="h-4 w-4 text-[#B95F46]"
        strokeWidth={1.7}
      />
    );
  }

  if (risk === "Moderate") {
    return (
      <ShieldAlert
        className="h-4 w-4 text-[#9A7650]"
        strokeWidth={1.7}
      />
    );
  }

  return (
    <CheckCircle2
      className="h-4 w-4 text-[#69784F]"
      strokeWidth={1.7}
    />
  );
}

function Predictions() {
  const highRisk = predictions.filter(
    (prediction) => prediction.risk === "High",
  ).length;

  const moderateRisk = predictions.filter(
    (prediction) => prediction.risk === "Moderate",
  ).length;

  const lowRisk = predictions.filter(
    (prediction) => prediction.risk === "Low",
  ).length;

  return (
    <div className="space-y-7">
      {/* Heading */}
      <section className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="eyebrow">Predictive Intelligence</p>

          <h1 className="mt-2 text-[42px] font-semibold leading-none tracking-[-0.055em] text-[#3B2A20] sm:text-[48px]">
            Predictions
          </h1>

          <p className="mt-3 max-w-xl text-[13px] leading-6 text-[#806B59]">
            Identify emerging asset risks, estimate failure windows, and
            prioritize intervention before operational impact.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="rounded-full border border-[#D8CBB9] bg-[#EEE5D7] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#806B59]">
            Predictive Model
          </span>

          <span className="rounded-full border border-[#C2CEAE] bg-[#DDE5D1] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#596842]">
            Live
          </span>
        </div>
      </section>

      {/* Summary cards */}
      <section className="grid gap-5 md:grid-cols-3">
        <article className="rounded-2xl border border-[#E1B7A9] bg-[#FBF3EF] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">High Risk</p>

              <div className="mt-4 text-[42px] font-light leading-none tracking-[-0.06em] text-[#B95F46]">
                {highRisk}
              </div>

              <p className="mt-3 text-[10px] text-[#A66B5A]">
                Requires intervention
              </p>
            </div>

            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#F1D9D0]">
              <TriangleAlert
                className="h-4 w-4 text-[#B95F46]"
                strokeWidth={1.7}
              />
            </div>
          </div>
        </article>

        <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">Moderate Risk</p>

              <div className="mt-4 text-[42px] font-light leading-none tracking-[-0.06em] text-[#9A7650]">
                {moderateRisk}
              </div>

              <p className="mt-3 text-[10px] text-[#9B8977]">
                Requires closer monitoring
              </p>
            </div>

            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#EFE3CE]">
              <ShieldAlert
                className="h-4 w-4 text-[#9A7650]"
                strokeWidth={1.7}
              />
            </div>
          </div>
        </article>

        <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">Low Risk</p>

              <div className="mt-4 text-[42px] font-light leading-none tracking-[-0.06em] text-[#69784F]">
                {lowRisk}
              </div>

              <p className="mt-3 text-[10px] text-[#9B8977]">
                Operating within forecast
              </p>
            </div>

            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#E0E7D6]">
              <CheckCircle2
                className="h-4 w-4 text-[#69784F]"
                strokeWidth={1.7}
              />
            </div>
          </div>
        </article>
      </section>

      {/* Prediction list */}
      <section className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
        <div className="flex items-center justify-between px-6 py-5">
          <div>
            <p className="eyebrow">Fleet Forecast</p>

            <h2 className="mt-2 text-[21px] font-semibold tracking-[-0.025em] text-[#4A3528]">
              Asset risk outlook
            </h2>

            <p className="mt-2 text-[11px] text-[#9B8977]">
              Model-generated condition forecasts and recommended actions.
            </p>
          </div>

          <Activity
            className="h-5 w-5 text-[#806B59]"
            strokeWidth={1.5}
          />
        </div>

        <div>
          {predictions.map((prediction) => (
            <article
              key={prediction.id}
              className="border-t border-[#E8DED1] px-6 py-6"
            >
              <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-3">
                    {riskIcon(prediction.risk)}

                    <div>
                      <p className="font-mono text-[12px] font-semibold text-[#4A3528]">
                        {prediction.id}
                      </p>

                      <p className="mt-1 text-[10px] text-[#9B8977]">
                        {prediction.component}
                      </p>
                    </div>

                    <span
                      className={`ml-2 rounded-full px-3 py-1.5 text-[8px] font-semibold uppercase tracking-[0.12em] ${riskBgColor(
                        prediction.risk,
                      )} ${riskTextColor(prediction.risk)}`}
                    >
                      {prediction.risk} risk
                    </span>
                  </div>

                  <div className="mt-5 grid gap-4 sm:grid-cols-3">
                    <div>
                      <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
                        Failure window
                      </p>

                      <div className="mt-2 flex items-center gap-2">
                        <Clock3
                          className="h-4 w-4 text-[#806B59]"
                          strokeWidth={1.5}
                        />
                        <p className="text-[12px] text-[#5D4535]">
                          {prediction.failureWindow}
                        </p>
                      </div>
                    </div>

                    <div>
                      <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
                        Model confidence
                      </p>

                      <p className="mt-2 text-[12px] text-[#5D4535]">
                        {prediction.confidence}%
                      </p>
                    </div>

                    <div>
                      <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
                        Condition trend
                      </p>

                      <div className="mt-2 flex items-center gap-2">
                        <ArrowUpRight
                          className={`h-4 w-4 ${
                            prediction.trend === "Declining"
                              ? "rotate-90 text-[#B95F46]"
                              : "text-[#69784F]"
                          }`}
                          strokeWidth={1.5}
                        />
                        <p className="text-[12px] text-[#5D4535]">
                          {prediction.trend}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-5">
                    <div className="flex items-center justify-between">
                      <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
                        Current health
                      </p>

                      <span className="text-[10px] font-medium text-[#806B59]">
                        {prediction.health}%
                      </span>
                    </div>

                    <div className="mt-2 h-2 overflow-hidden rounded-full bg-[#E5DACA]">
                      <div
                        className={`h-full rounded-full ${
                          prediction.risk === "High"
                            ? "bg-[#B95F46]"
                            : prediction.risk === "Moderate"
                              ? "bg-[#9A7650]"
                              : "bg-[#69784F]"
                        }`}
                        style={{ width: `${prediction.health}%` }}
                      />
                    </div>
                  </div>

                  <div className="mt-5 rounded-xl border border-[#E4D8C9] bg-[#F5EEE4] px-4 py-3">
                    <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
                      Recommended action
                    </p>

                    <p className="mt-1 text-[11px] leading-5 text-[#5D4535]">
                      {prediction.recommendation}
                    </p>
                  </div>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* Model status */}
      <section className="grid gap-0 overflow-hidden rounded-2xl border border-[#DED2C0] bg-[#EEE5D7] md:grid-cols-2">
        <div className="flex items-center gap-3 px-6 py-5">
          <CheckCircle2
            className="h-5 w-5 text-[#69784F]"
            strokeWidth={1.5}
          />

          <div>
            <p className="text-[13px] font-semibold text-[#4A3528]">
              Prediction engine operational
            </p>

            <p className="mt-1 text-[11px] text-[#9B8977]">
              Forecasts are available for all registered assets.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 border-t border-[#DED2C0] px-6 py-5 md:border-l md:border-t-0">
          <Activity
            className="h-5 w-5 text-[#69784F]"
            strokeWidth={1.5}
          />

          <div>
            <p className="text-[13px] font-semibold text-[#4A3528]">
              Continuous monitoring
            </p>

            <p className="mt-1 text-[11px] text-[#9B8977]">
              Risk scores update as new asset signals become available.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Predictions;
