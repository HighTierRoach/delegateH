const announcement = document.querySelector("#copy-status");

if (navigator.clipboard?.writeText) {
  for (const button of document.querySelectorAll(".snippet button")) {
    button.hidden = false;
    let reset;
    button.addEventListener("click", async () => {
      const command = button.closest(".snippet").querySelector("code").textContent;
      window.clearTimeout(reset);
      try {
        await navigator.clipboard.writeText(command);
        button.textContent = "Copied";
        announcement.textContent = "Copied to clipboard.";
      } catch {
        button.textContent = "Copy failed";
        announcement.textContent = "Copy failed. Select the text to copy it manually.";
      }
      reset = window.setTimeout(() => {
        button.textContent = "Copy";
        announcement.textContent = "";
      }, 2200);
    });
  }
}
