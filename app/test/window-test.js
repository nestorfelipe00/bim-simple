// Prueba del programa con la ventana oculta (constitución, Principio V). La carga app.js con ?test=1.
// Recorre las acciones como lo haría el usuario, captura la pantalla y escribe app/test-output/resultado.json.
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const $ = (id) => document.getElementById(id);
const NAVIGATOR_LIMIT_MS = 200; // SC-004

const EXPECTED_MENUS = [
  { label: "Archivo", items: ["Nuevo proyecto", "Abrir IFC…", "Guardar IFC", "Guardar IFC como…", "Salir"] },
  { label: "Edición", items: ["Deshacer", "Rehacer"] },
  { label: "Opciones", items: ["Estructuras compuestas…"] },
  { label: "Ayuda", items: ["Acerca de BIM Simple"] },
];

export async function run(app) {
  const result = { steps: [], captures: [], failures: 0, closeWithChanges: false };
  const t = {
    app,
    step(section, name, ok, detail) {
      result.steps.push({ section, name, ok: !!ok, detail });
      if (!ok) result.failures += 1;
    },
    // Acción del navegador de pisos: además de su comprobación, no puede tardar más de 200 ms (SC-004).
    async navigatorAction(section, name, action, check) {
      const started = performance.now();
      const response = await action();
      const ms = Math.round(performance.now() - started);
      const detail = { ms, error: response && !response.ok ? response.error : undefined };
      t.step(section, `${name} (${ms} ms)`, check(response) && ms <= NAVIGATOR_LIMIT_MS, detail);
      return response;
    },
    async capture(name) {
      app.viewports.draw();
      await sleep(600);
      result.captures.push({ name, size: await bim.test.capture(name) });
    },
    tableRows() {
      return [...$("storeys").querySelectorAll("tr")].map((tr) => [...tr.children].map((td) => td.textContent));
    },
    sleep,
    result,
  };

  try {
    await bim.test.capture("calentamiento"); // la primera captura de una ventana oculta devuelve un cuadro viejo
    await environment(t);
    for (const section of SECTIONS) await section(t);
    if (result.closeWithChanges) {
      // Deja un proyecto con cambios sin guardar para el último paso: cerrar con la X (FR-010).
      await app.handleAction("new");
      await app.handleAction("add-above");
    }
  } catch (error) {
    t.step("Error", "Excepción durante la prueba", false, String((error && error.stack) || error));
  }
  await bim.test.finish(result);
}

// Secciones de cada historia (se agregan en orden: Historia 1, 2, 3, 4, Motor detenido).
const SECTIONS = [];
export function addSection(fn) {
  SECTIONS.push(fn);
}

async function environment(t) {
  const S = "Entorno";
  t.step(S, `Motor listo en menos de 10 s (SC-007): ${t.app.ready.ready_ms} ms`, t.app.ready.ready_ms < 10000);
  t.step(S, "IfcOpenShell 0.9.0 en el motor", t.app.ready.ifcopenshell === "0.9.0", t.app.ready.ifcopenshell);
  const menus = await bim.test.menuLabels();
  t.step(S, "Menús Archivo, Edición, Opciones y Ayuda con sus textos (FR-003, FR-030)", JSON.stringify(menus) === JSON.stringify(EXPECTED_MENUS), menus);
  t.step(S, "Título sin proyecto: «BIM Simple»", (await bim.test.windowTitle()) === "BIM Simple");
  t.step(S, "Arranca sin proyecto (FR-006)", $("project").textContent === "No hay ningún proyecto abierto" && !t.app.getState().has_project);
  t.step(S, "Vistas vacías al arrancar (FR-006)", t.app.meshes.size === 0);
  await t.capture("base");
}

// ---------- Historia 1: abrir BIM Simple, empezar un proyecto y guardarlo ----------
async function waitFor(condition, timeoutMs = 10000, intervalMs = 100) {
  const started = performance.now();
  while (performance.now() - started < timeoutMs) {
    if (condition()) return true;
    await sleep(intervalMs);
  }
  return false;
}

