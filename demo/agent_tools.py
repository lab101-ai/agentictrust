from typing import List, Dict, Any, Type, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from demo.tools.workspan_data_tool import (
    get_all_companies,
    get_all_partners as get_all_workspan_partners,
    get_all_deals as get_all_workspan_deals,
    get_user_profiles,
    get_partner_insights,
    get_partner_benchmarks,
    get_deals_by_partner_id as get_workspan_deals_by_partner_id,
    get_partner_scores,
    get_partner_by_id as get_workspan_partner_by_id,
    get_deal_summary_analytics as get_workspan_deal_summary_analytics,
    get_insight_actions,
    get_telemetry_metrics
)

from demo.tools.cisco_data_tool import (
    get_all_partners,
    get_all_products,
    get_all_deals,
    get_deal_summary_analytics,
    get_all_users,
    get_owner_performance,
    get_partner_by_id,
    get_deals_by_partner_id,
    get_deal_notes,
    add_deal_note,
    get_deal_actions
)

# Define an empty schema for tools that don't take arguments
class EmptyArgsSchema(BaseModel):
    pass

# --- Define WorkSpan Specialized Tools ---

class GetAllWorkspanCompaniesTool(BaseTool):
    name: str = "Get All WorkSpan Companies"
    description: str = "Retrieves a list of all companies in the WorkSpan database, including their ID, name, HQ country, and industry."
    args_schema: Type[EmptyArgsSchema] = EmptyArgsSchema
    
    def _run(self) -> List[Dict[str, Any]]:
        return get_all_companies()

class GetAllWorkspanPartnersTool(BaseTool):
    name: str = "Get All WorkSpan Partners"
    description: str = "Retrieves a list of all partners in the WorkSpan database, including their ID, name, ultimate parent, and HQ country."
    args_schema: Type[EmptyArgsSchema] = EmptyArgsSchema
    
    def _run(self) -> List[Dict[str, Any]]:
        return get_all_workspan_partners()

class GetAllWorkspanDealsTool(BaseTool):
    name: str = "Get All WorkSpan Deals"
    description: str = "Retrieves a list of all deals in the WorkSpan database with company, partner, and product details. Optional: specify a limit."
    
    def _run(self, limit: int = 100) -> List[Dict[str, Any]]:
        return get_all_workspan_deals(limit=limit)

class GetWorkspanUserProfilesTool(BaseTool):
    name: str = "Get WorkSpan User Profiles"
    description: str = "Retrieves a list of all user profiles in the WorkSpan database with company details."
    args_schema: Type[EmptyArgsSchema] = EmptyArgsSchema
    
    def _run(self) -> List[Dict[str, Any]]:
        return get_user_profiles()

class GetPartnerIdArgs(BaseModel):
    partner_id: int = Field(..., description="The ID of the partner to retrieve data for.")

class GetWorkspanPartnerByIdTool(BaseTool):
    name: str = "Get WorkSpan Partner By ID"
    description: str = "Retrieves detailed information for a specific WorkSpan partner using their partner ID. Input: 'partner_id' (integer)."
    args_schema: Type[GetPartnerIdArgs] = GetPartnerIdArgs
    
    def _run(self, partner_id: int) -> Optional[Dict[str, Any]]:
        return get_workspan_partner_by_id(partner_id)

class GetWorkspanPartnerInsightsTool(BaseTool):
    name: str = "Get WorkSpan Partner Insights"
    description: str = "Retrieves all insights for a specific partner in the WorkSpan database. Input: 'partner_id' (integer)."
    args_schema: Type[GetPartnerIdArgs] = GetPartnerIdArgs
    
    def _run(self, partner_id: int) -> List[Dict[str, Any]]:
        return get_partner_insights(partner_id)

class GetWorkspanPartnerBenchmarksTool(BaseTool):
    name: str = "Get WorkSpan Partner Benchmarks"
    description: str = "Retrieves all benchmarks for a specific partner in the WorkSpan database. Input: 'partner_id' (integer)."
    args_schema: Type[GetPartnerIdArgs] = GetPartnerIdArgs
    
    def _run(self, partner_id: int) -> List[Dict[str, Any]]:
        return get_partner_benchmarks(partner_id)

class GetWorkspanDealsByPartnerTool(BaseTool):
    name: str = "Get WorkSpan Deals By Partner ID"
    description: str = "Retrieves all deals for a specific partner in the WorkSpan database. Input: 'partner_id' (integer)."
    args_schema: Type[GetPartnerIdArgs] = GetPartnerIdArgs
    
    def _run(self, partner_id: int) -> List[Dict[str, Any]]:
        return get_workspan_deals_by_partner_id(partner_id)

