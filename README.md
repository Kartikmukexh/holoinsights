# HoloInsights

**AI-assisted mixed reality business intelligence dashboard**  
**RMIT University | Mixed Reality | MR Group 2 | Final prototype (Milestone 3)**

**Prototype deployment and headset test:** 16 October 2026  
**Tested headset:** Meta Quest 3S  
**Repository:** https://github.com/Kartikmukexh/holoinsights  
**Main development branch:** `main`

## Overview

HoloInsights explores a more interactive way to understand business sales. Instead of relying only on flat dashboards, a user can view a three-dimensional sales chart in a headset, change the region or quarter with a controller, and read a short sales insight. The project also includes a browser dashboard with voice input and spoken feedback.

Two prototypes were developed during the project:

1. **Unity mixed reality prototype**, the main final headset demonstration. It runs as an Android application on Meta Quest 3S and includes a spatial dashboard with controller interactions.
2. **Three.js browser prototype**, used to explore 3D charts, question buttons, microphone input and spoken responses on a desktop browser. Its 3D view is not an immersive WebXR session.

A FastAPI backend provides sales data, summaries and optional AI-generated insights. The Unity headset build has an offline sales dataset so the dashboard still works when the database or network is unavailable.

## Final prototype status

| Component | Current status |
| --- | --- |
| Quest 3S Android application | Built, installed and tested on 16 October 2026 |
| Three-dimensional sales bars and value labels | Working |
| Switch region, quarter and dataset with Quest controller | Working; the headset test used the controller grip to activate selections |
| Meta Quest passthrough | Observed during headset testing; results may depend on headset configuration |
| Unity offline sample data | Working and enabled by default on Android |
| FastAPI endpoints | Tested locally |
| Gemini insight through FastAPI to the Quest | Successfully demonstrated during testing; later affected by API quota limits |
| Data-derived insight fallback | Working when a live AI response is not available |
| Azure SQL connection | Supported by backend code; not successfully connected during the final Quest test due to firewall/IP access restrictions |
| Browser dashboard, buttons and Web Speech API | Implemented for desktop browsers; speech support depends on the browser |
| Native Unity voice input and text-to-speech | Not implemented in the final headset application |
| Immersive browser WebXR | Not implemented |
| Power BI report | Not built; related planning and setup work is documented in the project |

**Important distinction:** The final Quest chart was demonstrated using **12 built-in sample sales records** (Products A, B and C; North and South; Q1 and Q2). A live Gemini insight was demonstrated on the headset, but the final recorded session may display the local **data-derived summary** when the external AI service is unavailable. The Quest data is not presented as live Azure SQL data.

## Features

### Unity / Meta Quest 3S

- World-space dashboard with three 3D bars and revenue labels.
- Four filter combinations: North Q1, South Q1, North Q2 and South Q2.
- **Switch Region**, **Switch Quarter** and **Switch Dataset** buttons.
- Local sales summary that updates with the selected values.
- Optional AI insight request to the FastAPI `/api/insight` endpoint.
- Automatic retention of the local text when the live AI response is unavailable.
- Offline sales-data fallback, with no database or internet required for the chart itself.
- Desktop preview scene for development without a headset.

**AI question limitation:** The current Unity AI client asks the same overall question, "Which region is underperforming?", after chart updates. Its AI response is not individually filtered to the currently selected region and quarter.

### Browser / Three.js

- KPI cards, animated 3D bar chart and chart labels.
- Three business-question buttons and a dynamic insight panel.
- Browser microphone input and speech synthesis, where supported.
- Backend-backed summaries and data-source labelling when the API is available.
- Sample values and a local presentation fallback for development.

The browser page is a **desktop Three.js/WebGL prototype**, not a completed immersive WebXR application.

## Technology stack

| Layer | Technology |
| --- | --- |
| Mixed reality | Unity **6000.6.1f1** (Unity 6.6), C#, Unity Mixed Reality template |
| XR | OpenXR, Meta OpenXR, XR Interaction Toolkit, XR Hands, AR Foundation |
| Rendering and UI | Universal Render Pipeline, TextMeshPro |
| Headset build | Android, IL2CPP, ARM64; Meta Quest 3S |
| Web | HTML, CSS, JavaScript, Three.js r128, Web Speech API |
| API | Python, FastAPI, Uvicorn, requests, python-dotenv |
| Database option | Microsoft Azure SQL, pyodbc and Microsoft ODBC Driver 18 for SQL Server |
| AI option | Gemini or an OpenAI-compatible service such as GitHub Models |
| Version control | Git and GitHub |

