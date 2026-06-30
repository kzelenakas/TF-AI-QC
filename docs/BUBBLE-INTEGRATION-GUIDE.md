# TF AI-QC — Bubble Frontend Integration Guide

## Free Plan Note

The Bubble free plan works fine for testing. Two things to know:
- File uploads via the API Connector are supported, but Bubble’s free plan caps file storage.  
  Upload the file **directly to your FastAPI backend** (which stores it in R2) — do NOT use Bubble’s file uploader for appraisal reports. This keeps NPI out of Bubble’s storage entirely.
- You’ll use `https://your-app.bubbleapps.io` as the domain. Set this in your Railway `CORS_ORIGINS` variable.

---

## Step 1: API Connector Plugin Setup

In your Bubble app: **Plugins → Add Plugin → API Connector**

### Base configuration

| Field | Value |
|---|---|
| API Name | `TF AI-QC` |
| Authentication | `Private key in header` |
| Key name | `Authorization` |
| Key value | `Bearer <your-bubble-user-token>` (set dynamically per user — see Auth section) |
| Base URL | `https://your-service.railway.app` |

> **Auth pattern**: Do NOT hardcode a token here. In each API call, you’ll pass the token dynamically from the logged-in user’s session. See Step 3.

---

## Step 2: API Calls — Full Configuration

Add each call in the API Connector. Mark calls as **“Use as Data”** where noted (returns data Bubble can display). Others are **“Action”** calls (triggered by workflows).

---

### CALL 1 — Upload Report
**Name**: `upload_report`  
**Use as**: Action  
**Method**: POST  
**URL**: `https://your-service.railway.app/reports`  
**Headers**:
```
Authorization: Bearer <token>   (dynamic, from Current User's auth token)
```
**Body type**: Form data (multipart)  
**Body fields**:
```
file   [file]   (the File Uploader element's value)
```
**Returns** (initialize with a test call):
```json
{
  "report_id": "uuid",
  "status": "submitted",
  "message": "Report queued for QC."
}
```

---

### CALL 2 — List Reports
**Name**: `list_reports`  
**Use as**: Data  
**Method**: GET  
**URL**: `https://your-service.railway.app/reports`  
**Headers**: `Authorization: Bearer <token>`  
**Query params** (optional):
```
status     text    (filter: submitted, qc_complete, approved, revision_requested)
page       number  (default 1)
page_size  number  (default 20)
```
**Returns**:
```json
[
  {
    "id": "uuid",
    "status": "qc_complete",
    "file_type": "xml",
    "original_filename": "1004_report.xml",
    "property_address": "123 Main St, Anytown CA",
    "run_number": 1,
    "latest_qc": {
      "pass_fail": true,
      "quality_score": 78,
      "error_count": 0,
      "warning_count": 2
    },
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:32:00Z"
  }
]
```

---

### CALL 3 — Get Report Detail
**Name**: `get_report`  
**Use as**: Data  
**Method**: GET  
**URL**: `https://your-service.railway.app/reports/<report_id>`  
**Path param**: `report_id` (text, dynamic)  
**Returns**:
```json
{
  "id": "uuid",
  "status": "qc_complete",
  "property_address": "123 Main St",
  "run_number": 1,
  "latest_qc": {
    "pass_fail": true,
    "quality_score": 78,
    "score_breakdown": {
      "comparables": 24,
      "adjustments": 20,
      "market_analysis": 15,
      "narrative": 11,
      "reconciliation": 8
    },
    "error_flags": [],
    "warning_flags": [
      {
        "rule_code": "UAD-006",
        "severity": "warning",
        "field_name": "comp_1_sale_date",
        "message": "Comparable sale date is 14 months old"
      }
    ]
  }
}
```

---

### CALL 4 — Get Report File URL (presigned)
**Name**: `get_report_file_url`  
**Use as**: Action  
**Method**: GET  
**URL**: `https://your-service.railway.app/reports/<report_id>/file`  
**Returns**:
```json
{
  "url": "https://r2.example.com/signed-url",
  "expires_in": 900
}
```
> Use the returned URL to open the file in a new tab. Do NOT store the URL — it expires in 15 minutes.

---

### CALL 5 — Approve Report
**Name**: `approve_report`  
**Use as**: Action  
**Method**: POST  
**URL**: `https://your-service.railway.app/reports/<report_id>/approve`  
**Returns**:
```json
{
  "report_id": "uuid",
  "status": "approved",
  "message": "Report approved."
}
```

---

### CALL 6 — Request Revision
**Name**: `request_revision`  
**Use as**: Action  
**Method**: POST  
**URL**: `https://your-service.railway.app/reports/<report_id>/request-revision`  
**Body type**: JSON  
**Body**:
```json
{
  "notes": "<revision_notes_input value>"
}
```
**Returns**:
```json
{
  "revision_id": "uuid",
  "report_id": "uuid",
  "status": "revision_requested",
  "message": "Revision request created."
}
```

---