addSection(async function historia1(t) {
  const S = "Historia 1";
  await t.app.handleAction("new"); // Archivo > Nuevo proyecto
  t.step(S, "Nuevo proyecto: «● Planta Baja | 0,00 | 3,00» (FR-007)", JSON.stringify(t.tableRows()) === JSON.stringify([["● Planta Baja", "0,00", "3,00"]]), t.tableRows());
  t.step(S, "Título: «Proyecto sin guardar — BIM Simple» (FR-004)", (await bim.test.windowTitle()) === "Proyecto sin guardar — BIM Simple", await bim.test.windowTitle());

  const output = await bim.test.outputDir();
  const path = `${output}\\prueba.ifc`;
  await bim.test.answerDialogs([path]); // el diálogo "Guardar IFC como" responde con esta ruta
  const saved = await t.app.handleAction("save"); // Guardar IFC sin ruta → Guardar como
  t.step(S, "Guardar IFC en un proyecto nuevo pide la ruta y guarda (FR-009)", saved && saved.ok && saved.result.path === path, saved);
  t.step(S, "Título: «prueba.ifc — BIM Simple»", (await bim.test.windowTitle()) === "prueba.ifc — BIM Simple", await bim.test.windowTitle());
  const validated = await waitFor(() => document.getElementById("messages").textContent === "Guardado. Validación IFC4: 0 errores.");
  t.step(S, "Validación en segundo plano: «Guardado. Validación IFC4: 0 errores.» (SC-003)", validated, document.getElementById("messages").textContent);

  await bim.about(); // Ayuda > Acerca de BIM Simple
  const log = await bim.test.dialogLog();
  const about = log.dialogs.find((d) => d.title === "Acerca de BIM Simple");
  t.step(S, "Acerca de: aviso LGPL-3.0 de IfcOpenShell con su enlace (FR-003, Principio VI)", about && about.message.includes("IfcOpenShell 0.9.0 — LGPL-3.0") && about.message.includes("https://github.com/IfcOpenShell/IfcOpenShell"), about);
  t.step(S, "Acerca de: BIM Simple bajo GPL-3.0 o posterior, con el enlace a su código (Principio VI)", about && about.message.includes("GPL-3.0 o posterior") && about.message.includes("https://github.com/nestorfelipe00/bim-simple"), about);
  await t.capture("h1");
});

addSection(async function historia1Panel(t) {
  const S = "Historia 1";
  const actions = document.getElementById("no-project-actions");
  t.step(S, "Con proyecto abierto se ocultan «Nuevo proyecto» y «Abrir IFC…» del panel (ui.md)", getComputedStyle(actions).display === "none");
});

// ---------- Historia 2: organizar los pisos ----------
async function editSelected(t, rowName, values) {
  // Selecciona la fila con un clic, abre "Editar piso…", completa el diálogo y pulsa Aceptar.
  const row = [...document.querySelectorAll("#storeys tr")].find((tr) => tr.firstChild.textContent.replace("● ", "") === rowName);
  row.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  const pending = t.app.handleAction("edit");
  await sleep(50);
  for (const [field, value] of Object.entries(values)) document.getElementById(`edit-${field}`).value = value;
  const started = performance.now();
  document.getElementById("edit-ok").click();
  const response = await pending;
  // SC-004 mide la acción (orden, respuesta y redibujo: total_ms de dispatch). El cierre del diálogo en una
  // ventana oculta llega con ~1 s de retraso por cómo Chromium agenda esas tareas; se registra aparte.
  return { response, ms: response ? response.total_ms : null, withDialogMs: Math.round(performance.now() - started) };
}