The exact Unity package dependencies and versions are listed in `unity/Packages/manifest.json`. Python dependencies are listed in `backend/requirements.txt`.

## Repository layout

```text
holoinsights/
├── backend/
│   ├── main.py                 # FastAPI routes, summaries and AI integration
│   ├── requirements.txt
│   ├── .env.example            # Configuration template, no real credentials
│   └── sample_sales.json       # Sample dataset for the API
├── web/
│   └── index.html              # Three.js browser prototype
├── unity/
│   ├── Assets/
│   │   ├── Scenes/
│   │   │   ├── HoloInsightsScene.unity
│   │   │   └── HoloInsightsQuestScene.unity
│   │   └── Scripts/
│   │       ├── DashboardController.cs
│   │       ├── SalesDataClient.cs
│   │       └── AIInsightClient.cs
│   ├── Packages/
│   └── ProjectSettings/
├── docs/
└── README.md
```

Generated APKs in `QuestBuilds/`, headset recordings in `QuestRecordings/`, virtual environments and Unity cache files are excluded from Git. They are **not downloaded by cloning this repository**.

## Quick start: Backend using sample data

This is the simplest way for a new user to reproduce the API without Azure SQL or an AI account. Run these commands from the cloned repository root.

**Requirements:** Python 3.13 (the development environment used Python 3.13), pip and Git. Microsoft ODBC Driver 18 for SQL Server is required for Azure SQL connectivity; the backend imports `pyodbc`, so install the driver when testing that integration.

### 1. Clone the repository

```powershell
git clone https://github.com/Kartikmukexh/holoinsights.git
cd holoinsights
```

### 2. Create a Python environment and install packages (PowerShell)

```powershell
python -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

On macOS or Linux, activate an equivalent virtual environment and use `python -m pip install -r backend/requirements.txt`.

### 3. Configure sample data mode

Copy `backend/.env.example` to `backend/.env`. The example file contains placeholder Azure credentials. **Clear the four `AZURE_SQL_*` values** to use sample data. The database selection code deliberately uses the sample file only when the Azure fields are empty.

A minimal sample-only `.env` is:

```dotenv
AZURE_SQL_SERVER=
AZURE_SQL_DATABASE=
AZURE_SQL_USERNAME=
AZURE_SQL_PASSWORD=
LLM_PROVIDER=gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3-flash-preview
```

With no `GEMINI_API_KEY`, the insight endpoint uses a data-derived response. No live AI subscription is required for this mode.

**Never upload your real `.env` file, API keys or passwords.**

### 4. Start FastAPI

From the repository root:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open:

- http://127.0.0.1:8000/ - backend status
- http://127.0.0.1:8000/docs - interactive API documentation
- http://127.0.0.1:8000/api/sales-data - sample sales records
- http://127.0.0.1:8000/api/summary - quarterly and regional summary
- http://127.0.0.1:8000/api/insight?question=Which%20region%20is%20underperforming - an AI answer when available, otherwise a rule-based answer

Expected in sample-only mode: `azure_configured: false`. `llm_configured` is `false` without an AI API key and `true` when an AI provider is configured.

## Optional: Live AI configuration

Edit `backend/.env` and restart Uvicorn after changes.

**Gemini example:**

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=YOUR_OWN_KEY
GEMINI_MODEL=gemini-3-flash-preview
```

**OpenAI-compatible provider example (including GitHub Models):**

```dotenv
LLM_PROVIDER=openai
LLM_ENDPOINT=https://models.github.ai/inference/chat/completions
LLM_TOKEN=YOUR_OWN_TOKEN
LLM_MODEL=openai/gpt-4.1-mini
```

Use a model your account is permitted to call. Model availability, quotas, request limits and billing requirements change over time. A configured API key does not guarantee that a request succeeds. The backend returns a **rule-based** response when the AI provider cannot be reached.

The `/api/insight` response has an `insight_type` field: `llm` for an AI-generated response or `rule_based` for the backend fallback. Its `source` field identifies the sales data source, such as `sample` or `azure`. This is different from the Unity on-screen label `offline_sample`.

