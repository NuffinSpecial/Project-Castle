document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("submission-form");
  const messageEl = document.getElementById("submission-message");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    messageEl.hidden = true;
    messageEl.className = "form-message";

    const english = document.getElementById("english-input").value.trim();
    const videoInput = document.getElementById("video-input");
    const notes = document.getElementById("notes-input").value.trim();

    if (!english) {
      messageEl.textContent = "Please enter an English word or phrase.";
      messageEl.classList.add("form-message--error");
      messageEl.hidden = false;
      return;
    }

    const formData = new FormData();
    formData.append("english", english);
    formData.append("notes", notes);
    if (videoInput.files[0]) {
      formData.append("video", videoInput.files[0]);
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = "Submitting…";

    try {
      const response = await fetch("/api/submissions", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Submission failed.");
      }
      messageEl.textContent = data.message || "Thank you! Your submission was received.";
      messageEl.classList.add("form-message--success");
      messageEl.hidden = false;
      form.reset();
    } catch (error) {
      messageEl.textContent = error.message || "Could not submit. Please try again.";
      messageEl.classList.add("form-message--error");
      messageEl.hidden = false;
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit";
    }
  });
});
