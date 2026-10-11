
using UnityEngine;

public class DesktopDatasetButton : MonoBehaviour
{
    public DashboardController dashboardController;

    private void OnMouseDown()
    {
        if (dashboardController != null)
        {
            dashboardController.SwitchDataset();
            Debug.Log("Desktop button clicked: Dataset switched.");
        }
        else
        {
            Debug.LogWarning("DesktopDatasetButton: DashboardController is not assigned.");
        }
    }
}
