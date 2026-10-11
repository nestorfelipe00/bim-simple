// Interfaz del prototipo: planta + 3D con Three.js; todo cambio del modelo lo hace el motor.
import * as THREE from "three";
import { MapControls } from "three/addons/controls/MapControls.js";
import CameraControls from "camera-controls";

THREE.Object3D.DEFAULT_UP.set(0, 0, 1); // IFC: Z hacia arriba
CameraControls.install({ THREE });

const PARAMS = new URLSearchParams(location.search);
const PRUEBA = PARAMS.get("prueba") === "1";
const $ = (id) => document.getElementById(id);
const lienzo = $("lienzo");
const divPlanta = $("vista-planta");
const div3d = $("vista-3d");

// ---------- escena ----------
const render3 = new THREE.WebGLRenderer({ canvas: lienzo, antialias: true, preserveDrawingBuffer: true });
render3.setPixelRatio(window.devicePixelRatio);
const escena = new THREE.Scene();
escena.background = new THREE.Color("#f4f4f2");
escena.add(new THREE.HemisphereLight("#ffffff", "#b9b4aa", 1.6));
const sol = new THREE.DirectionalLight("#ffffff", 1.4);
sol.position.set(10, -14, 20);
escena.add(sol);
const grilla = new THREE.GridHelper(40, 40, "#c9c5bd", "#e2dfd9");
grilla.rotation.x = Math.PI / 2;
escena.add(grilla);

const matMuro = new THREE.MeshStandardMaterial({ color: "#ddd6ca", roughness: 0.9 });
const matPlanta = new THREE.MeshBasicMaterial({ color: "#4a4741" }); // relleno oscuro de muro en planta
const matBorde = new THREE.LineBasicMaterial({ color: "#3b3833" });

const grupos = new Map(); // piso → THREE.Group
const mallas = new Map(); // elemento → THREE.Mesh
let estado = { proyecto: false };

const camPlanta = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 500);
camPlanta.up.set(0, 1, 0);
camPlanta.position.set(3, 2, 100);
const ctrlPlanta = new MapControls(camPlanta, divPlanta);
ctrlPlanta.enableRotate = false;
ctrlPlanta.screenSpacePanning = true;
ctrlPlanta.mouseButtons = { LEFT: -1, MIDDLE: THREE.MOUSE.PAN, RIGHT: -1 }; // clic izquierdo = dibujar
ctrlPlanta.zoomToCursor = true; // la rueda acerca hacia donde apunta el mouse
ctrlPlanta.target.set(3, 2, 0);

// Navegación 3D al estilo ArchiCAD/Revit:
//  - botón izquierdo (o Mayús + botón central): girar alrededor del punto señalado
//  - botón central o derecho: desplazar   · rueda: acercar hacia el mouse
const cam3d = new THREE.PerspectiveCamera(40, 1, 0.1, 500);
const ctrl3d = new CameraControls(cam3d, div3d);
ctrl3d.mouseButtons.left = CameraControls.ACTION.ROTATE;
ctrl3d.mouseButtons.middle = CameraControls.ACTION.TRUCK;
ctrl3d.mouseButtons.right = CameraControls.ACTION.TRUCK;
ctrl3d.mouseButtons.wheel = CameraControls.ACTION.DOLLY;
ctrl3d.dollyToCursor = true;
ctrl3d.maxPolarAngle = THREE.MathUtils.degToRad(88); // no se pasa por debajo del suelo ni se da vuelta
ctrl3d.minDistance = 0.5;
ctrl3d.maxDistance = 400;
ctrl3d.smoothTime = 0.12;
ctrl3d.draggingSmoothTime = 0.06;
ctrl3d.setLookAt(15, -13, 11, 3, 2, 1.5, false);

