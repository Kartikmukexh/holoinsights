
using System;
using System.Collections;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;

[Serializable]
public class AIInsightResponse
{
    public string insight;
    public string insight_type;
    public string source;
}

public class AIInsightClient : MonoBehaviour
{
    [Header("Backend")]
    public string apiUrl = "http://127.0.0.1:8000/api/insight";

    [Header("Display")]
    public TMP_Text insightText;

    private Coroutine activeRequest;
    private int requestVersion = 0;

    public void FetchInsight()
    {
        if (insightText == null)
        {
            Debug.LogWarning("AI insight text is not assigned.");
            return;
        }

        requestVersion++;

        if (activeRequest != null)
            StopCoroutine(activeRequest);

        activeRequest = StartCoroutine(
            FetchInsightCoroutine(requestVersion)
        );
    }

    private IEnumerator FetchInsightCoroutine(int version)
    {
        string question = "Which region is underperforming?";

        string url = apiUrl + "?question=" +
                     UnityWebRequest.EscapeURL(question);

        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            request.timeout = 15;
            yield return request.SendWebRequest();

            if (version != requestVersion)
                yield break;

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogWarning("AI request failed: " + request.error);
                yield break;
            }

            AIInsightResponse response =
                JsonUtility.FromJson<AIInsightResponse>(
                    request.downloadHandler.text
                );

            if (response != null &&
                response.insight_type == "llm" &&
                !string.IsNullOrEmpty(response.insight))
            {
                insightText.text =
                    "GEMINI AI INSIGHT\n" + response.insight;

                Debug.Log("HoloInsights Gemini insight received.");
            }
            else
            {
                Debug.LogWarning(
                    "Live AI unavailable; retaining local insight."
                );
            }
        }

        activeRequest = null;
    }
}
