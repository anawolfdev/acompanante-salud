import worker from "../nube-prueba/worker.js";

function crearDb(citas, enviosIniciales) {
  let envios = enviosIniciales || 0;
  return {
    enviosCount() {
      return envios;
    },
    prepare(sql) {
      const sentencia = String(sql);
      const ejecutar = () => {
        if (sentencia.includes("INSERT INTO envios")) {
          envios += 1;
          return { meta: { last_row_id: envios } };
        }
        throw new Error("Consulta no simulada en run: " + sentencia);
      };
      const listar = () => {
        if (sentencia.includes("FROM citas_prueba")) {
          return { results: citas.slice() };
        }
        throw new Error("Consulta no simulada en all: " + sentencia);
      };
      return {
        bind() {
          return { run: async () => ejecutar(), all: async () => listar() };
        },
        run: async () => ejecutar(),
        all: async () => listar(),
      };
    },
  };
}

async function caso(nombre, fn) {
  try {
    await fn();
    console.log("OK " + nombre);
  } catch (e) {
    console.error("FALLO " + nombre);
    console.error(e && e.stack ? e.stack : String(e));
    process.exitCode = 1;
  }
}

function afirmar(condicion, mensaje) {
  if (!condicion) {
    throw new Error(mensaje);
  }
}

const citas = [
  { titulo: "Cita de prueba con la doctora Ejemplo", fecha_hora: "2026-11-20 10:00", lugar: "Hospital Inventado" },
  { titulo: "Revisión de mentira", fecha_hora: "2026-11-25 17:30", lugar: "Centro de Salud Ficticio" },
];

await caso("envio_antes_del_limite", async () => {
  const db = crearDb(citas, 0);
  const llamadas = [];
  globalThis.fetch = async (url, opciones) => {
    llamadas.push({ url, opciones });
    return { ok: true, status: 200 };
  };
  await worker.scheduled({}, {
    DB: db,
    TELEGRAM_TOKEN: "TOKEN_FALSO",
    TELEGRAM_CHAT_ID: "123",
  }, {});
  afirmar(llamadas.length === 1, "Debía mandar un mensaje a Telegram");
  afirmar(db.enviosCount() === 1, "Debía reservar un intento");
  afirmar(String(llamadas[0].url).includes("TOKEN_FALSO"), "Debía usar el token del entorno");
  const cuerpo = JSON.parse(llamadas[0].opciones.body);
  afirmar(cuerpo.chat_id === "123", "Debía mandar al chat configurado");
  afirmar(cuerpo.text.includes("Mensaje 1 de 6"), "Debía indicar el número de mensaje");
});

await caso("ningun_envio_despues_del_limite", async () => {
  const db = crearDb(citas, 6);
  let llamadas = 0;
  globalThis.fetch = async () => {
    llamadas += 1;
    return { ok: true, status: 200 };
  };
  await worker.scheduled({}, {
    DB: db,
    TELEGRAM_TOKEN: "TOKEN_FALSO",
    TELEGRAM_CHAT_ID: "123",
  }, {});
  afirmar(llamadas === 0, "No debía llamar a Telegram tras el límite");
  afirmar(db.enviosCount() === 7, "Debía registrar la fila del intento aunque no envíe");
});

await caso("telegram_falla_consumiendo_intento", async () => {
  const db = crearDb(citas, 2);
  let llamadas = 0;
  globalThis.fetch = async () => {
    llamadas += 1;
    return { ok: false, status: 500 };
  };
  let fallo = null;
  try {
    await worker.scheduled({}, {
      DB: db,
      TELEGRAM_TOKEN: "TOKEN_FALSO",
      TELEGRAM_CHAT_ID: "123",
    }, {});
  } catch (e) {
    fallo = e;
  }
  afirmar(llamadas === 1, "Debía intentar mandar a Telegram");
  afirmar(fallo !== null, "Debía fallar cuando Telegram responde con error");
  afirmar(db.enviosCount() === 3, "Debía consumir el intento aunque Telegram falle");
});

if (process.exitCode) {
  process.exit(process.exitCode);
}
