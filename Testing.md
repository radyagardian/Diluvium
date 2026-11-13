### Testing Documentation

---

Based on your repository state and codebase, the prototype currently has functional components ready across the Admin Dashboard, Data Ingestion, and the FastMCP Tool Server:

| Component | Available Feature | Implementation Status |
| :--- | :--- | :--- |
| **Admin Web GUI** | Supabase Session Authentication | **Live**: Validates email/password against Supabase Auth, handles invalid credentials, issues JWT bearer tokens, and supports logout. |
| **Admin Web GUI** | Pipeline & Telemetry Monitoring Display | **Live UI**: Renders telemetry parameters (Manggarai/Katulampa gate levels, BMKG ingestion status, token quota, Siaga level) via Jinja2 templates. |
| **Admin Web GUI** | Channel Diagnostic Trigger (`POST /api/admin/test-alert`) | **Live Endpoint**: Token-protected endpoint returning mock delivery verification for Telegram/Discord webhooks. |
| **Admin Web GUI** | Emergency Non-AI Fallback Toggle (`POST /api/admin/override`) | **Live Endpoint**: Token-protected endpoint switching UI status to fallback mode. |
| **FastMCP Server** | BMKG Weather & Telemetry Fetcher (`get_specific_area_weather`) | **Live Backend**: Live async network query to Data Terbuka BMKG via `BMKGClient` with local caching. |
| **FastMCP Server** | Jakarta Watchlist Aggregation (`get_jakarta_flood_watchlist_summary`) | **Live Backend**: Concurrently polls flood-prone kelurahan across DKI Jakarta. |
| **FastMCP Server** | Hydrological Calculation Tool (`calculate_flood_risk`) | **Mock / Contract**: Returns structured prediction payload validated against Pydantic schemas. |
| **FastMCP Server** | Alert Dispatch Tool (`verify_and_dispatch_alert`) | **Mock / Contract**: Returns verification receipt for downstream bot dispatchers. |

---

### Testing Guide

#### 1. Start the Admin Dashboard Server
Make sure your Python virtual environment is activated in your terminal:

```powershell
uvicorn src.gui.admin_web:app --reload
```

Open your browser and navigate to:
```text
http://127.0.0.1:8000
```

![image](https://hackmd.io/_uploads/rJokPropGe.png)


---

#### 2. Test Admin Authentication & Access Guardrails
1. **Test Invalid Login:**
   * Enter a bogus email/password (e.g., `test@wrong.com` / `wrongpass`) and click **Login Dashboard**.
   * **Expected Result:** A popup alert appears stating `"Login failed: Invalid email or password."`, keeping the dashboard blurred/covered.
![image](https://hackmd.io/_uploads/rJhMDrs6Ge.png)

2. **Test Valid Login:**
   * Enter your registered Supabase credentials:
     * **Email:** `admin@diluvium.local`
     * **Password:** `somppassword`
   * Click **Login Dashboard**.
   * **Expected Result:** The overlay clears, revealing the dashboard. The status log at the bottom updates to:
     ```text
     > Administrator authenticated successfully.
     ```
   * *Under the hood:* Check browser DevTools (`F12` -> **Application** -> **Local Storage**) to verify `supabase_token` is saved.
![image](https://hackmd.io/_uploads/SJ-SvSjpGx.png)

3. **Test Session Persistence & Logout:**
   * Refresh the page (`F5`). The login overlay should stay hidden because the token is cached.
   * Click the **Logout** button in the header. The token will clear from `localStorage`, and the overlay reappears.
![image](https://hackmd.io/_uploads/B1I0CSsTfx.png)


Logging: 
![image](https://hackmd.io/_uploads/SJABwBipfe.png)



---

#### 3. Test Manual Overrides & Diagnostics (With Auth Headers)
Log back in and test the control buttons in **Section 2 (Manual Overrides & Channel Diagnostics)**:

1. **Trigger Test Alert (Telegram / Discord):**
   * Click **Trigger Test Alert (Telegram / Discord)**.
   * **Expected Result:** The audit box updates to:
     ```text
     > [DIAGNOSTIC] Delivery verified to Telegram (@BotFather) & Discord Webhook (200 OK).
     ```
     ![image](https://hackmd.io/_uploads/H11tPHiTMx.png)

     
2. **Emergency Fallback Switch:**
   * Click **Emergency Toggle: Non-AI Fallback**.
   * Click **OK** on the browser confirmation modal.
   * **Expected Result:** The *AI Orchestrator Status* card updates dynamically to `Offline (Fallback Active)`, and the audit box updates to:
     ```text
     > [OVERRIDE] Mode switched to Non-AI Hardcoded Fallback Script!
     ```
     ![image](https://hackmd.io/_uploads/HkFcvHs6Gl.png)

3. **Verify Header Protection (API Security):**
   * Open DevTools Console (`F12`) and run a request without a token:
     ```javascript
     fetch('/api/admin/override', { method: 'POST' }).then(r => console.log(r.status));
     ```
   * **Expected Result:** Status returns `422 Unprocessable Entity` or `401 Unauthorized`, proving unauthenticated actors cannot trigger backend controls.
   ![image](https://hackmd.io/_uploads/HJT6wSj6Gx.png)


---

#### 4. Test the Live Ingestion & MCP Tools via Official MCP Inspector
To test the real-time BMKG weather retrieval and calculation mock tools outside the browser GUI:

1. BPBD Client Test: 
`python -m src.ingestion.bpbd_client`

2. BMKG Server Test: 
`python -m src.ingestion.bmkg_client`

3. Clean Dataset to JSON: 
`python src/calculation/engine.py` 
