// Selección con la Flecha (función 002; FR-023; contracts/ui.md "Selección").
// Clic sobre un muro en la planta (piso activo) o en el 3D (clic sin arrastre); Shift + clic agrega o quita;
// clic en un lugar vacío o Esc deja todo sin seleccionar. Los seleccionados se ven en azul en las dos vistas.
export class Selection {
  constructor({ viewports, meshes, onChange }) {
    this.viewports = viewports;
    this.meshes = meshes;
    this.onChange = onChange;
    this.ids = [];
  }

  wallId(hit) {
    return hit && hit.object.userData.wall ? hit.object.userData.id : null;
  }

  clickPlan(event) {
    return this.pick(this.wallId(this.viewports.hitPlan(event)), event.shiftKey);
  }

  click3d(event, hit) {
    return this.pick(this.wallId(hit), event.shiftKey);
  }

  pick(id, shift) {
    if (id === null) {
      if (!shift) this.set([]);
      return this.ids;
    }
    if (shift) this.set(this.ids.includes(id) ? this.ids.filter((x) => x !== id) : [...this.ids, id]);
    else this.set([id]);
    return this.ids;
  }

  set(ids) {
    this.ids = ids.filter((id) => this.meshes.wall(id));
    this.meshes.setSelected(this.ids);
    this.onChange(this.ids);
  }

  clear() {
    if (this.ids.length) this.set([]);
  }

  // Después de cada respuesta del motor: quedan solo los muros que siguen existiendo.
  keepExisting() {
    const kept = this.ids.filter((id) => this.meshes.wall(id));
    if (kept.length !== this.ids.length) this.set(kept);
  }

  walls() {
    return this.ids.map((id) => this.meshes.wall(id)).filter(Boolean);
  }
}