addSection(async function historia2(t) {
  const S = "Historia 2";
  await t.app.handleAction("new");
  await t.navigatorAction(S, "Agregar piso arriba", () => t.app.handleAction("add-above"), (r) => r.ok);
  await t.navigatorAction(S, "Agregar piso arriba", () => t.app.handleAction("add-above"), (r) => r.ok);
  await t.navigatorAction(S, "Agregar piso abajo", () => t.app.handleAction("add-below"), (r) => r.ok);
  const expected = [["Piso 2", "6,00", "3,00"], ["Piso 1", "3,00", "3,00"], ["● Planta Baja", "0,00", "3,00"], ["Sótano 1", "-3,00", "3,00"]];
  t.step(S, "Cuatro pisos en orden, el más alto arriba (FR-012 a FR-014)", JSON.stringify(t.tableRows()) === JSON.stringify(expected), t.tableRows());

  const edit = await editSelected(t, "Planta Baja", { height: "3,50" });
  t.step(S, `Editar piso: altura de Planta Baja 3,50 → Piso 1 a 3,50 y Piso 2 a 6,50 (FR-016) (${edit.ms} ms)`,
    edit.response.ok && edit.ms <= 200 && JSON.stringify(t.tableRows().slice(0, 3)) === JSON.stringify([["Piso 2", "6,50", "3,00"], ["Piso 1", "3,50", "3,00"], ["● Planta Baja", "0,00", "3,50"]]), t.tableRows());

  const before = JSON.stringify(t.tableRows());
  const invalid = await editSelected(t, "Piso 1", { elevation: "0,00" });
  t.step(S, "Cota inválida: mensaje exacto y la tabla no cambia",
    !invalid.response.ok && document.getElementById("messages").textContent === "La cota debe ser mayor que la del piso de abajo («Planta Baja», 0,00 m)." && JSON.stringify(t.tableRows()) === before,
    document.getElementById("messages").textContent);

  const sotano = [...document.querySelectorAll("#storeys tr")].find((tr) => tr.firstChild.textContent === "Sótano 1");
  sotano.dispatchEvent(new MouseEvent("click", { bubbles: true }));
  await t.navigatorAction(S, "Borrar «Sótano 1» (sin elementos, sin preguntar)", () => t.app.handleAction("delete"), (r) => r.ok && t.tableRows().length === 3);

  await t.navigatorAction(S, "Edición > Deshacer: vuelve «Sótano 1»", () => t.app.handleAction("undo"), (r) => r.ok && t.tableRows().length === 4);
  await t.navigatorAction(S, "Edición > Rehacer: se borra de nuevo", () => t.app.handleAction("redo"), (r) => r.ok && t.tableRows().length === 3);
  t.step(S, "Título con cambios sin guardar empieza con «* »", (await bim.test.windowTitle()).startsWith("* "), await bim.test.windowTitle());

  // Pregunta por cambios sin guardar (FR-010): Nuevo proyecto + Cancelar no cambia nada.
  const rows = JSON.stringify(t.tableRows());
  await bim.test.answerDialogs(["Cancelar"]);
  await t.app.handleAction("new");
  const log = await bim.test.dialogLog();
  const last = log.dialogs[log.dialogs.length - 1];
  t.step(S, "Nuevo proyecto con cambios: pregunta «¿Guardar cambios antes de cerrar?» y «Cancelar» no cambia nada",
    last && last.message === "¿Guardar cambios antes de cerrar?" && last.answer === "Cancelar" && JSON.stringify(t.tableRows()) === rows, last);
  await t.capture("h2");
  t.result.closeWithChanges = true; // el último paso de la prueba cierra la ventana con cambios (lo registra el proceso principal)
});

// ---------- Historia 3: trabajar en un piso ----------
function rowByName(name) {
  return [...document.querySelectorAll("#storeys tr")].find((tr) => tr.firstChild.textContent.replace("● ", "") === name);
}