### CALL 7 — Get Revisions
**Name**: `list_revisions`  
**Use as**: Data  
**Method**: GET  
**URL**: `https://your-service.railway.app/reports/<report_id>/revisions`  
**Returns**: list of revision objects with `notes`, `status`, `run_number`, `responses`

---

### CALL 8 — Respond to Revision
**Name**: `respond_revision`  
**Use as**: Action  
**Method**: POST  
**URL**: `https://your-service.railway.app/revisions/<revision_id>/respond`  
**Body**:
```json
{
  "response_text": "<response_input value>"
}
```

---

### CALL 9 — Resubmit Report
**Name**: `resubmit_report`  
**Use as**: Action  
**Method**: POST  
**URL**: `https://your-service.railway.app/reports/<report_id>/resubmit`  
**Body type**: Form data (multipart)  
**Body fields**: `file` [file]

---

### CALL 10 — My Coaching Profile
**Name**: `get_my_coaching`  
**Use as**: Data  
**Method**: GET  
**URL**: `https://your-service.railway.app/coaching/me`  
**Query params**: `lookback_days` (number, optional, default 90)

---

### CALL 11 — Appraiser List (Reviewer/Admin)
**Name**: `list_appraisers`  
**Use as**: Data  
**Method**: GET  
**URL**: `https://your-service.railway.app/coaching/appraisers`

---

### CALL 12 — Appraiser Coaching Profile (Reviewer/Admin)
**Name**: `get_appraiser_coaching`  
**Use as**: Data  
**Method**: GET  
**URL**: `https://your-service.railway.app/coaching/appraisers/<appraiser_id>`

---

### CALL 13 — Coaching Recommendations
**Name**: `get_recommendations`  
**Use as**: Data  
**Method**: GET  
**URL**: `https://your-service.railway.app/coaching/appraisers/<appraiser_id>/recommendations`

---

### CALL 14 — List Rules (Reviewer/Admin)
**Name**: `list_rules`  
**Use as**: Data  
**Method**: GET  
**URL**: `https://your-service.railway.app/rules`

---

### CALL 15 — Toggle Rule (Admin)
**Name**: `toggle_rule`  
**Use as**: Action  
**Method**: PATCH  
**URL**: `https://your-service.railway.app/rules/<rule_code>/enable`  
*(swap `enable` → `disable` for the disable action)*

---

## Step 3: Auth Flow

TF AI-QC uses Bubble’s native auth. On login, Bubble issues the user a session token. You pass this token as the `Authorization: Bearer` header on every API call.

### How to pass the token dynamically in Bubble

In each API Connector call that requires auth:

1. In the API call definition, set the `Authorization` header value to `Bearer ` (with the space)
2. Mark it as **private** = No (so it can be set dynamically)
3. In your workflow action that calls the API, set:
   ```
   Authorization: "Bearer " + Current User's token
   ```
   Where `Current User's token` comes from Bubble’s `Current User > Authentication token`

### Backend token verification

The FastAPI backend reads the Bubble JWT, verifies it with `BUBBLE_AUTH_SECRET`, and extracts `user_id` (= Bubble user’s unique ID) and `role` (a custom field you set on the Bubble User data type).

**Required Bubble User fields to add**:

| Field name | Type | Purpose |
|---|---|---|
| `role` | text | `appraiser`, `reviewer`, or `admin` |
| `qc_user_id` | text | Backend’s internal user UUID (returned after first upload) |

The backend creates a local User record on first upload, keyed by `bubble_user_id`. No manual sync needed.

---

## Step 4: Page Structure

### Recommended pages

| Page | Roles | Purpose |
|---|---|---|
| `index` (login) | all | Bubble native login/signup |
| `dashboard` | appraiser | Upload reports, view own report list |
| `report-detail` | all | Report flags, QC score, approve/revision actions |
| `coaching` | appraiser | Own coaching profile + recommendations |
| `reviewer-queue` | reviewer, admin | All reports pending review |
| `coaching-admin` | reviewer, admin | Appraiser roster + coaching profiles |
| `rules-admin` | admin | Enable/disable rules, adjust thresholds |

### Page routing

Use a `Header` reusable element with conditional visibility:
- Show **Reviewer Queue** link if `Current User’s role = "reviewer"` or `"admin"`
- Show **Rules Admin** link if `Current User’s role = "admin"`
- Show **Coaching** for all logged-in users

---

## Step 5: Key Workflows

### Upload Report (Dashboard page)

```
Element: File Uploader (accept: .xml, .pdf)
Button: “Submit for QC”

Workflow:
1. Only when: File Uploader’s value is not empty
2. Action: API Connector → upload_report
   - file: File Uploader’s value
   - Authorization: "Bearer " + Current User's token
3. Action: Set state “last_upload_status” = Result of Step 2’s status
4. Action: Show alert “Report submitted for QC review.”
5. Action: Navigate to page “report-detail” with data = Result of Step 2’s report_id
```

### Poll for QC complete (Report Detail page)

QC runs async (backend returns 202 on upload). The report-detail page needs to poll until status changes from `qc_running` to `qc_complete`.

