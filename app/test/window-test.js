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
