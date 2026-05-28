document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".admin-approve").forEach((button) => {
    button.addEventListener("click", async () => {
      const id = button.dataset.id;
      button.disabled = true;
      try {
        const response = await fetch(`/admin/submissions/${id}/approve`, {
          method: "POST",
          headers: { Accept: "application/json" },
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Approve failed.");
        button.closest(".admin-card")?.remove();
      } catch (error) {
        alert(error.message);
        button.disabled = false;
      }
    });
  });

  document.querySelectorAll(".admin-reject").forEach((button) => {
    button.addEventListener("click", async () => {
      const card = button.closest(".admin-card");
      const noteField = card?.querySelector(".admin-reject-note");
      const noteInput = card?.querySelector(".reject-note-input");

      if (noteField?.hidden) {
        noteField.hidden = false;
        noteInput?.focus();
        return;
      }

      const id = button.dataset.id;
      button.disabled = true;
      try {
        const response = await fetch(`/admin/submissions/${id}/reject`, {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ reviewNote: noteInput?.value || "" }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Reject failed.");
        card?.remove();
      } catch (error) {
        alert(error.message);
        button.disabled = false;
      }
    });
  });
});
