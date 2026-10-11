// Mallas que manda el motor (data-model.md §5), agrupadas por piso en la escena.
import * as THREE from "three";

const MATERIALS = {
  IfcWall: new THREE.MeshStandardMaterial({ color: "#ddd6ca", roughness: 0.9 }),
  IfcSlab: new THREE.MeshStandardMaterial({ color: "#cfcbc4", roughness: 0.9 }),
  IfcColumn: new THREE.MeshStandardMaterial({ color: "#c9c2b6", roughness: 0.9 }),
  IfcDoor: new THREE.MeshStandardMaterial({ color: "#b8926a", roughness: 0.8 }),
  IfcWindow: new THREE.MeshStandardMaterial({ color: "#a9c6dd", roughness: 0.4 }),
};
const DEFAULT_MATERIAL = new THREE.MeshStandardMaterial({ color: "#d9d9d6", roughness: 0.9 });
const EDGE_MATERIAL = new THREE.LineBasicMaterial({ color: "#3b3833" });

function decode(base64, Type) {
  const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
  return new Type(bytes.buffer);
}

export class MeshStore {
  constructor(viewports) {
    this.viewports = viewports;
    this.byId = new Map();
  }

  get size() {
    return this.byId.size;
  }

  clear() {
    for (const id of [...this.byId.keys()]) this.remove(id);
  }

  remove(id) {
    const mesh = this.byId.get(id);
    if (!mesh) return;
    mesh.parent.remove(mesh);
    mesh.geometry.dispose();
    mesh.children.forEach((child) => child.geometry.dispose());
    this.byId.delete(id);
  }

  // result = { meshes, existing_ids } de la orden "meshes".
  apply(result) {
    for (const item of result.meshes) {
      this.remove(item.id);
      const indexed = new THREE.BufferGeometry();
      indexed.setAttribute("position", new THREE.BufferAttribute(decode(item.vertices, Float32Array), 3));
      indexed.setIndex(new THREE.BufferAttribute(decode(item.faces, Uint32Array), 1));
      const geometry = indexed.toNonIndexed();
      geometry.computeVertexNormals();
      indexed.dispose();
      const material = MATERIALS[item.ifc_class] || DEFAULT_MATERIAL;
      const mesh = new THREE.Mesh(geometry, material);
      mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geometry, 20), EDGE_MATERIAL));
      mesh.userData = { id: item.id, storeyId: item.storey_id, ifcClass: item.ifc_class, material };
      this.viewports.group(item.storey_id).add(mesh);
      this.byId.set(item.id, mesh);
    }
    const existing = new Set(result.existing_ids);
    for (const id of [...this.byId.keys()]) if (!existing.has(id)) this.remove(id);
    this.viewports.draw();
  }
}
