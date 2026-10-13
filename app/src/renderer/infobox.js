// Info Box (función 002; FR-002 a FR-004, FR-024; contracts/ui.md "Info Box").
// Con la herramienta Muro muestra los valores del próximo muro; con la Flecha, los de los muros seleccionados.
import { formatMeters } from "./storey-panel.js";

const $ = (id) => document.getElementById(id);
const VARIOS = "varios";
const REFERENCE_TEXT = { exterior: "Exterior", center: "Centro", interior: "Interior", other: "Otra" };
const DEFAULT_MATERIAL = "Hormigón";
const DEFAULT_THICKNESS = 0.2;

export const parseNumber = (text) => {
  const trimmed = String(text).trim();
  return trimmed === "" ? NaN : Number(trimmed.replace(",", "."));
};

function same(values) {
  return values.every((v) => JSON.stringify(v) === JSON.stringify(values[0])) ? values[0] : VARIOS;
}

export class InfoBox {
  constructor({ onEdit, onSplit, onDelete, onOpenStructures, showMessage }) {
    this.onEdit = onEdit; // cambios de la selección → edit_walls
    this.onSplit = onSplit;
    this.onDelete = onDelete;
    this.onOpenStructures = onOpenStructures;
    this.showMessage = showMessage;
    this.state = { has_project: false, materials: [], structures: [], storeys: [] };
    this.tool = "arrow";
    this.selection = []; // datos de los muros seleccionados (data-model.md §6)
    // Valores del próximo muro (FR-004): se recuerdan mientras el programa esté abierto.
    this.values = { structure_id: null, material_id: null, thickness: DEFAULT_THICKNESS, height: null, reference: "exterior" };

    $("ib-structure").addEventListener("change", () => this.structureChanged());
    $("ib-material").addEventListener("change", () => this.materialChanged());
    $("ib-thickness").addEventListener("change", () => this.numberChanged("thickness", "El espesor debe ser mayor que 0."));
    $("ib-height").addEventListener("change", () => this.numberChanged("height", "La altura debe ser mayor que 0."));
    for (const button of $("ib-reference").querySelectorAll("button")) {
      button.addEventListener("click", () => {
        this.values.reference = button.dataset.reference;
        this.render();
      });
    }
    $("ib-structures").addEventListener("click", () => this.onOpenStructures());
    $("ib-split").addEventListener("click", () => this.onSplit());
    $("ib-delete").addEventListener("click", () => this.onDelete());
  }

  // ---------- datos ----------
  activeStorey() {
    return this.state.storeys.find((s) => s.id === this.state.active_storey_id) || null;
  }

  structure(id) {
    return this.state.structures.find((s) => s.id === id) || null;
  }

  defaultMaterialId() {
    const found = this.state.materials.find((m) => m.name === DEFAULT_MATERIAL) || this.state.materials[0];
    return found ? found.id : null;
  }

  // Valores que usa el próximo muro (orden create_wall).
  toolValues() {
    const storey = this.activeStorey();
    const composite = this.values.structure_id !== null;
    return {
      structure_id: this.values.structure_id,
      material_id: composite ? null : this.values.material_id,
      thickness: composite ? null : this.values.thickness,
      height: this.values.height ?? (storey ? storey.height : 3.0),
      reference: this.values.reference,
    };
  }

  // Espesor y capas del próximo muro, para la vista previa.
  toolLayers() {
    const s = this.structure(this.values.structure_id);
    return s ? s.layers.map((l) => l.thickness) : [this.values.thickness];
  }

  // ---------- cambios ----------
  structureChanged() {
    const raw = $("ib-structure").value;
    const id = raw === "" ? null : Number(raw);
    if (this.tool === "wall") {
      this.values.structure_id = id;
      this.render();
    } else if (raw !== VARIOS) {
      this.onEdit({ structure_id: id });
    }
  }

  materialChanged() {
    const id = Number($("ib-material").value);
    if (this.tool === "wall") {
      this.values.material_id = id;
      this.render();
    } else {
      this.onEdit({ material_id: id });
    }
  }

  numberChanged(field, message) {
    const input = $(`ib-${field}`);
    const value = parseNumber(input.value);
    if (!(value > 0)) {
      this.showMessage(message, true);
      this.render(); // vuelve el valor anterior
      return;
    }
    if (this.tool === "wall") {
      this.values[field] = value;
      this.render();
    } else {
      this.onEdit({ [field]: value });
    }
  }

