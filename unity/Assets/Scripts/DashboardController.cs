
using UnityEngine;
using TMPro;
using UnityEngine.InputSystem;

public class DashboardController : MonoBehaviour
{
    [Header("Bars")]
    public Transform productABar;
    public Transform productBBar;
    public Transform productCBar;

    [Header("Value Labels")]
    public TMP_Text productALabel;
    public TMP_Text productBLabel;
    public TMP_Text productCLabel;

    [Header("Sales Insight")]
    public TMP_Text insightText;

    [Header("Backend")]
    public SalesDataClient salesDataClient;

    [Header("Chart Settings")]
    public float maximumRevenue = 100000f;
    public float maximumBarHeight = 0.45f;
    public float barBaselineY = -0.35f;

    private SalesResponse salesResponse;

    // 0 = North Q1, 1 = South Q1,
    // 2 = North Q2, 3 = South Q2.
    private int datasetIndex = 0;

    private void Awake()
    {
        if (salesDataClient == null)
        {
            salesDataClient = GetComponent<SalesDataClient>();
        }
    }

    private void OnEnable()
    {
        if (salesDataClient != null)
        {
            salesDataClient.OnSalesDataLoaded += HandleSalesDataLoaded;
        }
    }

    private void Start()
    {
        if (salesDataClient == null)
        {
            insightText.text = "Sales data client is not configured.";
            Debug.LogError("HoloInsights: SalesDataClient is missing.");
            return;
        }

        insightText.text = "Loading sales data...";

        if (salesDataClient.LatestResponse != null)
        {
            HandleSalesDataLoaded(salesDataClient.LatestResponse);
        }
    }

    private void OnDisable()
    {
        if (salesDataClient != null)
        {
            salesDataClient.OnSalesDataLoaded -= HandleSalesDataLoaded;
        }
    }

    private void Update()
    {
        if (Keyboard.current != null &&
            Keyboard.current.spaceKey.wasPressedThisFrame)
        {
            SwitchDataset();
        }
    }

    // Called by keyboard, desktop mouse or XR selection.
    public void SwitchDataset()
    {
        datasetIndex = (datasetIndex + 1) % 4;
        RefreshDashboard();
    }

    private void HandleSalesDataLoaded(SalesResponse response)
    {
        salesResponse = response;

        Debug.Log(
            "HoloInsights dashboard received " +
            response.data.Length +
            " sales records."
        );

        RefreshDashboard();
    }

    private void RefreshDashboard()
    {
        if (salesResponse == null || salesResponse.data == null)
        {
            insightText.text = "Waiting for backend sales data...";
            return;
        }

        string region = datasetIndex % 2 == 0 ? "North" : "South";
        string quarter = datasetIndex < 2 ? "Q1" : "Q2";

        float a = GetRevenue("Product A", region, quarter);
        float b = GetRevenue("Product B", region, quarter);
        float c = GetRevenue("Product C", region, quarter);

        SetBar(productABar, a);
        SetBar(productBBar, b);
        SetBar(productCBar, c);

        productALabel.text = "A - " + (a / 1000f).ToString("0.#") + "K";
        productBLabel.text = "B - " + (b / 1000f).ToString("0.#") + "K";
        productCLabel.text = "C - " + (c / 1000f).ToString("0.#") + "K";

        float highestRevenue = Mathf.Max(a, b, c);
        string leadingProduct = "Product A";

        if (b > a && b >= c)
        {
            leadingProduct = "Product B";
        }
        else if (c > a && c > b)
        {
            leadingProduct = "Product C";
        }

        insightText.text =
            region + " " + quarter + " | " +
            leadingProduct + " leads with $" +
            (highestRevenue / 1000f).ToString("0.#") +
            "K revenue.\nSource: " +
            salesResponse.source +
            " (data-derived summary)";
    }

    private float GetRevenue(string product, string region, string quarter)
    {
        float total = 0f;

        foreach (SalesRecord record in salesResponse.data)
        {
            if (record.product_name == product &&
                record.region == region &&
                record.quarter == quarter)
            {
                total += record.revenue;
            }
        }

        return total;
    }

    private void SetBar(Transform bar, float revenue)
    {
        float ratio = Mathf.Max(0f, revenue) /
                      Mathf.Max(1f, maximumRevenue);

        float height = maximumBarHeight * ratio;

        Vector3 scale = bar.localScale;
        scale.y = height;
        bar.localScale = scale;

        Vector3 position = bar.localPosition;
        position.y = barBaselineY + height / 2f;
        bar.localPosition = position;
    }
}