addSection(async function historia3(t) {
  const S = "Historia 3";
  const fixtures = await bim.test.fixtures();
  t.step(S, "IFC de prueba generados con engine/tests/make_fixtures.py", fixtures && fixtures.ok, fixtures);
  // Abrir con_elementos.ifc (3 pisos con un muro cada uno); hay cambios de la Historia 2: «No guardar».
  await bim.test.answerDialogs(["No guardar", `${fixtures.folder}\\con_elementos.ifc`]);
  const opened = await t.app.handleAction("open");
  const ids = Object.fromEntries(t.app.getState().storeys.map((s) => [s.name, s.id]));
  t.step(S, "Abrir «con_elementos.ifc»: 3 pisos y activa «Planta Baja»",
    opened && opened.ok && JSON.stringify(t.tableRows().map((r) => r[0])) === JSON.stringify(["Piso 2", "Piso 1", "● Planta Baja"]), t.tableRows());
  t.app.viewports.draw();
  const all = [ids["Planta Baja"], ids["Piso 1"], ids["Piso 2"]].sort();
  t.step(S, "El 3D muestra los elementos de los 3 pisos (FR-002)", JSON.stringify(t.app.viewports.debugVisible3dStoreys().sort()) === JSON.stringify(all), t.app.viewports.debugVisible3dStoreys());

  // Doble clic en "Piso 1" (FR-020): pasa a ser el único activo y la planta muestra solo sus elementos.
  await t.navigatorAction(S, "Doble clic en «Piso 1» lo activa", async () => {
    rowByName("Piso 1").dispatchEvent(new MouseEvent("dblclick", { bubbles: true }));
    const done = await waitFor(() => t.app.getState().active_storey_id === ids["Piso 1"] && rowByName("Piso 1").classList.contains("active"), 2000, 2);
    return { ok: done };
  }, (r) => r.ok);
  const plan = t.app.viewports.debugVisiblePlanStoreys();
  t.step(S, "Un solo piso activo (FR-021) y la planta muestra solo «Piso 1» (FR-022)",
    t.tableRows().filter((r) => r[0].startsWith("● ")).length === 1 && JSON.stringify(plan) === JSON.stringify([ids["Piso 1"]]), { plan, rows: t.tableRows() });
  t.step(S, "Etiqueta de la planta: «Planta — Piso 1»", document.getElementById("plan-label").textContent === "Planta — Piso 1", document.getElementById("plan-label").textContent);
  t.step(S, "Activar no marca cambios sin guardar", !t.app.getState().dirty && !(await bim.test.windowTitle()).startsWith("* "), await bim.test.windowTitle());
  t.step(S, "El 3D sigue mostrando los 3 pisos", JSON.stringify(t.app.viewports.debugVisible3dStoreys().sort()) === JSON.stringify(all), t.app.viewports.debugVisible3dStoreys());

  // Borrar un piso con elementos (FR-017): primero «Cancelar», después «Borrar».
  rowByName("Piso 2").dispatchEvent(new MouseEvent("click", { bubbles: true }));
  const rows = JSON.stringify(t.tableRows());
  await bim.test.answerDialogs(["Cancelar"]);
  await t.app.handleAction("delete");
  let log = await bim.test.dialogLog();
  let last = log.dialogs[log.dialogs.length - 1];
  t.step(S, "Borrar «Piso 2» con 1 elemento: pregunta con el texto exacto y «Cancelar» no borra nada",
    last && last.message === "El piso «Piso 2» tiene 1 elemento. Se borrarán junto con el piso." && last.answer === "Cancelar" && JSON.stringify(t.tableRows()) === rows, last);
  await bim.test.answerDialogs(["Borrar"]);
  const deleted = await t.app.handleAction("delete");
  log = await bim.test.dialogLog();
  last = log.dialogs[log.dialogs.length - 1];
  t.step(S, "Con «Borrar»: el piso y su muro desaparecen de la tabla y de la escena",
    deleted && deleted.ok && last.answer === "Borrar" && !rowByName("Piso 2") && !t.app.viewports.debugVisible3dStoreys().includes(ids["Piso 2"]),
    { rows: t.tableRows(), view3d: t.app.viewports.debugVisible3dStoreys() });

  await t.app.handleAction("fit"); // botón Encuadrar
  await t.capture("h3");
});

