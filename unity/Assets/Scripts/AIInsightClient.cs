
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
        {
            StopCoroutine(activeRequest);
        }

        activeRequest = StartCoroutine(
            FetchInsightCoroutine(requestVersion)
        );
    }

    private IEnumerator FetchInsightCoroutine(int version)
    {
        // Ask Gemini for a short, complete insight
        // that fits comfortably inside the Quest dashboard.
        string question =
            "Which region is underperforming? " +
            "Answer in one very short, complete sentence, " +
            "ideally under 80 characters. " +
            "Include the key percentages. " +
            "Do not add extra explanations or bullet points.";

        string url = apiUrl + "?question=" +
                     UnityWebRequest.EscapeURL(question);

        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            request.timeout = 15;

            yield return request.SendWebRequest();

            if (version != requestVersion)
            {
                yield break;
            }

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogWarning(
                    "AI request failed: " + request.error
                );

                yield break;
            }

            try
            {
                AIInsightResponse response =
                    JsonUtility.FromJson<AIInsightResponse>(
                        request.downloadHandler.text
                    );

                if (response != null &&
                    response.insight_type == "llm" &&
                    !string.IsNullOrEmpty(response.insight))
                {
                    // Display the complete AI-generated sentence.
                    string shortInsight = response.insight.Trim();

                    insightText.text =
                        "GEMINI AI INSIGHT\n" + shortInsight;

                    Debug.Log(
                        "HoloInsights Gemini insight received."
                    );
                }
                else
                {
                    Debug.LogWarning(
                        "Live AI unavailable; retaining local insight."
                    );
                }
            }
            catch (Exception exception)
            {
                Debug.LogWarning(
                    "Failed to parse AI insight: " +
                    exception.Message
                );
            }
        }

        activeRequest = null;
    }
}
