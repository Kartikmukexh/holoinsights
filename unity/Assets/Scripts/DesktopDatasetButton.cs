using UnityEngine;

public class DesktopDatasetButton : MonoBehaviour
{
    public enum ButtonAction
    {
        SwitchDataset,
        SwitchRegion,
        SwitchQuarter
    }

    public DashboardController dashboardController;

    public ButtonAction buttonAction = ButtonAction.SwitchDataset;

    private void OnMouseDown()
    {
        if (dashboardController == null)
        {
            Debug.LogWarning(
                "DesktopDatasetButton: DashboardController is not assigned."
            );
            return;
        }

        switch (buttonAction)
        {
            case ButtonAction.SwitchRegion:
                dashboardController.SwitchRegion();
                Debug.Log("Desktop button clicked: Region switched.");
                break;

            case ButtonAction.SwitchQuarter:
                dashboardController.SwitchQuarter();
                Debug.Log("Desktop button clicked: Quarter switched.");
                break;

            default:
                dashboardController.SwitchDataset();
                Debug.Log("Desktop button clicked: Dataset switched.");
                break;
        }
    }
}