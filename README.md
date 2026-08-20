# Eunoia Beta v0.3

**Entrena conversaciones que importan.**

Esta versión añade un Laboratorio de Calibración al entrenamiento conversacional.

## Novedades v0.3
- Triple evaluación independiente por mensaje.
- Prueba rápida de 6 mensajes, ejecución por ámbito o corpus completo de 90.
- MAE para IEC e IBC frente a la referencia humana provisional.
- ICC de acuerdo absoluto para estudiar estabilidad entre las tres ejecuciones.
- Desviación estándar intra-mensaje para detectar inestabilidad IA–IA.
- Señalización automática de casos fuera de tolerancia o inestables.
- Exportación CSV de resultados resumidos y JSON de datos brutos.

## Precaución metodológica
Las referencias IEC/IBC siguen siendo provisionales. Una discrepancia no demuestra por sí sola que la IA esté equivocada: puede indicar un problema del modelo, del prompt, de la referencia humana o de la definición del indicador.

## Coste de API
El corpus completo ejecuta 90 mensajes × 3 repeticiones = 270 llamadas. Empieza por la prueba rápida o por un ámbito.

## Ejecución
1. `pip install -r requirements.txt`
2. Configura `GEMINI_API_KEY` en `.streamlit/secrets.toml`.
3. `streamlit run app.py`
