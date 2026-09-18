\# HoloInsights



HoloInsights is a Mixed Reality business intelligence prototype that explores how spatial data visualisation, voice interaction and AI-style insights could make business analytics more intuitive and immersive.



The intended HoloInsights experience allows a user to ask a business question, receive a natural-language insight, hear that insight through speech output, and view the relevant data as a spatial 3D visualisation.



This repository currently contains \*\*two parallel prototype tracks\*\*:



1\. A browser-based Three.js prototype being developed toward WebXR.

2\. A Unity/OpenXR prototype being developed toward a native Meta Quest mixed-reality experience.



Both approaches are currently at an intermediate prototype stage. The project is using both implementations to evaluate development complexity, interaction support, deployment requirements, headset compatibility and suitability for the final HoloInsights experience.



\---



\## Repository Structure



```text

holoinsights/

│

├── web/

│   └── index.html

│

├── unity/

│   ├── Assets/

│   ├── Packages/

│   └── ProjectSettings/

│

└── README.md

```



\### `web/`



Contains the browser-based HoloInsights prototype built with HTML, CSS, JavaScript and Three.js.



This prototype focuses on validating the HoloInsights interaction flow and 3D data visualisation experience.



\### `unity/`



Contains the Unity/OpenXR implementation of HoloInsights.



This prototype focuses on developing the project toward a headset-based mixed-reality application and provides a foundation for later Meta Quest testing.



\---



\# Prototype Track 1: Browser / WebXR Direction



The browser prototype demonstrates the core HoloInsights interaction loop using a standard desktop browser.



It currently uses \*\*Three.js for genuine WebGL-rendered 3D visualisation\*\*, but an immersive WebXR session has not yet been implemented. The browser prototype should therefore currently be considered a \*\*Three.js-based prototype being developed toward WebXR\*\*, rather than a completed WebXR application.



\## Current Browser Features



\- Dark business intelligence dashboard interface

\- Three headline KPI cards

\- Genuine Three.js 3D bar chart

\- Three switchable sample datasets

\- Animated 3D bar transitions

\- Floating value labels above chart bars

\- Three sample business-question buttons

\- Voice input using browser speech recognition

\- Text-to-speech narration

\- Dynamic insight panel

\- Simulated "Generating insight..." delay

\- Automatic slow 3D scene rotation

\- Subtle mouse-parallax camera movement

\- Responsive switching between visualisations and insights



\## Example Interaction



A user can select or speak questions such as:



\- "How did revenue perform this quarter?"

\- "Which region is underperforming?"

\- "What's the monthly trend?"



The prototype then:



1\. Selects the appropriate sample dataset.

2\. Updates the 3D chart.

3\. Displays a corresponding insight.

4\. Reads the insight aloud using text-to-speech.



\## Important AI Limitation



The current browser prototype does \*\*not\*\* use a live AI model, Azure OpenAI or another LLM service.



The current insight layer is a \*\*simulated AI implementation\*\*. Natural-language insight responses are pre-written and selected using simple keyword matching.



This allows the team to prototype and evaluate the intended interaction flow before introducing live backend and AI integration.



\## WebXR Status



The browser prototype does not currently create an immersive WebXR session.



Current work includes Three.js 3D rendering and browser interaction, while future WebXR work may include:



\- immersive AR session support

\- headset pose tracking

\- spatial placement of the dashboard

\- controller or hand interaction

\- Quest browser testing

\- spatial user-interface adaptation



\---



\# Prototype Track 2: Unity / OpenXR Direction



The second implementation is being developed using Unity as an alternative path toward a native mixed-reality experience.



The Unity prototype currently uses the Unity Mixed Reality project foundation and OpenXR-related project components.



\## Current Unity Features



\- World-space HoloInsights dashboard

\- Dark dashboard panel

\- Three 3D data bars

\- Product value labels

\- AI insight section

\- Desktop preview camera

\- Interactive dataset switching

\- Dynamically changing bar heights

\- Dynamically changing value labels

\- Dynamically changing insight text

\- Existing XR/OpenXR project foundation retained for later headset testing



\## Current Interaction



While running the Unity prototype in desktop preview mode:



```text

Press Space

```



to switch between two sample datasets.



\### Dataset 1



```text

A - 85

B - 62

C - 48

```



Insight:



```text

Product A leads at 85, outperforming Product B by 23

and Product C by 37.

```



\### Dataset 2



```text

A - 60

B - 78

C - 55

```



Insight:



```text

Product B now leads at 78, outperforming Product A by 18

and Product C by 23.

```



The associated 3D bars resize automatically when the dataset changes.



\---



\# Why Two Prototype Tracks?



The original HoloInsights project direction proposed a browser/WebXR approach because it offered a lightweight way to develop spatial interaction and 3D visualisation for a small team.



During development, the browser version made it possible to quickly test:



\- voice interaction

