// Lanza el motor BIM (Python + IfcOpenShell) y le habla por stdin/stdout, una línea JSON por mensaje
// (contracts/core_api.md). Si el motor se cae sin que se lo pida, rechaza las órdenes pendientes,
// avisa y lo vuelve a lanzar.
const { spawn } = require("child_process");
const { EventEmitter } = require("events");
const fs = require("fs");
const path = require("path");
const readline = require("readline");

class Engine extends EventEmitter {
  constructor({ pythonExe, logFile, restartOnCrash = true }) {
    super();
    this.pythonExe = pythonExe;
    this.logFile = logFile;
    this.restartOnCrash = restartOnCrash;
    this.process = null;
    this.pending = new Map();
    this.nextId = 1;
    this.stopping = false;
  }

  start() {
    this.stopping = false;
    this.readyPromise = new Promise((resolve, reject) => {
      this.resolveReady = resolve;
      this.rejectReady = reject;
    });
    const started = Date.now();
    this.process = spawn(this.pythonExe, ["-u", "-m", "bimsimple_engine"], {
      windowsHide: true,
      stdio: ["pipe", "pipe", "pipe"],
    });
    this.process.on("error", (error) => this.rejectReady(error));
    readline.createInterface({ input: this.process.stdout }).on("line", (line) => this.onLine(line, started));
    this.process.stderr.on("data", (data) => this.log(data));
    this.process.on("exit", (code) => this.onExit(code));
    return this.readyPromise;
  }

  onLine(line, started) {
    let message;
    try {
      message = JSON.parse(line);
    } catch {
      this.log(`Línea no válida del motor: ${line}\n`);
      return;
    }
    if (message.id === 0) {
      this.resolveReady({ ...message.result, ready_ms: Date.now() - started });
      return;
    }
    const waiting = this.pending.get(message.id);
    if (!waiting) return;
    this.pending.delete(message.id);
    message.round_trip_ms = Date.now() - waiting.started;
    waiting.resolve(message);
  }

  onExit(code) {
    const crashed = !this.stopping;
    for (const waiting of this.pending.values()) {
      waiting.resolve({ ok: false, error: "El motor de BIM Simple se detuvo antes de responder." });
    }
    this.pending.clear();
    this.process = null;
    if (crashed) {
      this.log(`El motor terminó inesperadamente (código ${code}).\n`);
      this.emit("crashed", code);
      if (this.restartOnCrash) this.start().then((info) => this.emit("restarted", info), () => {});
    }
  }

  ready() {
    return this.readyPromise;
  }

  async request(cmd, args = {}) {
    await this.readyPromise;
    if (!this.process) return { ok: false, error: "El motor de BIM Simple no está disponible." };
    return new Promise((resolve) => {
      const id = this.nextId++;
      this.pending.set(id, { resolve, started: Date.now() });
      this.process.stdin.write(JSON.stringify({ id, cmd, args }) + "\n");
    });
  }

  stop() {
    this.stopping = true;
    if (this.process) {
      this.process.stdin.end();
      const proceso = this.process;
      setTimeout(() => proceso.exitCode === null && proceso.kill(), 3000);
    }
  }

  // Solo para la prueba del programa: simula que el motor se cae.
  killForTest() {
    if (this.process) this.process.kill();
  }

  log(data) {
    if (!this.logFile) return;
    fs.mkdirSync(path.dirname(this.logFile), { recursive: true });
    fs.appendFileSync(this.logFile, data);
  }
}

module.exports = { Engine };