// ---------- Historia 4: abrir un IFC existente ----------
addSection(async function historia4(t) {
  const S = "Historia 4";
  const { folder } = await bim.test.fixtures();
  const lastDialog = async () => {
    const log = await bim.test.dialogLog();
    return log.dialogs[log.dialogs.length - 1];
  };

  // Hay cambios de la Historia 3: «No guardar» y después el archivo elegido en el diálogo Abrir IFC.
  await bim.test.answerDialogs(["No guardar", `${folder}\\otro_programa_mm.ifc`]);
  const opened = await t.app.handleAction("open");
  t.step(S, "Abrir «otro_programa_mm.ifc» (milímetros): 4 pisos en metros, activo «Nivel 0» (FR-008)",
    opened && opened.ok && JSON.stringify(t.tableRows()) === JSON.stringify([["Nivel 2", "6,00", "3,00"], ["Nivel 1", "3,20", "2,80"], ["● Nivel 0", "0,00", "3,20"], ["Subsuelo", "-2,80", "2,80"]]),
    t.tableRows());
  t.step(S, "Título: «otro_programa_mm.ifc — BIM Simple»", (await bim.test.windowTitle()) === "otro_programa_mm.ifc — BIM Simple", await bim.test.windowTitle());

  // Un archivo dañado no cambia nada (FR-011).
  const rows = JSON.stringify(t.tableRows());
  await bim.test.answerDialogs([`${folder}\\danado.ifc`]);
  const broken = await t.app.handleAction("open");
  t.step(S, "Abrir «danado.ifc»: mensaje exacto y el proyecto abierto no cambia (FR-011)",
    broken && !broken.ok && document.getElementById("messages").textContent === "No se pudo abrir «danado.ifc»: no es un archivo IFC válido." && JSON.stringify(t.tableRows()) === rows && (await bim.test.windowTitle()) === "otro_programa_mm.ifc — BIM Simple",
    document.getElementById("messages").textContent);

  // Aviso de varios edificios en el panel.
  await bim.test.answerDialogs([`${folder}\\dos_edificios.ifc`]);
  await t.app.handleAction("open");
  const notice = document.getElementById("notice");
  t.step(S, "Aviso en el panel: «El archivo tiene 2 edificios; se muestran los pisos de «Edificio A»»",
    !notice.hidden && notice.textContent === "El archivo tiene 2 edificios; se muestran los pisos de «Edificio A»", notice.textContent);

  // Pregunta por cambios sin guardar (FR-010): agregar un piso; Abrir IFC… con «Cancelar» y después con «No guardar».
  await t.app.handleAction("add-above");
  const changed = JSON.stringify(t.tableRows());
  await bim.test.answerDialogs(["Cancelar"]);
  await t.app.handleAction("open");
  const asked = await lastDialog();
  t.step(S, "Abrir IFC… con cambios: pregunta «¿Guardar cambios antes de cerrar?» y «Cancelar» no cambia nada",
    asked && asked.message === "¿Guardar cambios antes de cerrar?" && asked.answer === "Cancelar" && JSON.stringify(t.tableRows()) === changed, asked);
  await bim.test.answerDialogs(["No guardar", `${folder}\\con_elementos.ifc`]);
  const reopened = await t.app.handleAction("open");
  t.step(S, "Con «No guardar» se abre el archivo elegido",
    reopened && reopened.ok && JSON.stringify(t.tableRows().map((r) => r[0])) === JSON.stringify(["Piso 2", "Piso 1", "● Planta Baja"]) && document.getElementById("notice").hidden,
    t.tableRows());
  await t.capture("h4");
});

// ---------- Motor detenido (ui.md, "Motor detenido") ----------
addSection(async function motorDetenido(t) {
  const S = "Motor detenido";
  const NOTICE = "El motor de BIM Simple se detuvo. Los cambios sin guardar se perdieron; el último archivo guardado no se modificó.";
  await t.app.handleAction("add-above"); // cambios sin guardar que se pierden
  await bim.test.killEngine();
  const restarted = await waitFor(() => document.getElementById("messages").textContent === NOTICE && !t.app.getState().has_project, 15000, 20);
  t.step(S, "Aviso exacto y el programa queda sin proyecto", restarted, { message: document.getElementById("messages").textContent, has_project: t.app.getState().has_project });
  const ready = await bim.engineReady();
  t.step(S, "El motor vuelve a estar listo", ready && ready.ready === true && ready.ifcopenshell === "0.9.0", ready);
  t.step(S, "Título «BIM Simple» y panel «No hay ningún proyecto abierto»",
    (await bim.test.windowTitle()) === "BIM Simple" && document.getElementById("project").textContent === "No hay ningún proyecto abierto" && t.app.meshes.size === 0,
    await bim.test.windowTitle());
  const created = await t.app.handleAction("new");
  t.step(S, "Las órdenes siguientes funcionan: Nuevo proyecto", created && created.ok && JSON.stringify(t.tableRows()) === JSON.stringify([["● Planta Baja", "0,00", "3,00"]]), t.tableRows());
  await t.capture("motor");
});

