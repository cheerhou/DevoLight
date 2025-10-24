export interface SelectedRole {
  name: string;
  score: number;
  reason: string;
  handoff_note: string;
}

export interface RoutingDecision {
  mode: 'single' | 'sequence' | 'smart' | 'halt';
  selected_roles: SelectedRole[];
  overall_rationale: string;
  fallback_plan: string;
  warnings: string[];
}

export interface RoleOutputModel {
  role_name: string;
  content: string;
}

export interface RouterResponse {
  decision: RoutingDecision;
  role_outputs: RoleOutputModel[];
  warnings: string[];
}

export interface RouterRequestPayload {
  session_id: string;
  payload: Record<string, unknown>;
}

export interface FormState {
  sessionId: string;
  scripture: string;
  userQuestion: string;
  userProfile: {
    age_group: string;
    profession: string;
    concerns: string[];
  };
  spiritualState: string;
  sessionStage: string;
  historySummary: string;
}