const rayo = new THREE.Raycaster();
div3d.addEventListener("pointerdown", (e) => {
  const girar = e.button === 0 || (e.button === 1 && e.shiftKey);
  ctrl3d.mouseButtons.middle = e.shiftKey ? CameraControls.ACTION.ROTATE : CameraControls.ACTION.TRUCK;
  if (!girar) return;
  // El centro de giro pasa a ser el punto del modelo bajo el mouse, sin mover la vista.
  const caja = div3d.getBoundingClientRect();
  rayo.setFromCamera(new THREE.Vector2(((e.clientX - caja.left) / caja.width) * 2 - 1, -((e.clientY - caja.top) / caja.height) * 2 + 1), cam3d);
  const toque = rayo.intersectObjects([...mallas.values()], false)[0];
  if (toque) ctrl3d.setOrbitPoint(toque.point.x, toque.point.y, toque.point.z);
}, { capture: true });

// Vista previa del muro que se está dibujando.
const vistaPrevia = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: "#1e5aa0" }));
vistaPrevia.visible = false;
escena.add(vistaPrevia);
const dibujo = { activo: false, p1: null }; // estado de la herramienta Muro

function dibujar() {
  const w = lienzo.clientWidth, h = lienzo.clientHeight;
  if (!w || !h) return;
  render3.setSize(w, h, false);
  render3.setScissorTest(true);
  const mitad = Math.floor(w / 2);

  // Planta: solo el piso activo, visto desde arriba, con los muros rellenos.
  const alto = 9;
  camPlanta.left = -alto * (mitad / h); camPlanta.right = alto * (mitad / h);
  camPlanta.top = alto; camPlanta.bottom = -alto;
  camPlanta.updateProjectionMatrix();
  for (const [id, g] of grupos) g.visible = id === estado.activo;
  for (const m of mallas.values()) m.material = matPlanta;
  render3.setViewport(0, 0, mitad, h); render3.setScissor(0, 0, mitad, h);
  render3.render(escena, camPlanta);

  // 3D: todo el edificio.
  for (const g of grupos.values()) g.visible = true;
  for (const m of mallas.values()) m.material = matMuro;
  vistaPrevia.visible = false;
  cam3d.aspect = (w - mitad) / h; cam3d.updateProjectionMatrix();
  render3.setViewport(mitad, 0, w - mitad, h); render3.setScissor(mitad, 0, w - mitad, h);
  render3.render(escena, cam3d);
  vistaPrevia.visible = dibujo.p1 !== null;
}
ctrlPlanta.addEventListener("change", dibujar);
new ResizeObserver(dibujar).observe(lienzo);
const reloj = new THREE.Timer();
(function bucle(instante) { // el 3D se mueve suave: se redibuja mientras la cámara se está acomodando
  reloj.update(instante);
  if (ctrl3d.update(reloj.getDelta())) dibujar();
  requestAnimationFrame(bucle);
})();

// Encuadra la planta en el piso activo y el 3D en todo el edificio.
function encuadrar() {
  const todo = new THREE.Box3(), piso = new THREE.Box3();
  for (const m of mallas.values()) {
    todo.expandByObject(m);
    if (m.userData.piso === estado.activo) piso.expandByObject(m);
  }
  if (todo.isEmpty()) return;
  const caja = piso.isEmpty() ? todo : piso;
  const c = caja.getCenter(new THREE.Vector3()), t = caja.getSize(new THREE.Vector3());
  ctrlPlanta.target.set(c.x, c.y, 0);
  camPlanta.position.set(c.x, c.y, 100);
  camPlanta.zoom = Math.min(9 / (t.y * 0.75), 9 * (divPlanta.clientWidth / lienzo.clientHeight) / (t.x * 0.75));
  camPlanta.updateProjectionMatrix();
  ctrlPlanta.update();
  const centro = todo.getCenter(new THREE.Vector3()), radio = todo.getSize(new THREE.Vector3()).length() / 2;
  const dist = radio / Math.sin(THREE.MathUtils.degToRad(cam3d.fov / 2)) * 1.1;
  const pos = centro.clone().add(new THREE.Vector3(1, -1.1, 0.8).normalize().multiplyScalar(dist));
  ctrl3d.setLookAt(pos.x, pos.y, pos.z, centro.x, centro.y, centro.z, !PRUEBA); // con transición suave
  ctrl3d.update(0);
  dibujar();
}