// ---------- Función 002: muros con capas (specs/002-muros-capas) ----------
const WALL_LIMIT_MS = 200; // SC-006

// Evento del ratón en el punto (x, y) de la planta, como lo recibe app.js.
function at(t, x, y, extra = {}) {
  return { ...t.app.viewports.worldToClient(x, y), button: 0, shiftKey: false, ...extra };
}

async function click(t, x, y, extra = {}) {
  t.app.planPointer("move", at(t, x, y, extra));
  return t.app.planPointer("down", at(t, x, y, extra));
}

async function press(t, ...keys) {
  for (const key of keys) await t.app.keyDown({ key, target: document.body, preventDefault() {} });
}

// Proyecto nuevo con pisos a 0,00, 3,00 y 6,00 y el Piso 1 activo.
async function threeStoreys(t) {
  await t.app.handleAction("new");
  await t.app.handleAction("add-above");
  await t.app.handleAction("add-above");
  const piso1 = t.app.getState().storeys.find((s) => s.name === "Piso 1").id;
  await t.app.handleAction("activate", piso1);
  return piso1;
}

// Superficie en planta: área de los triángulos de arriba (normal +Z) de las mallas de muro del piso.
function planArea(t, storeyId) {
  let area = 0;
  for (const mesh of t.app.meshes.byId.values()) {
    if (!mesh.userData.wall || mesh.userData.storeyId !== storeyId) continue;
    const p = mesh.geometry.attributes.position.array;
    for (let i = 0; i < p.length; i += 9) {
      const ux = p[i + 3] - p[i], uy = p[i + 4] - p[i + 1], uz = p[i + 5] - p[i + 2];
      const vx = p[i + 6] - p[i], vy = p[i + 7] - p[i + 1], vz = p[i + 8] - p[i + 2];
      const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
      const length = Math.hypot(nx, ny, nz);
      if (length > 0 && nz / length > 0.99) area += length / 2;
    }
  }
  return area;
}

const near = (a, b, tolerance = 0.001) => Math.abs(a - b) <= tolerance;
const selectedText = (id) => {
  const select = document.getElementById(id);
  return select.options[select.selectedIndex] ? select.options[select.selectedIndex].textContent : "";
};