## Optional: Azure SQL configuration

The backend expects a queryable Azure SQL view named `SalesData` with these fields:

```text
product_name | region | quarter | revenue
```

Configure the four `AZURE_SQL_*` variables in `backend/.env` and install **Microsoft ODBC Driver 18 for SQL Server**. Your network's public IP must be allowed by the Azure SQL server firewall, and the database credentials must have permission to read the view.

```dotenv
AZURE_SQL_SERVER=YOUR_SERVER.database.windows.net
AZURE_SQL_DATABASE=YOUR_DATABASE
AZURE_SQL_USERNAME=YOUR_USERNAME
AZURE_SQL_PASSWORD=YOUR_PASSWORD
```

Restart the API and check `/api/test-db` and `/api/sales-data`. **Important:** When all four Azure settings are populated, a failed database connection returns an error rather than automatically switching to sample data. To demonstrate the API without Azure access, clear those four settings again.

Kartik's database and data-import work is described in the project documentation. The final on-headset demonstration did not verify the Azure SQL connection, and the Azure dataset is not required to run the sample-data demonstration.

## Run the browser dashboard

1. Start the FastAPI backend if you want API-backed values or responses.
2. Open `web/index.html` with **VS Code Live Server**, or use a simple static HTTP server.
3. Use Chrome or Edge for the best chance of browser speech recognition support.
4. Use the question buttons or microphone and watch the chart and insight area update.

Example using Python from the repository root:

```powershell
python -m http.server 5500
```

Then open http://127.0.0.1:5500/web/index.html . The page loads Three.js from a CDN, so internet access is needed for that library. By default, the page targets `http://127.0.0.1:8000` for API requests; its `?api=` query parameter can override the API base URL.

## Run the Unity desktop preview

1. Install Unity Hub and **Unity Editor 6000.6.1f1** with the appropriate project modules.
2. In Unity Hub select **Add project from disk** and choose the repository's `unity` folder, not the repository root.
3. Allow Unity to import the project and packages. The first import can take several minutes.
4. Open `Assets/Scenes/HoloInsightsScene.unity`.
5. Select the **Game** tab and enter Play mode.
6. Click the Game view and press **Space** to switch the displayed dataset.

The editor scene is for desktop development. For native headset operation, use the Quest scene and Android build instructions below.

## Build and test on Meta Quest 3S

**Requirements:** Meta Quest 3S, USB-C data cable, Unity Android Build Support (Android SDK, NDK and OpenJDK), the correct XR packages from `unity/Packages/manifest.json`, and permission to enable Quest developer/USB debugging features.

1. In Unity Hub open the `unity` project with **6000.6.1f1**.
2. Open `Assets/Scenes/HoloInsightsQuestScene.unity`.
3. Open **File > Build Profiles**. Use or activate the project's **HoloInsights Quest** Android profile if it is present. Confirm that the intended Quest scene is the scene included in the Android build.
4. Confirm OpenXR/Meta Quest settings, Android ARM64 and IL2CPP. The tested setup used Android minimum and target API level 34. Review the project's actual Player Settings if your Unity installation differs.
5. Connect the headset by USB, enable USB debugging on the device and check that ADB recognises it.
6. Build an APK to a local folder such as `QuestBuilds/` (ignored by Git). You may choose your own APK filename.
7. Install and launch the APK using the installed Android SDK's `adb` command:

```powershell
adb devices
adb install -r .\QuestBuilds\HoloInsightsQuest.apk
adb shell monkey -p com.DefaultCompany.MixedRealityTemplate -c android.intent.category.LAUNCHER 1
```

The tested Android package identifier was `com.DefaultCompany.MixedRealityTemplate`. Check the current Unity Player Settings if you change the application identifier before building.

**Quest interactions:** Use the right controller to aim at the dashboard buttons; the tested configuration selected with the **grip** control. Switch Region, Quarter and Dataset should update the three bars and their local insight. The headset build is configured to use offline sales data by default, so it can operate without the laptop backend.

### Optional USB-connected live AI on Quest

The Quest can contact FastAPI through USB using ADB reverse port forwarding. This is useful during lab testing and avoids requiring direct network access between the headset and laptop.