// ---------- mallas que manda el motor ----------
const decodificar = (b64, Tipo) => {
  const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  return new Tipo(bytes.buffer);
};

function grupoDe(piso) {
  if (!grupos.has(piso)) { const g = new THREE.Group(); grupos.set(piso, g); escena.add(g); }
  return grupos.get(piso);
}

function quitar(id) {
  const m = mallas.get(id);
  if (!m) return;
  m.parent.remove(m); m.geometry.dispose(); m.children.forEach((c) => c.geometry.dispose());
  mallas.delete(id);
}

function aplicarMallas(datos) {
  for (const el of datos.elementos) {
    quitar(el.id);
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(decodificar(el.v, Float32Array), 3));
    geo.setIndex(new THREE.BufferAttribute(decodificar(el.c, Uint32Array), 1));
    const plana = geo.toNonIndexed(); plana.computeVertexNormals(); geo.dispose();
    const malla = new THREE.Mesh(plana, matMuro);
    malla.add(new THREE.LineSegments(new THREE.EdgesGeometry(plana, 20), matBorde));
    malla.userData = { id: el.id, piso: el.piso };
    grupoDe(el.piso).add(malla);
    mallas.set(el.id, malla);
  }
  const existentes = new Set(datos.existentes);
  for (const id of [...mallas.keys()]) if (!existentes.has(id)) quitar(id);
}

// ---------- órdenes al motor ----------
let ultima = "";
async function ejecutar(cmd, args = {}) {
  const t0 = performance.now();
  const r = await bim.motor(cmd, args);
  if (!r.ok) { mostrarEstado(`No se pudo: ${r.error}`); return r; }
  const res = r.result;
  estado = res.estado || (res.pisos || res.proyecto === false ? res : estado);
  let mallasResp = null;
  if (["nuevo_proyecto", "deshacer", "rehacer"].includes(cmd)) {
    if (cmd === "nuevo_proyecto") { for (const id of [...mallas.keys()]) quitar(id); }
    mallasResp = await bim.motor("mallas", {});
  } else if (res.afectados) {
    mallasResp = await bim.motor("mallas", { ids: res.afectados });
  }
  const habiaElementos = mallas.size > 0;
  if (mallasResp && mallasResp.ok) aplicarMallas(mallasResp.result);
  actualizarPanel();
  if (!habiaElementos && mallas.size > 0) encuadrar(); // primer elemento del proyecto
  dibujar();
  r.total_ms = Math.round(performance.now() - t0);
  r.mallas_ms = mallasResp ? mallasResp.ida_vuelta_ms : 0;
  ultima = `${cmd}: ${r.total_ms} ms en total (motor ${r.ms} ms, ida y vuelta ${r.ida_vuelta_ms} ms` +
    (mallasResp ? `, formas 3D ${mallasResp.ida_vuelta_ms} ms` : "") + ")";
  mostrarEstado();
  return r;
}

const fmt = (n) => n.toFixed(2).replace(".", ",");
function actualizarPanel() {
  const cuerpo = $("pisos");
  cuerpo.innerHTML = "";
  if (!estado.proyecto) { $("proyecto").textContent = "No hay ningún proyecto abierto"; return; }
  for (const p of estado.pisos) {
    const fila = document.createElement("tr");
    fila.dataset.id = p.id;
    if (p.id === estado.activo) fila.className = "activo";
    fila.innerHTML = `<td>${p.id === estado.activo ? "● " : ""}${p.nombre}</td><td class="num">${fmt(p.cota)}</td><td class="num">${fmt(p.altura)}</td>`;
    fila.addEventListener("dblclick", () => ejecutar("activar_piso", { id: p.id }));
    cuerpo.appendChild(fila);
  }
  const nombre = estado.ruta ? estado.ruta.split(/[\\/]/).pop() : "Proyecto sin guardar";
  $("proyecto").innerHTML = nombre + (estado.sucio ? ' <span class="sucio">• Cambios sin guardar</span>' : "");
  const activo = estado.pisos.find((p) => p.id === estado.activo);
  $("etiqueta-planta").textContent = `Planta — ${activo ? activo.nombre : ""}`;
  bim.titulo(`${estado.sucio ? "* " : ""}${nombre} — BIM Simple`);
}
function mostrarEstado(texto) {
  $("estado").textContent = (texto ? texto + "\n" : "") + (ultima ? `Última orden: ${ultima}\n` : "") + `Elementos en pantalla: ${mallas.size}`;
}