\- spoken insight output

\- dynamic data switching

\- 3D chart behaviour

\- dashboard layout

\- the question-to-insight interaction flow



A Unity/OpenXR implementation was then developed in parallel to investigate a more native route toward Meta Quest mixed reality.



The project has therefore not yet committed to one final implementation approach.



Instead, both approaches are being evaluated during prototyping.



Key evaluation criteria include:



\- development effort

\- ease of implementation for a small team

\- Meta Quest compatibility

\- spatial interaction support

\- voice integration

\- AI/backend integration complexity

\- deployment complexity

\- headset testing requirements

\- reliability of the final demonstration



Later development and headset testing will help determine whether one implementation should become the primary final delivery path or whether elements of both approaches should continue to be used.



\---



\# Technologies



\## Browser Prototype



\- HTML5

\- CSS3

\- Vanilla JavaScript

\- Three.js r128

\- WebGL

\- Web Speech API

&#x20; - Speech Recognition

&#x20; - Speech Synthesis

\- Git / GitHub



Three.js is currently loaded through a CDN.



No npm packages, Node.js build process or JavaScript framework are required.



\## Unity Prototype



\- Unity 6.6

\- C#

\- Unity Mixed Reality project/template components

\- OpenXR-related XR project components

\- TextMeshPro

\- Git / GitHub



Development has currently been performed using desktop preview because headset access is limited outside class.



\---



\# Running the Browser Prototype



\## Requirements



For the full browser experience, Google Chrome or Microsoft Edge is recommended.



Voice recognition may not work consistently in every browser.



\## Steps



1\. Clone the repository:



```bash

git clone https://github.com/Kartikmukexh/holoinsights.git

```



2\. Open the repository in Visual Studio Code.



3\. Open:



```text

web/index.html

```



4\. Run the page using the VS Code Live Server extension.



A typical development URL is:



```text

http://127.0.0.1:5500/web/index.html

```



5\. Use the sample question buttons or microphone control to interact with the prototype.



\### Browser Notes



\- Chrome and Edge are recommended for speech recognition.

\- Brave may require Google speech-recognition services to be enabled manually.

\- The Three.js CDN requires an internet connection when initially loading the library.



\---



\# Running the Unity Prototype



\## Recommended Unity Version



```text

Unity 6.6

6000.6.1f1

```



\## Steps



1\. Clone the repository.



2\. Open Unity Hub.



3\. Select \*\*Add project from disk\*\*.



4\. Select:



```text

holoinsights/unity

```



5\. Allow Unity to import and rebuild generated project files if necessary.



6\. Open the scene:



```text

Assets/Scenes/HoloInsightsScene.unity

```



7\. Select the \*\*Game\*\* tab.



8\. Enter Play mode.



9\. Click inside the Game window to give it keyboard focus.



10\. Press:



```text

Space

```



to switch between the two sample datasets.



\---



\# Current Prototype Limitations



The project is currently under active development.



Known limitations include:



\- no live Azure OpenAI integration

\- no live backend or database integration

\- no real business data

\- browser insights currently use simulated AI responses

\- immersive WebXR sessions are not yet implemented

\- Unity MR behaviour has not yet been fully tested on Meta Quest

\- browser speech recognition has browser-specific compatibility limitations

\- Unity voice interaction has not yet been implemented

\- advanced spatial controller/hand interaction is still pending

\- current data is sample data used for prototype demonstration



These limitations are part of the ongoing technical evaluation and will inform the next implementation stage.



\---



\# Current Development Status



\## Browser Track



Working:



\- 3D visualisation

\- interactive dataset switching

\- animated chart transitions

\- question buttons

\- voice input

\- text-to-speech

\- simulated AI-style insights

\- value labels

\- camera movement



Still to investigate:



\- immersive WebXR

\- headset testing

\- spatial controls

\- real AI/backend integration



\## Unity Track



Working:



\- Unity project foundation

\- world-space 3D dashboard

\- value labels

\- AI-style insight panel

\- dataset switching

\- dynamic bar resizing

\- desktop demonstration



Still to investigate:



\- Meta Quest testing

\- OpenXR headset interaction

\- controller/hand interaction

\- voice input/output

\- live backend/AI integration

\- final MR placement and usability



\---



\# Development Approach



HoloInsights is being developed iteratively.



Rather than selecting a final architecture before sufficient implementation experience is available, the team is using parallel prototypes to investigate the strengths and limitations of browser/WebXR and Unity/OpenXR development.



The next phase will focus on further testing, particularly on Meta Quest hardware, before determining the most suitable direction for the final HoloInsights implementation.



\---



\# Academic Prototype Notice



HoloInsights is currently an academic prototype.



All business data shown in the current prototypes is fictional sample data created for demonstration purposes.



References to AI insights describe the intended product experience. The current prototype insight responses are simulated and should not be interpreted as live AI-generated business analysis.