```
Page load workflow:
1. Schedule API workflow to run in 5 seconds
   - API call: get_report (report_id from URL param)
   - If result’s status = “qc_running”: schedule again in 5 seconds
   - If result’s status = “qc_complete” or “approved”: refresh page data
```

### Approve Report (Report Detail — reviewer only)

```
Button: “Approve” (visible only if Current User’s role = reviewer/admin AND report status = qc_complete)

Workflow:
1. Action: API Connector → approve_report
   - report_id: Current Page’s report_id
   - Authorization: "Bearer " + Current User's token
2. Action: Refresh data for the report repeating group
3. Action: Show alert “Report approved. Appraiser has been notified.”
```

### Request Revision (Report Detail — reviewer only)

```
Elements:
- Multiline input: “revision_notes_input”
- Button: “Request Revision”
- Popup: “revision-popup” (contains the multiline input + button)

Workflow:
1. Show popup “revision-popup”
2. On button click:
   a. API Connector → request_revision
      - report_id: Current Page’s report_id
      - notes: revision_notes_input’s value
   b. Close popup
   c. Refresh report data
   d. Alert “Revision requested. Appraiser notified.”
```

### Display QC Flags (Report Detail)

```
Repeating Group: “error_flags”
  Type of content: API Connector → get_report (use “latest_qc > error_flags”)
  
Each cell displays:
  - Rule code (text)
  - Severity badge (conditional color: red=error, yellow=warning, blue=info)
  - Field name
  - Message

Repeating Group: “warning_flags” (same pattern, different data field)
```

### Quality Score Display

```
Text element: Current Page Report’s latest_qc quality_score + ”/100”
Progress bar: Width = (quality_score / 100) * parent width
Color conditional:
  - Green: score >= 80
  - Yellow: 60-79
  - Red: < 60

Score Breakdown (5 categories):
  - Comparables: score_breakdown > comparables
  - Adjustments: score_breakdown > adjustments
  - Market Analysis: score_breakdown > market_analysis
  - Narrative: score_breakdown > narrative
  - Reconciliation: score_breakdown > reconciliation
```

### Coaching Dashboard (Appraiser)

```
On page load:
1. API Connector → get_my_coaching (lookback_days = 90)

Display:
- Pass Rate: result’s pass_rate_pct + “%”
- Avg Quality Score: result’s avg_quality_score
- Reports reviewed: result’s reports_in_window + “ reports (last 90 days)”

Repeating Group: Patterns
  - Filter: is_recurring = yes (show recurring at top)
  - Rule code + description
  - Fire rate: fire_rate_pct + “% of reports”
  - Badge: “Recurring Issue” if is_recurring = true
```

---

## Step 6: QCFlag Display Element

Build a reusable `QCFlag` group element:

```
Background color conditionals:
- severity = “error”: #FEE2E2 (red tint)
- severity = “warning”: #FEF3C7 (yellow tint)
- severity = “info”: #EFF6FF (blue tint)

Content:
- Left icon: ✕ (error) / ⚠ (warning) / ℹ (info)
- Rule code: bold, small caps
- Message: main body text
- Field name: muted, small
```

---

## Step 7: Reviewer Queue Page

```
Filter controls:
- Dropdown: Status (All / Pending QC / Needs Review / Approved / Revision Requested)
- Date picker: Submitted after

Repeating Group: list_reports
  Filtered by selected status
  Sorted by created_at desc

Each row:
- Property address (or “Processing...” if status = qc_running)
- Status badge (color-coded per status)
- Quality score / spinner
- Pass/Fail badge
- Error count chip
- “Review” button → navigate to report-detail
```

---

## Step 8: Rules Admin Page

```
Repeating Group: list_rules
  Each row:
  - Rule code + description text
  - Category badge
  - Severity badge
  - Toggle switch → workflow: if currently enabled, call disable; else call enable
  - “Edit Config” → popup with key/value inputs for threshold adjustment

Page condition: Redirect to index if Current User’s role ≠ “admin”
```

---

## Free Plan Limitations for Demo

| Limitation | Impact | Workaround |
|---|---|---|
| Bubble watermark | Visible in demo | Fine for internal review; remove on paid plan |
| `bubbleapps.io` domain | No custom domain | Set Railway CORS to this URL |
| 2 collaborators | Can’t add IT team yet | Upgrade to Starter ($32/mo) before dev handoff |
| API call limits | ~1,000/month free | More than enough for QC testing |
| No version control history | — | Use Bubble’s Dev vs Live version separation |

Recommend: Demo on free plan, then upgrade to Starter before IT takes it over.

---

## Railway Env Vars to Set After Bubble App Created

```
CORS_ORIGINS=https://your-app.bubbleapps.io
BUBBLE_AUTH_SECRET=<Bubble app Settings → API → Token secret>
BUBBLE_DATA_API_URL=https://your-app.bubbleapps.io/api/1.1/obj
BUBBLE_DATA_API_KEY=<Bubble private key>
```