addSection(async function muros1(t) {
  const S = "Muros 1 — dibujar";
  const piso1 = await threeStoreys(t);
  t.step(S, "Al crear un proyecto queda activa la Flecha (FR-001)", t.app.getTool() === "arrow" && document.querySelector('#toolbox button[data-tool="arrow"]').classList.contains("active"));
  document.querySelector('#toolbox button[data-tool="wall"]').click(); // caja de herramientas > Muro
  const reference = document.querySelector("#ib-reference button.on");
  t.step(S, "Info Box del Muro: Básica, Hormigón, 0,20, altura del piso 3,00 y Exterior (FR-003)",
    t.app.getTool() === "wall" && selectedText("ib-structure") === "Básica" && selectedText("ib-material") === "Hormigón" &&
    document.getElementById("ib-thickness").value === "0,20" && document.getElementById("ib-height").value === "3,00" && reference && reference.dataset.reference === "exterior",
    { structure: selectedText("ib-structure"), material: selectedText("ib-material"), thickness: document.getElementById("ib-thickness").value, height: document.getElementById("ib-height").value });

  // Rectángulo de 6 × 4 m en sentido horario: 4 clics y un clic en el primer punto (FR-005, FR-010).
  const times = [];
  for (const [x, y] of [[0, 4], [6, 4], [6, 0], [0, 0], [0, 4]]) {
    const response = await click(t, x, y);
    if (response) times.push(response.total_ms);
  }
  const walls = t.app.meshes.walls(piso1);
  t.step(S, "4 clics y clic en el primer punto: 4 muros en el Piso 1 y la cadena terminó (FR-005, FR-010, FR-013)",
    walls.length === 4 && t.app.wallTool.chain === null && walls.every((w) => w.kind === "regenerable" && near(w.thickness, 0.2) && near(w.height, 3)), walls.length);
  const area = planArea(t, piso1);
  t.step(S, `Superficie en planta ${area.toFixed(4)} m² = 3,84 ± 0,1 %: esquinas sin huecos ni superposiciones (SC-002)`, Math.abs(area - 3.84) <= 3.84 * 0.001, area);
  t.step(S, `Cada muro con su redibujo en < ${WALL_LIMIT_MS} ms (SC-006): ${times.join(", ")} ms`, times.length === 4 && times.every((ms) => ms < WALL_LIMIT_MS), times);

  // Cambiar de piso termina la cadena (casos límite).
  await click(t, 20, 0);
  const pb = t.app.getState().storeys.find((s) => s.name === "Planta Baja").id;
  await t.app.handleAction("activate", pb);
  const ended = t.app.wallTool.chain === null;
  await t.app.handleAction("activate", piso1);
  t.step(S, "Cambiar de piso activo termina la cadena", ended);

  // Shift (45°) y longitud escrita (FR-007, FR-008).
  await click(t, 10, 0);
  t.app.planPointer("move", at(t, 13, 2.9, { shiftKey: true }));
  await press(t, "4", ",", "5", "Enter");
  const diagonal = t.app.meshes.walls(piso1).find((w) => near(w.start[0], 10) && near(w.start[1], 0));
  const expectedEnd = 10 + 4.5 * Math.SQRT1_2;
  t.step(S, "Shift + «4,5» + Enter: muro de 4,50 m a 45° (FR-007, FR-008)",
    diagonal && near(diagonal.end[0], expectedEnd) && near(diagonal.end[1], 4.5 * Math.SQRT1_2), diagonal);
  await press(t, "Escape");
  t.step(S, "Esc termina la cadena (FR-010)", t.app.wallTool.chain === null);

  // Imán al extremo de un muro existente (FR-009): un clic a 5 px de la esquina (6, 0).
  const corner = at(t, 6, 0);
  const nearCorner = { ...corner, clientX: corner.clientX + 5 };
  t.app.planPointer("move", nearCorner);
  await t.app.planPointer("down", nearCorner);
  const snapped = t.app.wallTool.chain && t.app.wallTool.chain.first;
  await click(t, 6, -3);
  await press(t, "Escape");
  const fromCorner = t.app.meshes.walls(piso1).find((w) => near(w.end[1], -3));
  t.step(S, "Imán: un clic a 5 px de un extremo empieza el muro exactamente en el extremo (FR-009)",
    snapped && snapped.x === 6 && snapped.y === 0 && fromCorner && near(fromCorner.start[0], 6, 1e-6) && near(fromCorner.start[1], 0, 1e-6), { snapped, fromCorner });

  // Un muro de menos de 1 cm no se crea (casos límite).
  const count = t.app.meshes.walls(piso1).length;
  await click(t, 30, 0);
  await click(t, 30.004, 0);
  await press(t, "Escape");
  t.step(S, "Un muro de menos de 1 cm no se crea", t.app.meshes.walls(piso1).length === count);

  t.app.viewports.fit({ animate: false });
  await t.capture("m1");
});

// Elige una opción de una lista del Info Box por su texto, como el usuario.
function choose(id, text) {
  const select = document.getElementById(id);
  const option = [...select.options].find((o) => o.textContent === text);
  if (!option) return false;
  select.value = option.value;
  select.dispatchEvent(new Event("change", { bubbles: true }));
  return true;
}

function setInput(element, value) {
  element.value = value;
  element.dispatchEvent(new Event("input", { bubbles: true }));
  element.dispatchEvent(new Event("change", { bubbles: true }));
}

function listItem(name) {
  return [...document.querySelectorAll("#sd-list li")].find((li) => li.firstChild.textContent === name);
}

