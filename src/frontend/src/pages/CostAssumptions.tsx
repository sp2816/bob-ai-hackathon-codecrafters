import React, { useEffect, useState } from "react";
import { getCostAssumptions, updateCostAssumption, formatCurrency } from "../services/api";
import type { ApiCostAssumption } from "../types/api";
import { Edit2, Save, X, Loader2, CheckCircle2 } from "lucide-react";

export default function CostAssumptions() {
  const [assumptions, setAssumptions] = useState<ApiCostAssumption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAssumptions();
  }, []);

  const fetchAssumptions = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getCostAssumptions();
      setAssumptions(data);
    } catch (err) {
      setError("Unable to load cost assumptions.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <section className="flex items-center justify-between">
        <div>
          <h1 className="page-title mt-2">Cost Assumptions</h1>
          <p className="body-text mt-2 max-w-xl">
            These are configurable organization-level assumptions used to model the economic impact of maintenance decisions. They are not actual costs incurred by individual assets.
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>Currency</p>
          <p className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>INR (₹)</p>
        </div>
      </section>

      <div className="banner-info">
        <strong>MODELED DEMO ASSUMPTIONS</strong> — These values are configurable estimates used by the economic model. They are not actual costs incurred by individual assets. AssetSentinel uses existing sensor/HUMS and maintenance data. <strong>AssetSentinel does not replace physical sensors.</strong>
      </div>

      {loading && assumptions.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin" style={{ color: "var(--brand-accent)" }} />
          <span className="ml-3 font-semibold" style={{ color: "var(--text-muted)" }}>Loading cost assumptions...</span>
        </div>
      )}

      {error && assumptions.length === 0 && (
        <div className="banner-danger flex items-center justify-between">
          <span>{error}</span>
          <button onClick={fetchAssumptions} className="btn-secondary-sm">Retry</button>
        </div>
      )}

      {!loading && assumptions.length === 0 && !error && (
        <div className="card rounded-xl p-8 text-center">
          <p className="text-lg font-semibold" style={{ color: "var(--text-muted)" }}>No cost assumptions configured.</p>
          <p className="mt-2 text-sm" style={{ color: "var(--text-muted)" }}>The backend should seed defaults on startup.</p>
        </div>
      )}

      {assumptions.map((assumption) => (
        <CostAssumptionEditor key={assumption.component_type} initialData={assumption} onSaved={fetchAssumptions} />
      ))}
    </div>
  );
}

function CostAssumptionEditor({ initialData, onSaved }: { initialData: ApiCostAssumption; onSaved: () => void }) {
  const [isEditing, setIsEditing] = useState(false);
  const [data, setData] = useState<ApiCostAssumption>(initialData);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    setData(initialData);
  }, [initialData]);

  const handleSave = async () => {
    setSaving(true);
    setSaveMessage(null);
    try {
      await updateCostAssumption(data.component_type, data);
      setSaveMessage("Cost assumptions updated.");
      setIsEditing(false);
      onSaved();
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (err) {
      console.error(err);
      setSaveMessage("Failed to save changes.");
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field: keyof ApiCostAssumption, value: number) => {
    setData(prev => ({ ...prev, [field]: value }));
  };

  const renderField = (label: string, field: keyof ApiCostAssumption, isPercent: boolean = false) => {
    const value = data[field] as number;
    return (
      <div className="flex flex-col">
        <label className="text-[11px] font-semibold uppercase tracking-wider mb-1" style={{ color: "var(--text-muted)" }}>{label}</label>
        {isEditing ? (
          <div className="relative">
            {!isPercent && <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-sm" style={{ color: "var(--text-muted)" }}>₹</span>}
            <input 
              type="number"
              className="w-full rounded-md px-2 py-1.5 text-sm font-semibold"
              style={{ 
                background: "var(--surface-input, var(--surface-base))", 
                border: "1px solid var(--border-default)",
                color: "var(--text-primary)",
                paddingLeft: isPercent ? "0.5rem" : "1.5rem"
              }}
              value={isPercent ? value * 100 : value}
              onChange={(e) => handleChange(field, isPercent ? parseFloat(e.target.value) / 100 : parseFloat(e.target.value))}
            />
            {isPercent && <span className="absolute right-2.5 top-1/2 -translate-y-1/2 text-sm" style={{ color: "var(--text-muted)" }}>%</span>}
          </div>
        ) : (
          <span className="text-[15px] font-bold" style={{ color: "var(--text-primary)" }}>
            {isPercent ? `${(value * 100).toFixed(0)}%` : formatCurrency(value)}
          </span>
        )}
      </div>
    );
  };

  return (
    <article className="card rounded-xl overflow-hidden transition-all duration-200">
      <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: "1px solid var(--border-subtle)", background: "var(--surface-elevated)" }}>
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-bold tracking-tight uppercase" style={{ color: "var(--text-primary)" }}>
            {data.component_type.replace(/_/g, " ")}
          </h2>
          {saveMessage === "Cost assumptions updated." && (
            <span className="flex items-center gap-1.5 text-xs font-semibold" style={{ color: "var(--success-text)" }}>
              <CheckCircle2 className="h-3.5 w-3.5" /> Saved
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {isEditing ? (
            <>
              <button onClick={() => { setIsEditing(false); setData(initialData); }} disabled={saving} className="btn-secondary-sm">
                <X className="h-3.5 w-3.5" /> Cancel
              </button>
              <button onClick={handleSave} disabled={saving} className="btn-primary-sm flex items-center gap-1.5">
                {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                Save
              </button>
            </>
          ) : (
            <button onClick={() => setIsEditing(true)} className="btn-secondary-sm">
              <Edit2 className="h-3.5 w-3.5" /> Edit
            </button>
          )}
        </div>
      </div>

      <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-x-8 gap-y-6">
        <div className="col-span-1 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider mb-3" style={{ color: "var(--danger-text)" }}>Traditional Operations</h3>
          {renderField("Monitoring Cost", "monitoring_cost_traditional")}
          {renderField("Inspection Cost", "inspection_cost_traditional")}
          {renderField("Preventive Maint.", "preventive_maintenance_traditional")}
        </div>
        <div className="col-span-1 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider mb-3" style={{ color: "var(--success-text)" }}>AssetSentinel</h3>
          {renderField("Existing Sensor Data", "sensor_data_cost_assetsentinel")}
          {renderField("Planned Downtime Hrs", "planned_downtime_hours")}
          {renderField("Deployment Cost", "assetsentinel_deployment_cost")}
        </div>
        <div className="col-span-1 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider mb-3" style={{ color: "var(--warning-text)" }}>Failure Impact</h3>
          {renderField("Emerg. Intervention", "emergency_intervention_cost")}
          {renderField("Emerg. Maintenance", "emergency_maintenance_cost")}
          {renderField("Emerg. Downtime Hrs", "emergency_downtime_hours")}
          {renderField("Downtime Cost / Hr", "downtime_cost_per_hour")}
          {renderField("Mission Disruption", "mission_disruption_cost")}
        </div>
        <div className="col-span-1 space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider mb-3" style={{ color: "var(--brand-400)" }}>Model Parameters</h3>
          {renderField("Standard Repair", "repair_cost")}
          {renderField("Standard Replacement", "replacement_cost")}
          {renderField("Residual Risk", "residual_failure_probability_multiplier", true)}
          <div className="mt-4 pt-4" style={{ borderTop: "1px dashed var(--border-subtle)" }}>
            <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>Last Updated: Just now<br/>Source: System Defaults</p>
          </div>
        </div>
      </div>
    </article>
  );
}
