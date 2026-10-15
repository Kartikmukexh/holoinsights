
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

    [Header("Offline Support")]
    public bool useOfflineDataOnAndroid = true;

    public SalesResponse LatestResponse { get; private set; }

    public event Action<SalesResponse> OnSalesDataLoaded;

    private void Start()
    {
        FetchSalesData();
    }

    public void FetchSalesData()
    {
#if UNITY_ANDROID && !UNITY_EDITOR
        if (useOfflineDataOnAndroid)
        {
            LoadOfflineData();
            return;
        }
#endif

        StartCoroutine(FetchSalesDataCoroutine());
    }

    private IEnumerator FetchSalesDataCoroutine()
    {
        using (UnityWebRequest request = UnityWebRequest.Get(apiUrl))
        {
            request.timeout = 5;

            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                Debug.LogWarning(
                    "HoloInsights API unavailable: " + request.error
                );

                LoadOfflineData();
                yield break;
            }

            try
            {
                SalesResponse response =
                    JsonUtility.FromJson<SalesResponse>(
                        request.downloadHandler.text
                    );

                if (response == null ||
                    response.data == null ||
                    response.data.Length == 0)
                {
                    Debug.LogWarning(
                        "Invalid API sales response. Using offline data."
                    );

                    LoadOfflineData();
                    yield break;
                }

                LatestResponse = response;

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
                Debug.LogWarning(
                    "Failed to parse sales data: " +
                    exception.Message
                );

                LoadOfflineData();
            }
        }
    }

    private void LoadOfflineData()
    {
        LatestResponse = new SalesResponse
        {
            source = "offline_sample",

            data = new SalesRecord[]
            {
                new SalesRecord { product_name = "Product A", region = "North", quarter = "Q1", revenue = 85000 },
                new SalesRecord { product_name = "Product B", region = "North", quarter = "Q1", revenue = 62000 },
                new SalesRecord { product_name = "Product C", region = "North", quarter = "Q1", revenue = 48000 },

                new SalesRecord { product_name = "Product A", region = "South", quarter = "Q1", revenue = 60000 },
                new SalesRecord { product_name = "Product B", region = "South", quarter = "Q1", revenue = 78000 },
                new SalesRecord { product_name = "Product C", region = "South", quarter = "Q1", revenue = 55000 },

                new SalesRecord { product_name = "Product A", region = "North", quarter = "Q2", revenue = 92000 },
                new SalesRecord { product_name = "Product B", region = "North", quarter = "Q2", revenue = 68000 },
                new SalesRecord { product_name = "Product C", region = "North", quarter = "Q2", revenue = 52000 },

                new SalesRecord { product_name = "Product A", region = "South", quarter = "Q2", revenue = 71000 },
                new SalesRecord { product_name = "Product B", region = "South", quarter = "Q2", revenue = 84000 },
                new SalesRecord { product_name = "Product C", region = "South", quarter = "Q2", revenue = 59000 }
            }
        };

        Debug.Log(
            "HoloInsights offline sales data loaded. Records: " +
            LatestResponse.data.Length
        );

        OnSalesDataLoaded?.Invoke(LatestResponse);
    }
}
