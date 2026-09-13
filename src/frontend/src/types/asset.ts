export interface Asset {
  asset_id: string;
  name: string;
  status: string;
  component_id?: string;
  component_name?: string;
  criticality?: string;
  last_service?: string;
}