addSection(async function muros2(t) {
  const S = "Muros 2 — compuestos";
  const piso1 = await threeStoreys(t);
  t.app.setTool("wall");
  choose("ib-structure", "Muro exterior 30");
  t.step(S, "«Muro exterior 30» en el Info Box: espesor 0,30 desactivado y material «—» (FR-003)",
    document.getElementById("ib-thickness").value === "0,30" && document.getElementById("ib-thickness").disabled &&
    selectedText("ib-material") === "—" && document.getElementById("ib-material").disabled);
  for (const [x, y] of [[0, 0], [5, 0], [5, 4]]) await click(t, x, y);
  await press(t, "Escape");
  const drawn = t.app.meshes.walls(piso1);
  const state = t.app.getState();
  const color = (name) => state.materials.find((m) => m.name === name).color;
  const expected = ["Revoque", "Ladrillo", "Aislación", "Revoque"].map((n) => color(n).slice(1));
  const colorsOk = drawn.every((w) => {
    const mesh = t.app.meshes.byId.get(w.id);
    return mesh.geometry.groups.length === 4 && mesh.userData.material.map((m) => m.color.getHexString()).join() === expected.join();
  });
  t.step(S, "2 muros compuestos: 4 grupos con los colores del catálogo (FR-017)", drawn.length === 2 && colorsOk, drawn.map((w) => w.layers.length));

  // Opciones > Estructuras compuestas…: crear "Muro de prueba" con 3 capas.
  let pending = t.app.handleAction("structures");
  await sleep(50);
  const opened = document.getElementById("structures-dialog").open;
  document.getElementById("sd-new").click();
  setInput(document.getElementById("sd-name"), "Muro de prueba");
  document.getElementById("sd-add-layer").click();
  document.getElementById("sd-add-layer").click();
  const inputs = () => [...document.querySelectorAll("#sd-layers input")];
  setInput(inputs()[0], "0,15");
  t.step(S, "El diálogo muestra el espesor total: «Espesor total: 0,35 m»", opened && document.getElementById("sd-total").textContent === "Espesor total: 0,35 m", document.getElementById("sd-total").textContent);
  document.getElementById("sd-ok").click();
  let response = await pending;
  t.step(S, "Aceptar crea «Muro de prueba» y aparece en la lista del Info Box (FR-015)",
    response && response.ok && [...document.getElementById("ib-structure").options].some((o) => o.textContent === "Muro de prueba"),
    response && response.error);

  // Renombrar a un nombre que ya existe: error exacto y el diálogo sigue abierto.
  pending = t.app.handleAction("structures");
  await sleep(50);
  listItem("Muro de prueba").click();
  setInput(document.getElementById("sd-name"), "Muro exterior 30");
  document.getElementById("sd-ok").click();
  await waitFor(() => !document.getElementById("sd-error").hidden, 3000, 20);
  t.step(S, "Nombre repetido: «Ya existe una estructura llamada «Muro exterior 30».» y el diálogo sigue abierto",
    document.getElementById("sd-error").textContent === "Ya existe una estructura llamada «Muro exterior 30»." && document.getElementById("structures-dialog").open,
    document.getElementById("sd-error").textContent);
  document.getElementById("sd-cancel").click();
  await pending;

  // Editar la Aislación de "Muro exterior 30" a 0,08: los muros dibujados cambian (FR-015).
  pending = t.app.handleAction("structures");
  await sleep(50);
  listItem("Muro exterior 30").click();
  setInput(inputs()[2], "0,08");
  document.getElementById("sd-ok").click();
  response = await pending;
  const thick = () => t.app.meshes.walls(piso1).map((w) => w.thickness);
  t.step(S, "Aislación 0,08: los 2 muros que usan «Muro exterior 30» pasan a 0,33 (FR-015)",
    response && response.ok && thick().every((v) => near(v, 0.33)), thick());
  await t.app.handleAction("undo");
  t.step(S, "Ctrl+Z: los muros vuelven a 0,30 (un solo paso de deshacer)", thick().every((v) => near(v, 0.3)), thick());
  t.app.viewports.fit({ animate: false });
  await t.capture("m2");
});
