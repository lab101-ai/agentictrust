**Designing database schema**

The user asks for a database design for two platforms: Cisco Operational (internal, Cisco data) and Workspan (aggregated data including Cisco, Google, and Meta). Cisco requires tables for Partners, AdoptionScore, Deals, Telemetry, Company, Users, and possibly Agents. Workspan will require similar tables but supporting multiple companies. Both databases must support metrics like partner adoption scores, deals, and telemetry. I'll focus on a relational design, keeping it as generic as possible, but without worrying about security, as mentioned.


Thought for 20 seconds


Below is a **starter relational design** for two independent databases that will let you stand up a realistic demo of the Cisco‑only operational store and the multi‑tenant Workspan analytics store.

> • **Cisco Operational DB** – authoritative, near‑real‑time data that only Cisco systems can write
> • **Workspan Analytics DB** – cross‑company, read‑optimized store fed by periodic extracts from Cisco, Google, Meta, etc.

Both are expressed in a neutral SQL style (PostgreSQL / MySQL‑compatible).  Feel free to rename or prune tables to fit the actual demo scope.

---

## 1. Cisco Operational DB  (`cisco_ops`)

| Table                    | Key(s)                                        | Purpose & Key Columns                                                                                              |
| ------------------------ | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **partners**             | `partner_id PK`                               | Canonical list of Cisco partners.<br>• `partner_name`, `partner_tier`, `country`, `industry`, `crm_account_id`     |
| **contacts**             | `contact_id PK`                               | Named contacts at each partner.<br>• `partner_id FK`, `first_name`, `last_name`, `email`, `role`                   |
| **users**                | `user_id PK`                                  | Cisco employees who interact with partners.<br>• `email`, `first_name`, `last_name`, `department`                  |
| **products**             | `product_id PK`                               | Cisco SKUs or solution families.<br>• `product_name`, `segment`, `family`                                          |
| **deals**                | `deal_id PK`                                  | Pipeline & booked deals.<br>• `partner_id FK`, `product_id FK`, `amount_usd`, `stage`, `close_dt`, `is_actionable` |
| **deal\_notes**          | `note_id PK`                                  | Free‑form notes threaded to a deal.<br>• `deal_id FK`, `user_id FK`, `note_txt`, `created_at`                      |
| **lci\_telemetry**       | `telemetry_id PK`                             | Raw lifecycle‑incentive telemetry.<br>• `partner_id FK`, `metric_name`, `metric_value`, `captured_at`              |
| **adoption\_scores**     | (`partner_id`, `score_dt`) PK                 | Daily/weekly overall adoption score.<br>• `score_value`, `score_breakdown_json`                                    |
| **adoption\_components** | (`partner_id`, `component_id`, `score_dt`) PK | Granular components that roll up to the overall score.<br>• `component_name`, `component_score`                    |
| **deal\_actions**        | `action_id PK`                                | Tasks suggested by the AI agent.<br>• `deal_id FK`, `action_txt`, `owner_user_id FK`, `due_dt`, `status`           |
| **region\_dim**          | `region_id PK`                                | Reusable geography dimension.<br>• `region_name`, `geo_hierarchy_json`                                             |
| **partner\_region\_map** | (`partner_id`, `region_id`) PK                | Partners may operate in multiple regions.                                                                          |
| **etl\_runs**            | `run_id PK`                                   | Audit table for outbound feeds into Workspan.<br>• `feed_name`, `run_ts`, `records_sent`, `status`                 |

### Relationships (ER glance)

```
partners 1─∞ contacts
partners 1─∞ deals 1─∞ deal_notes
partners 1─∞ adoption_scores
adoption_scores 1─∞ adoption_components
partners 1─∞ lci_telemetry
products 1─∞ deals
users 1─∞ deal_actions
```

---

## 2. Workspan Analytics DB  (`workspan_core`)

