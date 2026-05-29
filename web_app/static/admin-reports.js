document.addEventListener("DOMContentLoaded", () => {
  async function updateReport(id, action) {
    const card = document.querySelector(`[data-report-id="${id}"]`);
    const noteInput = card?.querySelector(".report-note-input");
    const note = noteInput?.value?.trim() || "";

    const response = await fetch(`/admin/reports/${id}/${action}`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ adminNote: note }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Update failed.");
    }
    card?.remove();
  }

  document.querySelectorAll(".admin-report-resolve").forEach((button) => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        await updateReport(button.dataset.id, "resolve");
      } catch (error) {
        alert(error.message);
        button.disabled = false;
      }
    });
  });

  document.querySelectorAll(".admin-report-dismiss").forEach((button) => {
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        await updateReport(button.dataset.id, "dismiss");
      } catch (error) {
        alert(error.message);
        button.disabled = false;
      }
    });
  });
});