class GetWorkspanPartnerScoresTool(BaseTool):
    name: str = "Get WorkSpan Partner Scores"
    description: str = "Retrieves all scores for a specific partner in the WorkSpan database. Input: 'partner_id' (integer)."
    args_schema: Type[GetPartnerIdArgs] = GetPartnerIdArgs
    
    def _run(self, partner_id: int) -> List[Dict[str, Any]]:
        return get_partner_scores(partner_id)

class GetWorkspanDealSummaryTool(BaseTool):
    name: str = "Get WorkSpan Deal Summary Analytics"
    description: str = "Calculates and retrieves summary analytics for WorkSpan deals, including total deals, amount, and stages."
    args_schema: Type[EmptyArgsSchema] = EmptyArgsSchema
    
    def _run(self) -> Dict[str, Any]:
        return get_workspan_deal_summary_analytics()

class GetInsightIdArgs(BaseModel):
    insight_id: int = Field(..., description="The ID of the insight to retrieve actions for.")

class GetInsightActionsTool(BaseTool):
    name: str = "Get WorkSpan Insight Actions"
    description: str = "Retrieves all actions for a specific insight. Input: 'insight_id' (integer)."
    args_schema: Type[GetInsightIdArgs] = GetInsightIdArgs
    
    def _run(self, insight_id: int) -> List[Dict[str, Any]]:
        return get_insight_actions(insight_id)

class GetTelemetryMetricsArgs(BaseModel):
    partner_id: int = Field(..., description="The ID of the partner to retrieve telemetry metrics for.")
    limit: int = Field(50, description="Maximum number of metrics to retrieve.")

