// Panel "BIM Simple": proyecto, navegador de pisos (clic selecciona, doble clic activa), botones y diálogo
// "Editar piso" (contracts/ui.md).
const $ = (id) => document.getElementById(id);
export const formatMeters = (value) => value.toFixed(2).replace(".", ",");

export class StoreyPanel {
  constructor({ onAction }) {
    this.onAction = onAction;
    this.state = { has_project: false, storeys: [] };
    this.selectedId = null;
    const bind = (id, action) => $(id).addEventListener("click", () => this.onAction(action));
    bind("btn-new", "new");
    bind("btn-open", "open");
    bind("btn-add-above", "add-above");
    bind("btn-add-below", "add-below");
    bind("btn-edit", "edit");
    bind("btn-delete", "delete");
    bind("btn-fit", "fit");
    const rows = $("storeys");
    rows.addEventListener("click", (event) => {
      const row = event.target.closest("tr");
      if (!row) return;
      this.selectedId = Number(row.dataset.id);
      this.render(this.state);
    });
    rows.addEventListener("dblclick", (event) => {
      const row = event.target.closest("tr");
      if (row) this.onAction("activate", Number(row.dataset.id));
    });
  }

  selected() {
    return this.state.storeys.find((s) => s.id === this.selectedId) || null;
  }

  render(state) {
    this.state = state;
    const project = $("project");
    $("no-project-actions").hidden = state.has_project;
    $("navigator").hidden = !state.has_project;
    $("notice").hidden = !state.notice;
    $("notice").textContent = state.notice || "";
    if (!state.has_project) {
      project.textContent = "No hay ningún proyecto abierto";
      $("storeys").innerHTML = "";
      return;
    }
    const name = state.path ? state.path.split(/[\\/]/).pop() : "Proyecto sin guardar";
    project.textContent = name;
    if (state.dirty) {
      const dirty = document.createElement("span");
      dirty.className = "dirty";
      dirty.textContent = " • Cambios sin guardar";
      project.appendChild(dirty);
    }
    if (!state.storeys.some((s) => s.id === this.selectedId)) this.selectedId = state.active_storey_id;
    const body = $("storeys");
    body.innerHTML = "";
    for (const storey of state.storeys) {
      const row = document.createElement("tr");
      row.dataset.id = storey.id;
      if (storey.id === state.active_storey_id) row.classList.add("active");
      if (storey.id === this.selectedId) row.classList.add("selected");
      const cells = [
        (storey.id === state.active_storey_id ? "● " : "") + storey.name,
        formatMeters(storey.elevation),
        formatMeters(storey.height),
      ];
      cells.forEach((text, i) => {
        const cell = document.createElement("td");
        cell.textContent = text;
        if (i > 0) cell.className = "num";
        row.appendChild(cell);
      });
      body.appendChild(row);
    }
    const hasSelection = this.selected() !== null;
    $("btn-add-above").disabled = !state.has_building;
    $("btn-add-below").disabled = !state.has_building;
    $("btn-edit").disabled = !hasSelection;
    $("btn-delete").disabled = !hasSelection || state.storeys.length <= 1;
  }

  // Abre "Editar piso" con los valores del piso; devuelve solo lo que cambió, o null si se cancela.
  editDialog(storey) {
    const dialog = $("edit-dialog");
    const fields = { name: $("edit-name"), elevation: $("edit-elevation"), height: $("edit-height") };
    const error = $("edit-error");
    fields.name.value = storey.name;
    fields.elevation.value = formatMeters(storey.elevation);
    fields.height.value = formatMeters(storey.height);
    error.hidden = true;
    dialog.showModal();
    return new Promise((resolve) => {
      const parse = (text) => Number(String(text).trim().replace(",", "."));
      const onClose = () => {
        if (dialog.returnValue !== "ok") return finish(null);
        const elevation = parse(fields.elevation.value);
        const height = parse(fields.height.value);
        if (fields.elevation.value.trim() === "" || Number.isNaN(elevation) || fields.height.value.trim() === "" || Number.isNaN(height)) {
          error.textContent = "Escribe un número, por ejemplo 3,00.";
          error.hidden = false;
          dialog.showModal();
          return;
        }
        const changes = {};
        if (fields.name.value !== storey.name) changes.name = fields.name.value;
        if (Math.abs(elevation - storey.elevation) > 1e-9) changes.elevation = elevation;
        if (Math.abs(height - storey.height) > 1e-9) changes.height = height;
        finish(changes);
      };
      const finish = (value) => {
        dialog.removeEventListener("close", onClose);
        resolve(value);
      };
      dialog.addEventListener("close", onClose);
    });
  }
}