// ---------- dibujo de muros en la planta ----------
const medida = $("medida");

function puntoEnPlanta(evento) {
  const caja = divPlanta.getBoundingClientRect();
  const ndc = new THREE.Vector3(((evento.clientX - caja.left) / caja.width) * 2 - 1, -((evento.clientY - caja.top) / caja.height) * 2 + 1, 0);
  ndc.unproject(camPlanta);
  let p = new THREE.Vector2(Math.round(ndc.x / 0.05) * 0.05, Math.round(ndc.y / 0.05) * 0.05); // grilla de 5 cm
  for (const m of mallas.values()) { // imán a vértices de muros del piso activo
    if (m.userData.piso !== estado.activo) continue;
    const pos = m.geometry.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const v = new THREE.Vector2(pos.getX(i), pos.getY(i));
      if (v.distanceTo(new THREE.Vector2(ndc.x, ndc.y)) < 0.25) { p = v; break; }
    }
  }
  if (evento.shiftKey && dibujo.p1) { // ángulos fijos de 45°
    const d = p.clone().sub(dibujo.p1);
    const ang = Math.round(Math.atan2(d.y, d.x) / (Math.PI / 4)) * (Math.PI / 4);
    p = dibujo.p1.clone().add(new THREE.Vector2(Math.cos(ang), Math.sin(ang)).multiplyScalar(d.length()));
  }
  return p;
}

function cotaActiva() { const p = estado.pisos && estado.pisos.find((x) => x.id === estado.activo); return p ? p.cota : 0; }

divPlanta.addEventListener("pointermove", (e) => {
  if (!dibujo.activo || !dibujo.p1) return;
  const p = puntoEnPlanta(e), z = cotaActiva() + 3.2;
  vistaPrevia.geometry.setFromPoints([new THREE.Vector3(dibujo.p1.x, dibujo.p1.y, z), new THREE.Vector3(p.x, p.y, z)]);
  medida.style.display = "block";
  medida.style.left = `${e.clientX - divPlanta.getBoundingClientRect().left + 14}px`;
  medida.style.top = `${e.clientY - divPlanta.getBoundingClientRect().top + 14}px`;
  medida.textContent = `${fmt(p.distanceTo(dibujo.p1))} m`;
  dibujar();
});
divPlanta.addEventListener("pointerdown", async (e) => {
  if (!dibujo.activo || !estado.proyecto) return;
  if (e.button === 2) return terminarMuro();
  if (e.button !== 0) return;
  const p = puntoEnPlanta(e);
  if (!dibujo.p1) { dibujo.p1 = p; return; }
  const r = await ejecutar("crear_muro", { p1: [dibujo.p1.x, dibujo.p1.y], p2: [p.x, p.y] });
  if (r.ok) dibujo.p1 = p; // los tramos se encadenan
});
divPlanta.addEventListener("contextmenu", (e) => e.preventDefault());
function terminarMuro() { dibujo.p1 = null; vistaPrevia.visible = false; medida.style.display = "none"; dibujar(); }
window.addEventListener("keydown", (e) => { if (e.key === "Escape") terminarMuro(); });