class GetTelemetryMetricsTool(BaseTool):
    name: str = "Get WorkSpan Telemetry Metrics"
    description: str = "Retrieves telemetry metrics for a specific partner. Input: 'partner_id' (integer) and optional 'limit' (integer, default 50)."
    args_schema: Type[GetTelemetryMetricsArgs] = GetTelemetryMetricsArgs
    
    def _run(self, partner_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        return get_telemetry_metrics(partner_id, limit)

# --- Define Cisco Data Tools ---

class GetAllPartnersTool(BaseTool):
    name: str = "Get All Cisco Partners"
    description: str = "Retrieves a list of all Cisco partner companies, including their ID, name, tier, country, industry, and CRM account ID."
    args_schema: Type[EmptyArgsSchema] = EmptyArgsSchema
    
    def _run(self) -> List[Dict[str, Any]]:
        return get_all_partners()

class GetAllProductsTool(BaseTool):
    name: str = "Get All Cisco Products"
    description: str = "Retrieves a list of all Cisco products, including their ID, name, segment, and family."
    args_schema: Type[EmptyArgsSchema] = EmptyArgsSchema

    def _run(self) -> List[Dict[str, Any]]:
        return get_all_products()

class GetAllDealsTool(BaseTool):
    name: str = "Get All Cisco Deals"
    description: str = "Retrieves a list of Cisco deals, including deal ID, partner name, product name, amount, stage, close date, owner email, and if it's actionable. Optional input: 'limit' (integer) to specify the number of deals to return (default is 100)."
    args_schema: Type[EmptyArgsSchema] = EmptyArgsSchema

    def _run(self, limit: int = 100) -> List[Dict[str, Any]]:
        return get_all_deals(limit=limit)

class GetDealSummaryAnalyticsTool(BaseTool):
    name: str = "Get Cisco Deal Summary Analytics"
    description: str = "Calculates and retrieves summary analytics for Cisco deals, including total number of deals, total monetary amount of all deals, and counts of deals per stage."
    args_schema: Type[EmptyArgsSchema] = EmptyArgsSchema

    def _run(self) -> Dict[str, Any]:
        return get_deal_summary_analytics()

class GetAllUsersTool(BaseTool):
    name: str = "Get All Cisco Users"
    description: str = "Retrieves a list of all Cisco users (internal), including their ID, email, first name, last name, and department."
    args_schema: Type[EmptyArgsSchema] = EmptyArgsSchema

    def _run(self) -> List[Dict[str, Any]]:
        return get_all_users()

class GetOwnerPerformanceTool(BaseTool):
    name: str = "Get Cisco Deal Owner Performance"
    description: str = "Retrieves a summary of deal performance metrics grouped by Cisco sales owners. Includes owner name, total deal amount, deal counts per stage, and total deals for each owner."
    args_schema: Type[EmptyArgsSchema] = EmptyArgsSchema

    def _run(self) -> Dict[str, List[Dict[str, Any]]]:
        return get_owner_performance()

class GetPartnerByIdArgs(BaseModel):
    partner_id: int = Field(..., description="The ID of the partner to retrieve.")

class GetPartnerByIdTool(BaseTool):
    name: str = "Get Cisco Partner By ID"
    description: str = "Retrieves detailed information for a specific Cisco partner using their partner ID. Input: 'partner_id' (integer)."
    args_schema: Type[GetPartnerByIdArgs] = GetPartnerByIdArgs

    def _run(self, partner_id: int) -> Optional[Dict[str, Any]]:
        return get_partner_by_id(partner_id=partner_id)

class GetDealsByPartnerIdArgs(BaseModel):
    partner_id: int = Field(..., description="The ID of the partner whose deals to retrieve.")

class GetDealsByPartnerIdTool(BaseTool):
    name: str = "Get Cisco Deals By Partner ID"
    description: str = "Retrieves all deals associated with a specific Cisco partner ID. Input: 'partner_id' (integer)."
    args_schema: Type[GetDealsByPartnerIdArgs] = GetDealsByPartnerIdArgs

    def _run(self, partner_id: int) -> List[Dict[str, Any]]:
        return get_deals_by_partner_id(partner_id=partner_id)

class GetDealNotesArgs(BaseModel):
    deal_id: int = Field(..., description="The ID of the deal for which to retrieve notes.")

class GetDealNotesTool(BaseTool):
    name: str = "Get Cisco Deal Notes"
    description: str = "Retrieves all notes associated with a specific Cisco deal ID. Input: 'deal_id' (integer)."
    args_schema: Type[GetDealNotesArgs] = GetDealNotesArgs

    def _run(self, deal_id: int) -> List[Dict[str, Any]]:
        return get_deal_notes(deal_id=deal_id)

class AddDealNoteArgs(BaseModel):
    deal_id: int = Field(..., description="The ID of the deal to add a note to.")
    user_id: int = Field(..., description="The ID of the user adding the note.")
    note_text: str = Field(..., description="The text content of the note.")

class AddDealNoteTool(BaseTool):
    name: str = "Add Cisco Deal Note"
    description: str = "Adds a new note to a specific Cisco deal. Inputs: 'deal_id' (integer), 'user_id' (integer of the user adding the note), 'note_text' (string). Returns the ID of the newly created note."
    args_schema: Type[AddDealNoteArgs] = AddDealNoteArgs

    def _run(self, deal_id: int, user_id: int, note_text: str) -> int:
        return add_deal_note(deal_id=deal_id, user_id=user_id, note_text=note_text)

class GetDealActionsArgs(BaseModel):
    deal_id: int = Field(..., description="The ID of the deal for which to retrieve actions.")

class GetDealActionsTool(BaseTool):
    name: str = "Get Cisco Deal Actions"
    description: str = "Retrieves all action items associated with a specific Cisco deal ID. Input: 'deal_id' (integer)."
    args_schema: Type[GetDealActionsArgs] = GetDealActionsArgs

    def _run(self, deal_id: int) -> List[Dict[str, Any]]:
        return get_deal_actions(deal_id=deal_id)

# Create a list of all WorkSpan specialized tools
workspan_tools_list = [
    GetAllWorkspanCompaniesTool(),
    GetAllWorkspanPartnersTool(),
    GetAllWorkspanDealsTool(),
    GetWorkspanUserProfilesTool(),
    GetWorkspanPartnerByIdTool(),
    GetWorkspanPartnerInsightsTool(),
    GetWorkspanPartnerBenchmarksTool(),
    GetWorkspanDealsByPartnerTool(),
    GetWorkspanPartnerScoresTool(),
    GetWorkspanDealSummaryTool(),
    GetInsightActionsTool(),
    GetTelemetryMetricsTool()
]

# Instantiate all Cisco tools
cisco_tools_list = [
    GetAllPartnersTool(),
    GetAllProductsTool(),
    GetAllDealsTool(),
    GetDealSummaryAnalyticsTool(),
    GetAllUsersTool(),
    GetOwnerPerformanceTool(),
    GetPartnerByIdTool(),
    GetDealsByPartnerIdTool(),
    GetDealNotesTool(),
    AddDealNoteTool(),
    GetDealActionsTool()
] 