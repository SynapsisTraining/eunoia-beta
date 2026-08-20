import json
import random
from pathlib import Path
import streamlit as st
import requests
import csv
import io
import math
import statistics
import time

st.set_page_config(page_title="Eunoia | Entrenamiento conversacional", page_icon="🌿", layout="centered")

# -----------------------------
# Configuración
# -----------------------------
API_KEY = st.secrets.get("GEMINI_API_KEY", "")
MODEL = st.secrets.get("GEMINI_MODEL", "gemini-3.7-flash")
FALLBACK_MODEL = st.secrets.get("GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

st.markdown("""
<style>
.stApp { background: #F7F8FA; }
.block-container { max-width: 860px; padding-top: 2rem; padding-bottom: 4rem; }
h1, h2, h3 { letter-spacing: -0.02em; }
.metric-card {
    background: white; border: 1px solid #E7E9EE; border-radius: 14px;
    padding: 16px; margin-bottom: 10px;
}
.small-muted { color: #6B7280; font-size: 0.92rem; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Corpus beta: 30 situaciones x 3 formulaciones
# -----------------------------
CASES = [
    {"id":"S01","ambito":"Pareja","P":"Nunca cuentas conmigo. Haces siempre lo que te da la gana.","N":"Has tomado esta decisión sin consultarme.","F":"Me gustaría que las decisiones que nos afectan las habláramos antes."},
    {"id":"S02","ambito":"Pareja","P":"Eres igual que tu padre. Nunca reconoces cuando te equivocas.","N":"No has reconocido tu error en esta situación.","F":"Me ayudaría que pudiéramos reconocer juntos qué parte nos corresponde a cada uno."},
    {"id":"S03","ambito":"Familia","P":"Contigo no se puede hablar de nada.","N":"Esta conversación se está haciendo difícil.","F":"Quiero hablar de esto, pero necesito que encontremos una forma en la que ambos podamos escucharnos."},
    {"id":"S04","ambito":"Familia","P":"Siempre tienes una excusa para todo.","N":"Has dado varias explicaciones distintas.","F":"Quiero entender qué ha ocurrido antes de sacar conclusiones."},
    {"id":"S05","ambito":"Padres-hijos","P":"Eres un irresponsable, nunca haces nada a tiempo.","N":"No has entregado la tarea en la fecha acordada.","F":"La tarea no está entregada; veamos qué necesitas para cumplir el próximo plazo."},
    {"id":"S06","ambito":"Padres-hijos","P":"Como sigas así no vas a llegar a nada.","N":"Tus resultados han empeorado este trimestre.","F":"Tus resultados han bajado; quiero que veamos juntos qué está pasando y cómo ayudarte."},
    {"id":"S07","ambito":"Amistad","P":"Solo me llamas cuando necesitas algo.","N":"Últimamente me has llamado principalmente para pedirme ayuda.","F":"Echo de menos que nuestra relación tenga también momentos que no giren alrededor de problemas."},
    {"id":"S08","ambito":"Amistad","P":"Haz lo que quieras, como siempre.","N":"Puedes decidirlo tú.","F":"No estoy de acuerdo, pero respeto que la decisión final sea tuya."},
    {"id":"S09","ambito":"Trabajo","P":"Este informe es un desastre.","N":"El informe contiene varios errores.","F":"He detectado varios errores en el informe; revisémoslos para dejarlo sólido."},
    {"id":"S10","ambito":"Trabajo","P":"No tienes ni idea de cómo llevar este proyecto.","N":"No comparto cómo estás gestionando el proyecto.","F":"Hay decisiones de gestión que me preocupan; me gustaría revisar contigo sus efectos."},
    {"id":"S11","ambito":"Dirección","P":"Si tengo que explicártelo otra vez, lo hago yo.","N":"Ya hemos revisado este procedimiento anteriormente.","F":"Quiero comprobar qué parte del procedimiento no ha quedado clara para poder resolverla."},
    {"id":"S12","ambito":"Dirección","P":"Aquí se hace lo que digo yo.","N":"La decisión final me corresponde a mí.","F":"Escucharé las propuestas y después asumiré la responsabilidad de decidir."},
    {"id":"S13","ambito":"Educación","P":"Este alumno no tiene ningún interés.","N":"El alumno participa poco en clase.","F":"Está participando poco; conviene averiguar qué está dificultando su implicación."},
    {"id":"S14","ambito":"Educación","P":"Si no estudias, suspenderás porque te lo mereces.","N":"Si no estudias, es probable que suspendas.","F":"Si mantienes este nivel de estudio, probablemente no alcanzarás los objetivos; podemos organizar un plan."},
    {"id":"S15","ambito":"Deporte","P":"Has perdido el partido tú solo.","N":"Tu error influyó en el resultado.","F":"Ese error tuvo peso en la jugada; vamos a analizarlo para aprender de él."},
    {"id":"S16","ambito":"Deporte","P":"No tienes carácter para competir.","N":"Hoy te has mostrado inseguro en momentos decisivos.","F":"Hoy te costó decidir bajo presión; podemos entrenar específicamente esas situaciones."},
    {"id":"S17","ambito":"Atención al público","P":"Ya se lo he explicado tres veces, ¿qué parte no entiende?","N":"Ya le he explicado este procedimiento varias veces.","F":"Parece que mi explicación anterior no ha sido suficiente; voy a plantearlo de otra manera."},
    {"id":"S18","ambito":"Atención al público","P":"Ese no es mi problema.","N":"Ese asunto no corresponde a mi departamento.","F":"No puedo resolverlo desde aquí, pero puedo indicarle dónde pueden ayudarle."},
    {"id":"S19","ambito":"Convivencia","P":"Eres un cerdo, nunca recoges nada.","N":"Has dejado tus cosas sin recoger.","F":"Necesito que recojas lo que has dejado para que podamos compartir el espacio cómodamente."},
    {"id":"S20","ambito":"Convivencia","P":"No pienso aguantar tus manías.","N":"No quiero mantener esta dinámica.","F":"Esta dinámica me está resultando difícil y necesito que acordemos otra forma de organizarnos."},
    {"id":"S21","ambito":"Desconocidos","P":"¿Eres tonto o qué?","N":"No entiendo por qué has hecho eso.","F":"Lo que acabas de hacer me ha molestado; necesito que mantengamos distancia."},
    {"id":"S22","ambito":"Desconocidos","P":"Aprende a conducir, inútil.","N":"Has hecho una maniobra peligrosa.","F":"Esa maniobra ha sido peligrosa; por favor, mantén más distancia."},
    {"id":"S23","ambito":"Redes sociales","P":"Solo un ignorante puede pensar eso.","N":"No comparto esa opinión.","F":"No coincido con esa conclusión; veo el asunto de otra manera por estas razones."},
    {"id":"S24","ambito":"Redes sociales","P":"Das pena intentando justificarte.","N":"Tu explicación no me convence.","F":"Tu explicación no resuelve mis dudas; ¿puedes aclarar este punto?"},
    {"id":"S25","ambito":"Institucional","P":"Los usuarios se quejan por todo.","N":"Hemos recibido varias quejas de usuarios.","F":"Las quejas recibidas pueden ayudarnos a identificar qué parte del servicio necesita revisión."},
    {"id":"S26","ambito":"Institucional","P":"No podemos perder el tiempo con estas tonterías.","N":"No podemos priorizar este asunto ahora.","F":"Ahora mismo tenemos otras prioridades; revisaremos este asunto cuando dispongamos de capacidad."},
    {"id":"S27","ambito":"Salud/acompañamiento","P":"Tienes que dejar de pensar así.","N":"Ese pensamiento te está generando malestar.","F":"Podemos explorar qué efecto tiene ese pensamiento y si existe otra forma de mirarlo."},
    {"id":"S28","ambito":"Salud/acompañamiento","P":"Te estás ahogando en un vaso de agua.","N":"La situación parece menor desde fuera.","F":"Aunque desde fuera pueda parecer pequeña, veo que para ti está teniendo mucho peso."},
    {"id":"S29","ambito":"Negociación","P":"O aceptas esto o no hay nada que hablar.","N":"Esta es mi propuesta final.","F":"Este es el límite hasta el que puedo llegar; si no encaja, tendremos que buscar otra opción."},
    {"id":"S30","ambito":"Negociación","P":"Estás intentando aprovecharte de mí.","N":"Considero que la propuesta me perjudica.","F":"La propuesta me resulta desequilibrada; necesito revisar estas condiciones antes de avanzar."},
]

# -----------------------------
# Patrón de calibración
# -----------------------------
CALIBRATION_PATH = Path(__file__).with_name("calibracion_90.json")
with open(CALIBRATION_PATH, "r", encoding="utf-8") as _f:
    CALIBRATION = json.load(_f)
CALIBRATION_BY_ID = {x["id"]: x for x in CALIBRATION}

def calibration_key(case_id, tipo):
    return f"{case_id}-" + {"Perjudicial":"P", "Neutro":"N", "Favorable":"F"}[tipo]

def compare_reference(result, reference):
    d_iec = round(result["indices"]["IEC"] - reference["IEC"], 1)
    d_ibc = round(result["indices"]["IBC"] - reference["IBC"], 1)
    tol = reference.get("tolerancia", 1.5)
    return {
        "delta_IEC": d_iec,
        "delta_IBC": d_ibc,
        "dentro_rango": abs(d_iec) <= tol and abs(d_ibc) <= tol
    }


# -----------------------------
# LLM helpers
# -----------------------------
def _safe_api_error(response):
    """Devuelve un error legible sin exponer cabeceras, URL ni credenciales."""
    status = getattr(response, "status_code", None)
    try:
        body = response.json()
        message = body.get("error", {}).get("message", "")
    except Exception:
        message = ""
    if status == 429:
        return "Gemini ha alcanzado temporalmente un límite de solicitudes. Inténtalo de nuevo en unos segundos."
    if status in (500, 502, 503, 504):
        return "El servicio de Gemini está temporalmente ocupado o no disponible."
    if status in (401, 403):
        return "Gemini ha rechazado la autenticación. Revisa la clave API y sus permisos."
    if status == 404:
        return "El modelo solicitado no está disponible para esta cuenta o endpoint."
    return f"Gemini devolvió un error HTTP {status}." + (f" {message}" if message else "")


def _request_model(model_name, payload, retries=3):
    url = f"{API_BASE}/{model_name}:generateContent"
    headers = {
        "x-goog-api-key": API_KEY,
        "Content-Type": "application/json",
    }
    retryable = {429, 500, 502, 503, 504}
    last_response = None

    for attempt in range(retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=75)
            last_response = response
        except requests.RequestException:
            if attempt < retries - 1:
                time.sleep(1.5 * (2 ** attempt))
                continue
            raise RuntimeError("No se pudo conectar con Gemini. Comprueba la conexión e inténtalo de nuevo.")

        if response.ok:
            data = response.json()
            try:
                output = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(output)
            except (KeyError, IndexError, TypeError, json.JSONDecodeError):
                raise RuntimeError("Gemini respondió, pero el formato recibido no era válido para Eunoia.")

        if response.status_code in retryable and attempt < retries - 1:
            time.sleep(1.5 * (2 ** attempt))
            continue

        break

    raise RuntimeError(_safe_api_error(last_response))


def call_gemini(system_prompt, user_prompt, temperature=None):
    if not API_KEY:
        raise RuntimeError("Falta GEMINI_API_KEY en los Secrets de Streamlit.")

    generation_config = {"responseMimeType": "application/json"}
    if temperature is not None:
        generation_config["temperature"] = temperature

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": generation_config,
    }

    try:
        return _request_model(MODEL, payload, retries=3)
    except RuntimeError as primary_error:
        # Solo recurrimos al modelo alternativo ante indisponibilidad temporal
        # o modelo no accesible; no ocultamos problemas de autenticación.
        msg = str(primary_error)
        fallback_allowed = (
            "temporalmente" in msg
            or "no está disponible" in msg
            or "No se pudo conectar" in msg
            or "límite de solicitudes" in msg
        )
        if FALLBACK_MODEL and FALLBACK_MODEL != MODEL and fallback_allowed:
            try:
                return _request_model(FALLBACK_MODEL, payload, retries=2)
            except RuntimeError:
                pass
        raise primary_error


ANALYSIS_SYSTEM = """
Eres el motor de análisis de Eunoia.
Analiza exclusivamente el texto recibido. No respondas al interlocutor y no diagnostiques a la persona.
Diferencia siempre intención y efecto. Que un mensaje pueda herir no implica intención deliberada de herir.
Las intenciones son inferencias: si la evidencia es insuficiente, baja la puntuación y la confianza.
Puntúa de 0 a 10. Devuelve SOLO JSON válido.

Esquema obligatorio:
{
  "metricas": {
    "complejidad_sintactica": {"valor": 0, "explicacion": ""},
    "complejidad_interpretativa": {"valor": 0, "explicacion": ""},
    "generalizacion": {"valor": 0, "explicacion": ""},
    "carga_evaluativa": {"valor": 0, "explicacion": ""},
    "personalizacion": {"valor": 0, "explicacion": ""},
    "intensidad_verbal": {"valor": 0, "explicacion": ""},
    "claridad": {"valor": 0, "explicacion": ""},
    "ausencia_descalificacion": {"valor": 0, "explicacion": ""},
    "apertura_dialogo": {"valor": 0, "explicacion": ""}
  },
  "verbos": [{"verbo":"", "accion_comunicativa":""}],
  "adjetivos": [{"adjetivo":"", "tipo":"descriptivo|evaluativo|afectivo|descalificador|intensificador"}],
  "marcadores": [{"elemento":"", "tipo":"generalizacion|negacion|intensificador|absolutizador|imperativo|atribucion|otro", "impacto":""}],
  "intenciones": [{"tipo":"", "valor":0, "confianza":"baja|media|alta", "justificacion":""}],
  "consecuencias": [{"tipo":"", "valor":0, "justificacion":""}],
  "sintesis": {"descripcion":"", "principal_factor_escalada":"", "principal_factor_apertura":"", "observacion":""}
}

Incluye en consecuencias, si son pertinentes: dolor, entendimiento, confusion, comprension, enfrentamiento, defensividad, acercamiento, distanciamiento, catarsis, reparacion.
"""

SOCRATIC_SYSTEM = """
Eres el tutor socrático de Eunoia.
Tu tarea es ayudar al usuario a examinar su propia respuesta sin darle la solución.
Reglas:
- Formula UNA sola pregunta cada vez.
- La pregunta debe depender del mensaje, de la respuesta del usuario y del análisis disponible.
- No hagas preguntas dirigidas que contengan la respuesta correcta.
- No moralices, no humilles y no diagnostiques.
- Trabaja con evidencias del texto, diferencias entre observación e interpretación, efectos probables, alternativas y coherencia entre intención y resultado.
- No busques bajar el conflicto a cero: una respuesta firme puede ser adecuada.
- El objetivo es reducir daño innecesario preservando verdad, claridad y límites.
- Devuelve SOLO JSON válido con: {"pregunta":"...", "foco":"..."}
"""

def analyze_message(text):
    raw = call_gemini(ANALYSIS_SYSTEM, f"Analiza este mensaje:\n{text}")
    m = raw["metricas"]
    # consecuencias helper
    cons = {c["tipo"].lower(): c["valor"] for c in raw.get("consecuencias", [])}
    defensividad = cons.get("defensividad", 0)
    enfrentamiento = cons.get("enfrentamiento", 0)
    comprension = cons.get("comprension", 0)
    entendimiento = cons.get("entendimiento", 0)
    reparacion = cons.get("reparacion", 0)
    iec = (
        m["generalizacion"]["valor"] * 0.15 +
        m["carga_evaluativa"]["valor"] * 0.20 +
        m["personalizacion"]["valor"] * 0.15 +
        m["intensidad_verbal"]["valor"] * 0.20 +
        defensividad * 0.15 +
        enfrentamiento * 0.15
    )
    ibc = (
        m["claridad"]["valor"] * 0.20 +
        comprension * 0.20 +
        entendimiento * 0.15 +
        reparacion * 0.15 +
        m["ausencia_descalificacion"]["valor"] * 0.15 +
        m["apertura_dialogo"]["valor"] * 0.15
    )
    raw["indices"] = {
        "IEC": round(iec, 1),
        "IBC": round(ibc, 1)
    }
    return raw

def socratic_question(case_text, user_answer, analysis, history):
    context = {
        "mensaje_inicial": case_text,
        "respuesta_usuario": user_answer,
        "analisis_respuesta": analysis,
        "historial_dialogo": history,
    }
    return call_gemini(SOCRATIC_SYSTEM, json.dumps(context, ensure_ascii=False))

# -----------------------------
# Laboratorio de calibración v0.3
# -----------------------------
def flatten_corpus():
    rows = []
    for c in CASES:
        for tipo, code in [("Perjudicial", "P"), ("Neutro", "N"), ("Favorable", "F")]:
            ref = CALIBRATION_BY_ID[f"{c['id']}-{code}"]["referencia"]
            rows.append({
                "key": f"{c['id']}-{code}", "situacion": c["id"], "ambito": c["ambito"],
                "tipo": tipo, "texto": c[code], "ref_IEC": ref["IEC"], "ref_IBC": ref["IBC"],
                "tolerancia": ref.get("tolerancia", 1.5)
            })
    return rows

CORPUS_ROWS = flatten_corpus()

def icc_absolute_single(matrix):
    """ICC(A,1): two-way mixed, single-measure, absolute agreement.
    matrix: n targets x k repeated ratings. Returns None when variance is insufficient.
    """
    n = len(matrix)
    if n < 2:
        return None
    k = len(matrix[0]) if matrix else 0
    if k < 2 or any(len(r) != k for r in matrix):
        return None
    grand = sum(sum(r) for r in matrix) / (n * k)
    row_means = [sum(r) / k for r in matrix]
    col_means = [sum(matrix[i][j] for i in range(n)) / n for j in range(k)]
    ss_rows = k * sum((m - grand) ** 2 for m in row_means)
    ss_cols = n * sum((m - grand) ** 2 for m in col_means)
    ss_total = sum((x - grand) ** 2 for r in matrix for x in r)
    ss_err = ss_total - ss_rows - ss_cols
    ms_rows = ss_rows / (n - 1)
    ms_cols = ss_cols / (k - 1)
    ms_err = ss_err / ((n - 1) * (k - 1))
    denom = ms_rows + (k - 1) * ms_err + (k * (ms_cols - ms_err) / n)
    return None if abs(denom) < 1e-12 else (ms_rows - ms_err) / denom

def summarize_lab(results):
    if not results:
        return {}
    iec_errors, ibc_errors, iec_matrix, ibc_matrix = [], [], [], []
    unstable = 0
    outliers = 0
    for r in results:
        iecs = r["IEC_runs"]
        ibcs = r["IBC_runs"]
        mean_iec = statistics.mean(iecs)
        mean_ibc = statistics.mean(ibcs)
        iec_errors.append(abs(mean_iec - r["ref_IEC"]))
        ibc_errors.append(abs(mean_ibc - r["ref_IBC"]))
        iec_matrix.append(iecs)
        ibc_matrix.append(ibcs)
        sd_iec = statistics.stdev(iecs) if len(iecs) > 1 else 0
        sd_ibc = statistics.stdev(ibcs) if len(ibcs) > 1 else 0
        if max(sd_iec, sd_ibc) >= 1.0:
            unstable += 1
        if abs(mean_iec-r["ref_IEC"]) > r["tolerancia"] or abs(mean_ibc-r["ref_IBC"]) > r["tolerancia"]:
            outliers += 1
    return {
        "MAE_IEC": round(statistics.mean(iec_errors), 3),
        "MAE_IBC": round(statistics.mean(ibc_errors), 3),
        "ICC_IEC": icc_absolute_single(iec_matrix),
        "ICC_IBC": icc_absolute_single(ibc_matrix),
        "inestables": unstable,
        "fuera_tolerancia": outliers,
        "n": len(results),
    }

def lab_rows_for_display(results):
    rows=[]
    for r in results:
        mi=statistics.mean(r["IEC_runs"]); mb=statistics.mean(r["IBC_runs"])
        si=statistics.stdev(r["IEC_runs"]) if len(r["IEC_runs"])>1 else 0
        sb=statistics.stdev(r["IBC_runs"]) if len(r["IBC_runs"])>1 else 0
        rows.append({
            "ID":r["key"], "Ámbito":r["ambito"], "Tipo":r["tipo"],
            "IEC ref":r["ref_IEC"], "IEC media":round(mi,2), "ΔIEC":round(mi-r["ref_IEC"],2), "SD IEC":round(si,2),
            "IBC ref":r["ref_IBC"], "IBC media":round(mb,2), "ΔIBC":round(mb-r["ref_IBC"],2), "SD IBC":round(sb,2),
            "Revisar":"Sí" if (max(si,sb)>=1.0 or abs(mi-r["ref_IEC"])>r["tolerancia"] or abs(mb-r["ref_IBC"])>r["tolerancia"]) else "No"
        })
    return rows

def rows_to_csv(rows):
    if not rows: return ""
    buf=io.StringIO(); w=csv.DictWriter(buf, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    return buf.getvalue()

# -----------------------------
# Session state
# -----------------------------
for k, v in {
    "case": None,
    "first_answer": "",
    "first_analysis": None,
    "dialogue": [],
    "current_question": None,
    "second_answer": "",
    "second_analysis": None,
    "case_calibration": None,
    "lab_results": [],
    "lab_progress": 0,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -----------------------------
# UI
# -----------------------------
st.title("Eunoia")
st.caption("Entrena conversaciones que importan. · Beta de entrenamiento conversacional con análisis cuantificado y diálogo socrático.")

with st.expander("Cómo funciona esta beta", expanded=False):
    st.write("1. Elige una situación. 2. Responde espontáneamente. 3. Analizamos tu respuesta. 4. La IA inicia un diálogo socrático. 5. Reformulas y comparamos ambos intentos.")

col1, col2 = st.columns([2,1])
with col1:
    ambitos = sorted(set(c["ambito"] for c in CASES))
    ambito = st.selectbox("Ámbito", ["Todos"] + ambitos)
with col2:
    dificultad = st.selectbox("Tipo de mensaje", ["Perjudicial", "Neutro", "Favorable"])

key_map = {"Perjudicial":"P", "Neutro":"N", "Favorable":"F"}
filtered = [c for c in CASES if ambito == "Todos" or c["ambito"] == ambito]

if st.button("Generar situación", type="primary"):
    c = random.choice(filtered)
    st.session_state.case = {"id": c["id"], "ambito": c["ambito"], "texto": c[key_map[dificultad]], "tipo": dificultad}
    st.session_state.first_answer = ""
    st.session_state.first_analysis = None
    st.session_state.dialogue = []
    st.session_state.current_question = None
    st.session_state.second_answer = ""
    st.session_state.second_analysis = None
    st.session_state.case_calibration = None

if st.session_state.case:
    case = st.session_state.case
    st.subheader("Situación")
    st.info(f"{case['texto']}\n\nÁmbito: {case['ambito']}")

    with st.expander("Calibración experimental", expanded=False):
        ref_key = calibration_key(case["id"], case["tipo"])
        ref = CALIBRATION_BY_ID[ref_key]["referencia"]
        st.caption("Referencia humana provisional. No interviene en la puntuación de tu respuesta.")
        r1, r2 = st.columns(2)
        r1.metric("IEC referencia", f"{ref['IEC']}/10")
        r2.metric("IBC referencia", f"{ref['IBC']}/10")

        if st.button("Comprobar IA contra referencia", key="calibrate_case"):
            try:
                model_case = analyze_message(case["texto"])
                cmp = compare_reference(model_case, ref)
                st.session_state.case_calibration = {
                    "analysis": model_case, "comparison": cmp, "reference": ref
                }
            except Exception as e:
                st.error(f"No se pudo ejecutar la calibración: {e}")

        if st.session_state.case_calibration:
            cc = st.session_state.case_calibration
            cmp = cc["comparison"]
            st.write(
                f"IA: IEC {cc['analysis']['indices']['IEC']}/10 · "
                f"IBC {cc['analysis']['indices']['IBC']}/10"
            )
            if cmp["dentro_rango"]:
                st.success(f"Dentro de tolerancia (±{cc['reference']['tolerancia']}).")
            else:
                st.warning(
                    f"Revisión necesaria · ΔIEC {cmp['delta_IEC']:+.1f} · "
                    f"ΔIBC {cmp['delta_IBC']:+.1f}"
                )

    st.session_state.first_answer = st.text_area("¿Qué responderías?", value=st.session_state.first_answer, height=130, key="first_answer_widget")

    if st.button("Analizar mi respuesta") and st.session_state.first_answer.strip():
        try:
            st.session_state.first_analysis = analyze_message(st.session_state.first_answer.strip())
            st.session_state.current_question = socratic_question(case["texto"], st.session_state.first_answer.strip(), st.session_state.first_analysis, [])
        except Exception as e:
            st.error(f"No se pudo completar el análisis: {e}")

if st.session_state.first_analysis:
    a = st.session_state.first_analysis
    st.subheader("Primer análisis")
    c1, c2 = st.columns(2)
    c1.metric("IEC · Escalada", f"{a['indices']['IEC']}/10")
    c2.metric("IBC · Benevolencia", f"{a['indices']['IBC']}/10")

    metrics = a.get("metricas", {})
    labels = [
        ("Generalización", "generalizacion"),
        ("Carga evaluativa", "carga_evaluativa"),
        ("Personalización", "personalizacion"),
        ("Intensidad verbal", "intensidad_verbal"),
        ("Claridad", "claridad"),
        ("Apertura al diálogo", "apertura_dialogo"),
    ]
    for label, key in labels:
        if key in metrics:
            st.progress(metrics[key]["valor"] / 10, text=f"{label}: {metrics[key]['valor']}/10")

    st.write(a.get("sintesis", {}).get("descripcion", ""))
    with st.expander("Ver análisis lingüístico"):
        st.json({"verbos": a.get("verbos", []), "adjetivos": a.get("adjetivos", []), "marcadores": a.get("marcadores", []), "intenciones": a.get("intenciones", []), "consecuencias": a.get("consecuencias", [])})

if st.session_state.current_question:
    st.subheader("Diálogo socrático")
    st.write(st.session_state.current_question["pregunta"])
    soc_answer = st.text_area("Tu reflexión", height=110, key=f"soc_{len(st.session_state.dialogue)}")
    c1, c2 = st.columns(2)
    if c1.button("Siguiente pregunta") and soc_answer.strip():
        st.session_state.dialogue.append({"pregunta": st.session_state.current_question["pregunta"], "respuesta": soc_answer.strip()})
        if len(st.session_state.dialogue) >= 5:
            st.session_state.current_question = None
        else:
            try:
                st.session_state.current_question = socratic_question(st.session_state.case["texto"], st.session_state.first_answer, st.session_state.first_analysis, st.session_state.dialogue)
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo generar la siguiente pregunta: {e}")
    if c2.button("Pasar a reformular"):
        st.session_state.current_question = None
        st.rerun()

if st.session_state.first_analysis and st.session_state.current_question is None:
    st.subheader("Segundo intento")
    st.caption("Responde de nuevo al mensaje inicial teniendo en cuenta lo que has descubierto. No busques una frase perfecta.")
    st.session_state.second_answer = st.text_area("Nueva respuesta", value=st.session_state.second_answer, height=130, key="second_answer_widget")
    if st.button("Comparar intentos") and st.session_state.second_answer.strip():
        try:
            st.session_state.second_analysis = analyze_message(st.session_state.second_answer.strip())
        except Exception as e:
            st.error(f"No se pudo analizar el segundo intento: {e}")

if st.session_state.second_analysis:
    a1 = st.session_state.first_analysis
    a2 = st.session_state.second_analysis
    st.subheader("Comparación")
    c1, c2 = st.columns(2)
    c1.metric("IEC", f"{a2['indices']['IEC']}/10", delta=round(a2['indices']['IEC']-a1['indices']['IEC'],1), delta_color="inverse")
    c2.metric("IBC", f"{a2['indices']['IBC']}/10", delta=round(a2['indices']['IBC']-a1['indices']['IBC'],1))
    st.write(a2.get("sintesis", {}).get("descripcion", ""))
    reflection = st.text_area("¿Qué has cambiado deliberadamente entre ambas respuestas?", height=100)
    if reflection:
        st.success("Ejercicio completado. El objetivo no es alcanzar una puntuación perfecta, sino comprender qué decisiones lingüísticas cambian la trayectoria de la conversación.")

st.divider()
st.header("Laboratorio de calibración · v0.3")
st.caption("Ejecuta cada mensaje tres veces para separar desacuerdo IA–referencia de inestabilidad IA–IA. Las llamadas consumen cuota de la API.")

with st.expander("Configurar ejecución", expanded=False):
    scope = st.selectbox("Conjunto", ["Prueba rápida · 6 mensajes", "Un ámbito", "Corpus completo · 90 mensajes"])
    lab_ambito = None
    if scope == "Un ámbito":
        lab_ambito = st.selectbox("Ámbito para calibrar", sorted(set(r["ambito"] for r in CORPUS_ROWS)), key="lab_ambito")
    st.caption("Cada mensaje se evalúa 3 veces de forma independiente. Corpus completo = 270 llamadas al modelo.")
    if st.button("Ejecutar calibración triple", type="primary", key="run_lab"):
        if scope.startswith("Prueba rápida"):
            selected = CORPUS_ROWS[:6]
        elif scope == "Un ámbito":
            selected = [r for r in CORPUS_ROWS if r["ambito"] == lab_ambito]
        else:
            selected = CORPUS_ROWS
        st.session_state.lab_results = []
        progress = st.progress(0, text="Iniciando calibración…")
        total = len(selected) * 3
        done = 0
        try:
            for item in selected:
                iecs, ibcs = [], []
                for run in range(3):
                    a = analyze_message(item["texto"])
                    iecs.append(float(a["indices"]["IEC"]))
                    ibcs.append(float(a["indices"]["IBC"]))
                    done += 1
                    progress.progress(done/total, text=f"{done}/{total} evaluaciones · {item['key']}")
                st.session_state.lab_results.append({**item, "IEC_runs": iecs, "IBC_runs": ibcs})
            progress.progress(1.0, text="Calibración completada")
        except Exception as e:
            st.error(f"La ejecución se detuvo en {done}/{total}: {e}")

if st.session_state.lab_results:
    summary = summarize_lab(st.session_state.lab_results)
    st.subheader("Resumen")
    a,b,c,d = st.columns(4)
    a.metric("MAE IEC", summary["MAE_IEC"])
    b.metric("MAE IBC", summary["MAE_IBC"])
    c.metric("ICC IEC", "—" if summary["ICC_IEC"] is None else f"{summary['ICC_IEC']:.3f}")
    d.metric("ICC IBC", "—" if summary["ICC_IBC"] is None else f"{summary['ICC_IBC']:.3f}")
    st.write(f"Casos evaluados: **{summary['n']}** · Inestables (SD ≥ 1): **{summary['inestables']}** · Fuera de tolerancia: **{summary['fuera_tolerancia']}**")
    st.caption("ICC mostrado: acuerdo absoluto, dos vías, medida individual. Interprétalo junto con MAE y dispersión; no como criterio único.")
    display_rows = lab_rows_for_display(st.session_state.lab_results)
    st.dataframe(display_rows, use_container_width=True, hide_index=True)
    st.download_button("Descargar resultados CSV", rows_to_csv(display_rows).encode("utf-8-sig"), file_name="eunoia_calibracion_v03.csv", mime="text/csv")
    raw_json = json.dumps(st.session_state.lab_results, ensure_ascii=False, indent=2)
    st.download_button("Descargar datos brutos JSON", raw_json.encode("utf-8"), file_name="eunoia_calibracion_v03_raw.json", mime="application/json")

st.divider()
st.caption("Beta experimental. IEC e IBC son indicadores pedagógicos, no diagnósticos psicológicos ni medidas clínicas.")
