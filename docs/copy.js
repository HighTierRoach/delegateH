const modelControls = document.querySelector(".model-controls");

if (modelControls) {
  const coordinator = modelControls.querySelector("#coordinator-model");
  const worker = modelControls.querySelector("#worker-model");
  const prompt = document.querySelector("#delegate-prompt");

  function updatePrompt() {
    const coordinatorModel = coordinator.value.trim();
    const workerModel = worker.value.trim() || "4 Hydrogen";
    const sentences = ["$delegateH AUTO"];
    if (coordinatorModel) sentences.push(`Use ${coordinatorModel} as orchestrator.`);
    sentences.push(`Use ${workerModel} as the Gemini Tasks worker.`);
    sentences.push("Review this change and delegate independent checks if useful.");
    prompt.textContent = sentences.join(" ");
  }

  modelControls.addEventListener("input", updatePrompt);
  updatePrompt();
  modelControls.hidden = false;
}

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
