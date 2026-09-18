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

    private Vector3 productABaseScale;
    private Vector3 productBBaseScale;
    private Vector3 productCBaseScale;

    private Vector3 productABasePosition;
    private Vector3 productBBasePosition;
    private Vector3 productCBasePosition;

    private bool showingSecondDataset = false;

    void Start()
    {
        productABaseScale = productABar.localScale;
        productBBaseScale = productBBar.localScale;
        productCBaseScale = productCBar.localScale;

        productABasePosition = productABar.localPosition;
        productBBasePosition = productBBar.localPosition;
        productCBasePosition = productCBar.localPosition;

        ShowDatasetOne();
    }

    void Update()
    {
        if (Keyboard.current != null &&
            Keyboard.current.spaceKey.wasPressedThisFrame)
        {
            showingSecondDataset = !showingSecondDataset;

            if (showingSecondDataset)
            {
                ShowDatasetTwo();
            }
            else
            {
                ShowDatasetOne();
            }
        }
    }

    void ShowDatasetOne()
    {
        SetBar(
            productABar,
            productABaseScale,
            productABasePosition,
            85f / 85f
        );

        SetBar(
            productBBar,
            productBBaseScale,
            productBBasePosition,
            62f / 62f
        );

        SetBar(
            productCBar,
            productCBaseScale,
            productCBasePosition,
            48f / 48f
        );

        productALabel.text = "A - 85";
        productBLabel.text = "B - 62";
        productCLabel.text = "C - 48";

        insightText.text =
            "Product A leads at 85, outperforming Product B by 23\n" +
            "and Product C by 37.";
    }

    void ShowDatasetTwo()
    {
        SetBar(
            productABar,
            productABaseScale,
            productABasePosition,
            60f / 85f
        );

        SetBar(
            productBBar,
            productBBaseScale,
            productBBasePosition,
            78f / 62f
        );

        SetBar(
            productCBar,
            productCBaseScale,
            productCBasePosition,
            55f / 48f
        );

        productALabel.text = "A - 60";
        productBLabel.text = "B - 78";
        productCLabel.text = "C - 55";

        insightText.text =
            "Product B now leads at 78, outperforming Product A by 18\n" +
            "and Product C by 23.";
    }

    void SetBar(
        Transform bar,
        Vector3 baseScale,
        Vector3 basePosition,
        float heightMultiplier
    )
    {
        Vector3 newScale = baseScale;
        newScale.y = baseScale.y * heightMultiplier;

        bar.localScale = newScale;

        Vector3 newPosition = basePosition;

        // Move the bar so its bottom stays approximately in the same place.
        newPosition.y =
            basePosition.y + (newScale.y - baseScale.y) / 2f;

        bar.localPosition = newPosition;
    }
}