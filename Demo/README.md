# What files are included (high level)

- `clusters.csv` → one row per **feature/theme** (the roll-up)
- `cluster_trend.csv` → one row per **theme per week** (for momentum lines)
- `feedback.csv` → one row per **raw message** (Slack/Forum/CRM)
- `cluster_members.csv` → **junction** linking messages ↔ themes
- `ClusterAgg.tds`, `ClusterTrend.tds` → Tableau **data-source shortcuts** that point to the CSVs (handy for quick local testing).

> In production, these CSVs map 1:1 to Salesforce custom objects (below) and then flow into Data Cloud via data streams, which Tableau Next reads.

---

# Field-by-field data dictionary

## 1) `clusters.csv` — one row per theme

| Field | Type | Meaning / Use |
| --- | --- | --- |
| `ClusterId` | Text (PK) | Unique theme ID (used to relate to other files) |
| `Title` | Text | Human name for the theme (e.g., “Dark Mode”) |
| `Summary` | Text (long) | Short description summarizing the theme |
| `PriorityScore` | Number | Overall importance (frequency + recency + VIP share) |
| `UniqueUsers` | Number | Distinct authors who asked for it |
| `VIPCount` | Number | Count of VIP/paying users in that theme |
| `RecencyDays` | Number | Days since last mention (lower = fresher) |
| `Confidence` | Number (0–1) | Cluster quality (0 = weak, 1 = strong) |
| `Status` | Text | `New`, `Reviewed`, `High Priority`, `Planned`, `Resolved` |
| `LastComputedAt` | Date/Time | When this roll-up was computed |

**Salesforce mapping:** `Cluster__c`

- External Id: `ExtId__c` (in prod we generate a stable ExtId from the title/content)
- Other fields mirror the above (e.g., `PriorityScore__c`, `UniqueUsers__c`, etc.)

---

## 2) `cluster_trend.csv` — weekly mentions per theme

| Field | Type | Meaning / Use |
| --- | --- | --- |
| `ClusterId` | Text (FK → clusters.ClusterId) | Which theme |
| `WeekStart` | Date | Start of the week |
| `Mentions` | Number | # of messages mapped to this theme that week |

**Salesforce mapping (options):**

- EITHER compute trends on the fly in Tableau/Data Cloud,
- OR create a tiny roll-up object (e.g., `ClusterTrend__c`) if you want to persist per-week counts. (Optional for MVP.)

---

## 3) `feedback.csv` — raw requests/messages

| Field | Type | Meaning / Use |
| --- | --- | --- |
| `FeedbackId` | Text (PK) | Unique row id for the message |
| `Source` | Text | `Slack`, `Forum`, `CRM` |
| `SourceId` | Text | Native source id (Slack TS, forum post id, case id). **Used for idempotent upsert** |
| `IngestedAt` | Date/Time | When we captured it |
| `Message` | Text (long) | The text users wrote |
| `ChannelOrTopic` | Text | Slack channel, forum category, CRM queue |
| `AuthorHash` | Text | Hashed author id (privacy) |
| `VIPFlag` | Boolean | True if from VIP/paying/high-tier account |

**Salesforce mapping:** `Feedback__c`

- External Id: `SourceId__c` (prevents duplicates)
- Other fields map 1:1 (e.g., `Message__c`, `VIPFlag__c`)

---

## 4) `cluster_members.csv` — junction linking feedback ↔ clusters

| Field | Type | Meaning / Use |
| --- | --- | --- |
| `ClusterMemberId` | Text (PK) | Unique id for the link row |
| `ClusterId` | Text (FK → clusters.ClusterId) | The theme |
| `FeedbackId` | Text (FK → feedback.FeedbackId) | The message |
| `Similarity` | Number (0–1) | Cosine similarity of message to theme |
| `Duplicate` | Boolean | True if near-duplicate |
| `Role` | Text | `Primary` / `Secondary` / `Duplicate` |

**Salesforce mapping:** `ClusterMember__c`

- External Id: `ExtId__c` (in prod we use `ClusterExtId::FeedbackSourceId`)
- Lookups: `Cluster__c` ↔ `Feedback__c`
- Other fields map 1:1 (`Similarity__c`, `Duplicate__c`, `Role__c`)

---

## 5) (Optional) `Score` object (Salesforce only)

If you want a **history** of scoring runs:

- `Score__c`: `Cluster__c` (lookup), `ScoreValue__c` (number), `WeightsJSON__c` (long text), `ComputedAt__c` (datetime)
    
    This is not a CSV in your starter set; introduce it only if you need auditability of how scores changed over time.
    

---

# Relationships (how to link them)

**In files / Tableau / Data Cloud ERD**

```
clusters (1) ──< cluster_trend (many)
    │
    └──< cluster_members (many) >── feedback (1)

```

- **clusters.ClusterId = cluster_trend.ClusterId**
- **clusters.ClusterId = cluster_members.ClusterId**
- **feedback.FeedbackId = cluster_members.FeedbackId**

**In Salesforce / Data Cloud model**

```
Cluster__c (1) ──< ClusterMember__c (many)
Feedback__c (1) ──< ClusterMember__c (many)

```

- Link by **lookups**: `ClusterMember__c.Cluster__c` → `Cluster__c.Id`, `ClusterMember__c.Feedback__c` → `Feedback__c.Id`.

> Weekly trend can be computed as an aggregation of ClusterMember__c by week on Feedback__c.IngestedAt__c, or persisted in a ClusterTrend__c object if you prefer durable time series.

# Note

- We have **five logical objects**: `Feedback`, `Cluster`, `Cluster Member`, `Audit Log`, `Score`.
- **Data Cloud** is the bridge for analytics—create a **data stream** per object, then **use in Tableau Next**.
- **Keys & Joins**: `Cluster` ↔ `Cluster Member` (1→many), `Feedback` ↔ `Cluster Member` (1→many).
- **PriorityScore** is explainable (frequency, recency, VIP%); `Confidence` tells the PM where to double-check.
- **VIPFlag** helps leadership focus; **AuditLog** records manual overrides for transparency.
- **.tds files** are local helpers; in prod we connect Tableau to **Data Cloud** (or directly to Salesforce).
---
