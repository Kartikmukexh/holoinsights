
using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

[Serializable]
public class SalesRecord
{
    public string product_name;
    public string region;
    public string quarter;
    public float revenue;
}

[Serializable]
public class SalesResponse
{
    public string source;
    public SalesRecord[] data;
}

public class SalesDataClient : MonoBehaviour
{
    [Header("Backend")]
    public string apiUrl = "http://127.0.0.1:8000/api/sales-data";

    public SalesResponse LatestResponse { get; private set; }

    public event Action<SalesResponse> OnSalesDataLoaded;

    private void Start()
    {
        FetchSalesData();
    }

    public void FetchSalesData()
    {
        StartCoroutine(FetchSalesDataCoroutine());
    }

    private IEnumerator FetchSalesDataCoroutine()
    {
        using (UnityWebRequest request = UnityWebRequest.Get(apiUrl))
        {
            request.timeout = 10;

            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError(
                    "HoloInsights API request failed: " + request.error
                );
                yield break;
            }

            try
            {
                LatestResponse = JsonUtility.FromJson<SalesResponse>(
                    request.downloadHandler.text
                );

                if (LatestResponse == null ||
                    LatestResponse.data == null)
                {
                    Debug.LogError(
                        "HoloInsights received an invalid sales response."
                    );
                    yield break;
                }

                Debug.Log(
                    "HoloInsights API connected. Source: " +
                    LatestResponse.source +
                    ". Records: " +
                    LatestResponse.data.Length
                );

                OnSalesDataLoaded?.Invoke(LatestResponse);
            }
            catch (Exception exception)
            {
                Debug.LogError(
                    "Failed to parse sales data: " + exception.Message
                );
            }
        }
    }
}