| Table                     | Key(s)                                         | Purpose & Key Columns                                                                                                                              |
| ------------------------- | ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **companies**             | `company_id PK`                                | Tenant companies (Cisco, Google, Meta).<br>• `company_name`, `hq_country`, `industry`                                                              |
| **company\_data\_feeds**  | `feed_id PK`                                   | Catalog of inbound feeds per company.<br>• `company_id FK`, `feed_type`, `schedule`, `last_run_ts`                                                 |
| **partners**              | `partner_id PK`                                | Global partner list – deduped across companies.<br>• `partner_name`, `ultimate_parent`, `hq_country`                                               |
| **company\_partner\_map** | (`company_id`,`partner_id`) PK                 | Maps each company’s internal partner ID to the global one.<br>• `company_partner_key` (e.g. Cisco CRM ID)                                          |
| **products**              | `product_id PK`                                | Normalized product families across companies.<br>• `product_name`, `category`, `company_id FK` (NULL = cross‑company)                              |
| **deals**                 | `deal_id PK`                                   | Aggregated deal facts from all vendors.<br>• `company_id FK`, `partner_id FK`, `product_id FK`, `amount_usd`, `stage`, `close_dt`, `is_actionable` |
| **deal\_attributes**      | (`deal_id`,`attr_name`) PK                     | EAV store for extra, vendor‑specific fields.<br>• `attr_value`                                                                                     |
| **telemetry\_metrics**    | `metric_id PK`                                 | Raw telemetry events from all companies.<br>• `company_id FK`, `partner_id FK`, `metric_name`, `metric_value`, `captured_at`                       |
| **partner\_scores**       | (`partner_id`,`score_dt`,`score_type`) PK      | Daily/weekly scores (e.g., adoption, health).<br>• `company_id FK`, `score_value`                                                                  |
| **benchmark\_dimensions** | `dimension_id PK`                              | Attributes used for cohorting benchmarks (region, industry).<br>• `dimension_name`, `dimension_value`                                              |
| **partner\_benchmarks**   | (`dimension_id`,`partner_id`,`metric_name`) PK | Benchmark deltas vs. cohort.<br>• `company_id FK`, `partner_metric_value`, `cohort_avg_value`, `variance`                                          |
| **insights**              | `insight_id PK`                                | AI‑generated insights surfaced in the UI.<br>• `partner_id FK`, `company_id FK`, `insight_txt`, `severity`, `created_at`                           |
| **insight\_actions**      | `action_id PK`                                 | Prescriptive actions linked to an insight.<br>• `insight_id FK`, `action_txt`, `priority`, `status`                                                |
| **user\_profiles**        | `profile_id PK`                                | Workspan portal users (vendor or partner).<br>• `email`, `first_name`, `last_name`, `company_id FK`, `role`                                        |
| **user\_partner\_access** | (`profile_id`,`partner_id`) PK                 | Which partners a portal user can see.                                                                                                              |
| **etl\_audit**            | `run_id PK`                                    | Inbound ETL run status per company/feed.                                                                                                           |

### Relationships (ER glance)

```
companies 1─∞ company_data_feeds
companies 1─∞ partners (via company_partner_map)
partners 1─∞ deals
deals 1─∞ deal_attributes
partners 1─∞ telemetry_metrics
partners 1─∞ partner_scores
benchmark_dimensions 1─∞ partner_benchmarks
insights 1─∞ insight_actions
companies 1─∞ user_profiles
user_profiles ∞─∞ partners (via user_partner_access)
```

---

## 3. How the Two Databases Align

| Concept           | Cisco Operational                         | Workspan                                     |
| ----------------- | ----------------------------------------- | -------------------------------------------- |
| Partner master    | `cisco_ops.partners`                      | `workspan_core.partners` (global)            |
| Adoption score    | `adoption_scores` + `adoption_components` | `partner_scores` (`score_type = 'adoption'`) |
| Deals             | `deals`, `deal_actions`                   | `deals`, `deal_attributes`                   |
| LCI telemetry     | `lci_telemetry`                           | `telemetry_metrics`                          |
| Company dimension | *N/A (always Cisco)*                      | `companies` table                            |

**ETL outline**

1. Nightly extract from Cisco tables → S3/Blob → Workspan loader
2. Loader populates `company_partner_map`, `products`, `deals`, `telemetry_metrics`, etc.
3. Workspan runs its enrichment jobs to compute `partner_scores`, `insights`, and `benchmarks`.
