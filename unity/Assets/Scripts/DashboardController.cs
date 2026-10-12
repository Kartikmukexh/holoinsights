
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

    [Header("AI Insight")]
    public TMP_Text insightText;

    [Header("Backend")]
    public SalesDataClient salesDataClient;

    [Header("Chart Settings")]
    public float maximumRevenue = 100000f;
    public float maximumBarHeight = 0.45f;
    public float barBaselineY = -0.35f;

    private SalesResponse salesResponse;
    private bool showingSecondDataset = false;

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

    // Used by the keyboard, mouse button and XR interaction.
    public void SwitchDataset()
    {
        showingSecondDataset = !showingSecondDataset;
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

        string region = showingSecondDataset ? "South" : "North";
        string quarter = "Q1";

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

        if (highestRevenue == b)
        {
            leadingProduct = "Product B";
        }
        else if (highestRevenue == c)
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
        // All bars use the same revenue scale.
        float ratio = Mathf.Max(0f, revenue) / Mathf.Max(1f, maximumRevenue);

        float height = maximumBarHeight * ratio;

        Vector3 scale = bar.localScale;
        scale.y = height;
        bar.localScale = scale;

        Vector3 position = bar.localPosition;
        position.y = barBaselineY + height / 2f;
        bar.localPosition = position;
    }
}