// ---------- botones y menú ----------
async function guardar(como = false) {
  if (!estado.proyecto) return;
  const r = (!como && estado.ruta) ? await ejecutar("guardar", { ruta: estado.ruta }) : await bim.guardarComo();
  if (r && r.ok) {
    estado = r.result.estado; actualizarPanel();
    mostrarEstado(`Guardado. Validación IFC4: ${r.result.errores} errores.`);
  }
}
const acciones = {
  nuevo: () => ejecutar("nuevo_proyecto"),
  piso: () => ejecutar("agregar_piso_arriba"),
  recinto: () => ejecutar("crear_recinto", { x: 0, y: 0, ancho: 6, largo: 4 }),
  deshacer: () => ejecutar("deshacer"),
  rehacer: () => ejecutar("rehacer"),
  guardar: () => guardar(false),
  guardar_como: () => guardar(true),
};
$("b-nuevo").onclick = acciones.nuevo;
$("b-piso").onclick = acciones.piso;
$("b-recinto").onclick = acciones.recinto;
$("b-deshacer").onclick = acciones.deshacer;
$("b-rehacer").onclick = acciones.rehacer;
$("b-guardar").onclick = acciones.guardar;
$("b-encuadrar").onclick = encuadrar;
$("b-muro").onclick = () => { dibujo.activo = !dibujo.activo; $("b-muro").classList.toggle("encendido", dibujo.activo); terminarMuro(); };
bim.alMenu((accion) => acciones[accion] && acciones[accion]());

// ---------- arranque ----------
const listo = await bim.motorListo();
mostrarEstado(`Motor listo (IfcOpenShell ${listo.ifcopenshell}) en ${listo.listo_ms} ms.`);
actualizarPanel();
dibujar();
if (PRUEBA) prueba(listo);

// ---------- prueba automática (ventana oculta) ----------
async function prueba(listo) {
  const r = { motor: listo, listo_en_ms: listo.listo_ms, pasos: [], capturas: [] };
  const paso = async (nombre, cmd, args) => {
    const resp = await ejecutar(cmd, args);
    r.pasos.push({ nombre, ok: resp.ok, error: resp.error, motor_ms: resp.ms, ida_vuelta_ms: resp.ida_vuelta_ms, formas_3d_ms: resp.mallas_ms, total_ms: resp.total_ms });
    return resp;
  };
  const captura = async (nombre) => { encuadrar(); await new Promise((ok) => setTimeout(ok, 600)); r.capturas.push({ nombre, tamaño: await bim.captura(nombre) }); };

  await bim.captura("0_calentamiento"); // la primera captura de una ventana oculta devuelve un cuadro viejo
  await paso("Nuevo proyecto", "nuevo_proyecto");
  await paso("Agregar piso arriba (Piso 1)", "agregar_piso_arriba");
  await paso("Agregar piso arriba (Piso 2)", "agregar_piso_arriba");
  await paso("Recinto de 4 muros unidos en Planta Baja", "crear_recinto", { x: 0, y: 0, ancho: 6, largo: 4 });
  await paso("Muro suelto unido en esquina", "crear_muro", { p1: [6, 4], p2: [9, 4] });
  await paso("Muro encadenado", "crear_muro", { p1: [9, 4], p2: [9, 7] });
  await captura("1_planta_baja");

  // Activar Piso 1 con doble clic, como lo haría el usuario.
  const fila = [...document.querySelectorAll("#pisos tr")].find((tr) => tr.textContent.includes("Piso 1"));
  const t0 = performance.now();
  fila.dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
  await new Promise((ok) => setTimeout(ok, 200));
  r.doble_clic_activa_piso = { activo: estado.pisos.find((p) => p.id === estado.activo).nombre, ms_aprox: Math.round(performance.now() - t0) };
  await paso("Recinto en Piso 1", "crear_recinto", { x: 1, y: 1, ancho: 4, largo: 3 });
  await captura("2_piso_1");

  await paso("Deshacer (Ctrl+Z)", "deshacer");
  await captura("3_despues_de_deshacer");
  await paso("Rehacer", "rehacer");
  const g = await paso("Guardar IFC y validar", "guardar", { ruta: PARAMS.get("salida") + "\\prueba_prototipo.ifc" });
  r.validacion = g.ok ? { errores: g.result.errores, mensajes: g.result.mensajes } : g.error;
  await paso("Cambio después de guardar", "crear_muro", { p1: [1, 1], p2: [1, -1] });
  r.estado_final = estado;
  r.elementos_en_pantalla = mallas.size;
  r.titulo_ventana = document.title;
  await bim.finPrueba(r);
}