  // ---------- dibujo ----------
  render(state = this.state, { tool = this.tool, selection = this.selection } = {}) {
    this.state = state;
    this.tool = tool;
    this.selection = selection;
    $("infobox").classList.toggle("disabled", !state.has_project);
    if (this.values.structure_id !== null && !this.structure(this.values.structure_id)) this.values.structure_id = null;
    if (!state.materials.some((m) => m.id === this.values.material_id)) this.values.material_id = this.defaultMaterialId();
    if (tool === "wall") this.renderTool();
    else this.renderSelection();
  }

  fillSelects(structureValue, materialValue) {
    const structureSelect = $("ib-structure");
    structureSelect.innerHTML = "";
    const add = (select, value, text, disabled = false) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = text;
      option.disabled = disabled;
      select.appendChild(option);
    };
    add(structureSelect, "", "Básica");
    for (const s of this.state.structures) add(structureSelect, String(s.id), s.name);
    if (structureValue === VARIOS) add(structureSelect, VARIOS, VARIOS, true);
    structureSelect.value = structureValue === VARIOS ? VARIOS : structureValue === null ? "" : String(structureValue);

    const materialSelect = $("ib-material");
    materialSelect.innerHTML = "";
    if (materialValue === "—") add(materialSelect, "", "—");
    for (const m of this.state.materials) add(materialSelect, String(m.id), m.name);
    if (materialValue === VARIOS) add(materialSelect, VARIOS, VARIOS, true);
    materialSelect.value = materialValue === "—" ? "" : materialValue === VARIOS ? VARIOS : String(materialValue ?? "");
  }

  setNumber(field, value, enabled) {
    const input = $(`ib-${field}`);
    input.value = value === VARIOS || value === null ? "" : formatMeters(value);
    input.placeholder = value === VARIOS ? VARIOS : "";
    input.disabled = !enabled;
  }

  show({ fields, empty, split, remove }) {
    $("ib-fields").hidden = !fields;
    $("ib-empty").hidden = !empty;
    $("ib-split").hidden = !split;
    $("ib-delete").hidden = !remove;
  }

  renderTool() {
    $("ib-icon").src = "icons/wall.svg";
    $("ib-title").textContent = "";
    this.show({ fields: true, empty: false, split: false, remove: false });
    $("ib-notice").hidden = true;
    const composite = this.structure(this.values.structure_id);
    this.fillSelects(this.values.structure_id, composite ? "—" : this.values.material_id);
    $("ib-structure").disabled = false;
    $("ib-material").disabled = !!composite;
    this.setNumber("thickness", composite ? composite.thickness : this.values.thickness, !composite);
    this.setNumber("height", this.toolValues().height, true);
    $("ib-reference").hidden = false;
    $("ib-reference-text").hidden = true;
    for (const button of $("ib-reference").querySelectorAll("button")) {
      button.classList.toggle("on", button.dataset.reference === this.values.reference);
    }
  }

  renderSelection() {
    $("ib-icon").src = "icons/arrow.svg";
    const walls = this.selection;
    $("ib-title").textContent = walls.length === 0 ? "" : walls.length === 1 ? "1 muro seleccionado" : `${walls.length} muros seleccionados`;
    if (walls.length === 0) {
      this.show({ fields: false, empty: true, split: false, remove: false });
      $("ib-notice").hidden = true;
      return;
    }
    this.show({ fields: true, empty: false, split: true, remove: true });
    const locked = walls.some((w) => w.kind === "locked");
    const other = walls.some((w) => w.reference === "other");
    const allBasic = walls.every((w) => w.structure_id === null && w.layers.length === 1);
    const materialValue = allBasic ? same(walls.map((w) => w.layers[0].material_id)) : "—";
    this.fillSelects(same(walls.map((w) => w.structure_id)), materialValue);
    $("ib-structure").disabled = locked || other;
    $("ib-material").disabled = locked || !allBasic;
    this.setNumber("thickness", same(walls.map((w) => w.thickness)), !locked && !other && allBasic);
    this.setNumber("height", same(walls.map((w) => w.height)), !locked);
    $("ib-reference").hidden = true;
    const reference = same(walls.map((w) => w.reference));
    $("ib-reference-text").hidden = false;
    $("ib-reference-text").textContent = reference === VARIOS ? VARIOS : REFERENCE_TEXT[reference];
    $("ib-split").disabled = !walls.some((w) => w.kind !== "locked" && w.layers.length >= 2);
    $("ib-notice").hidden = !locked;
    $("ib-notice").textContent = locked ? walls.find((w) => w.kind === "locked").locked_reason : "";
  }
}