1. Start FastAPI on the laptop at `127.0.0.1:8000` with a working AI provider configured.
2. Keep the USB cable attached and authorized.
3. Run:

```powershell
adb reverse tcp:8000 tcp:8000
adb reverse --list
```

4. Launch HoloInsights and wait for the AI insight text to appear. The Unity AI URL is `http://127.0.0.1:8000/api/insight`, which reaches the laptop over the reverse USB connection.

ADB reverse forwarding is **temporary** and may need to be repeated after disconnecting the headset. The Gemini service may also fail due to rate limits or quota. If a valid `llm` result does not arrive, the Unity dashboard retains its data-derived local summary.

**Important:** Quest chart values use `SalesDataClient.useOfflineDataOnAndroid = true` in the tested configuration. The chart and the optional AI summary therefore do not necessarily use the same data source or a filtered dataset. Do not describe this demonstration as live Azure data powering the Quest chart.

## API reference

| Method and endpoint | Purpose |
| --- | --- |
| `GET /` | API health and configuration flags (no secrets) |
| `GET /api/test-db` | Azure SQL connectivity test |
| `GET /api/sales-data` | Sales records and their source |
| `GET /api/summary` | Total revenue, quarterly changes and regional figures |
| `GET /api/insight?question=...` | Generates an AI answer when possible or a rule-based answer |
| `GET /docs` | Interactive Swagger documentation |

## Testing and known limitations

### Confirmed in final headset testing (16 October 2026)

- Android APK installed and launched on Meta Quest 3S.
- Dashboard bars, values and the three interaction buttons responded to Quest controller input.
- Passthrough and the dashboard were visible together during a successful test.
- A real Gemini-generated insight appeared on the dashboard during one test.
- The fallback dashboard continued to work after the AI provider's free-tier quota was exceeded.
- Headset recordings were captured for the assignment demonstration.

### Limitations and next steps

- The native Quest app does not implement microphone questions or spoken responses.
- The headset sales chart uses its built-in sample records by default, not live Azure SQL data.
- The Quest's fixed AI question does not follow the currently selected dataset.
- AI text may exceed the space allocated above the dashboard buttons.
- AI availability depends on network connectivity, credentials, rate limits and provider capacity.
- Passthrough and boundary appearance can vary with device and room setup.
- No formal usability study was conducted.
- The browser prototype has no immersive WebXR session.
- Additional product categories, data-driven questions and more complete Azure/Power BI integration remain potential extensions.

These are prototype constraints, not features that should be represented as completed.

## Development history

HoloInsights progressed through three milestones:

| Milestone | Outcome |
| --- | --- |
| Milestone 1 | Concept, initial architecture and project planning |
| Milestone 2 | Browser and Unity desktop prototypes, with basic interactions and example insights |
| Milestone 3 | Native Quest build, controller-driven dashboard, FastAPI integration, live Gemini proof of concept, fallback testing and headset recording |

The GitHub `main` branch contains incremental commits for browser interactions, Unity dashboard development, Quest deployment, API integration and AI insight support. Review the full [commit history](https://github.com/Kartikmukexh/holoinsights/commits/main) for a dated record of progress.

## Team and GitHub contributions

| Member | Role and contributions | GitHub |
| --- | --- | --- |
| **Kartik Mukesh Sundaram** | Project concept and planning; data architecture and Azure SQL work; backend and API work; AI provider integration and fallback logic; Power BI-related documentation; group report and presentation drafts. | [@Kartikmukexh](https://github.com/Kartikmukexh) |
| **Phavan Kumaar Janakiraman Suresh** | Browser dashboard and Three.js interactions; speech UI; Unity scene, chart and filters; Quest deployment and controller interaction; API-to-Unity integration; headset testing, recordings and GitHub documentation; report and presentation review and revision. | [@phavan1](https://github.com/phavan1) |

Both members contributed to design decisions, integration and final assessment preparation. Contributions are also visible through [repository commits](https://github.com/Kartikmukexh/holoinsights/commits/main); individual commit authorship may reflect the account used for each commit. The submitted work uses `main` as the shared integration branch.

## Academic context

This is an RMIT Mixed Reality coursework prototype developed for educational and demonstration purposes. The sample sales data is illustrative. The repository does not provide or require private API keys, database passwords, university headset recordings or generated APK files.
