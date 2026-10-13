// Caja de herramientas (función 002, FR-001; contracts/ui.md): Flecha y Muro, una sola activa.
const $ = (id) => document.getElementById(id);

export class Toolbox {
  constructor({ onChange }) {
    this.onChange = onChange;
    this.tool = "arrow";
    this.buttons = [...$("toolbox").querySelectorAll("button[data-tool]")];
    for (const button of this.buttons) button.addEventListener("click", () => this.onChange(button.dataset.tool));
    this.set("arrow");
  }

  set(tool) {
    this.tool = tool;
    for (const button of this.buttons) button.classList.toggle("active", button.dataset.tool === tool);
  }

  enable(enabled) {
    $("toolbox").classList.toggle("disabled", !enabled);
  }
}
