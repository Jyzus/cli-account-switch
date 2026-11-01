# Planifier v2.0.0 · Switch · Rol de sesión: coordinador

## Reanuda trabajo
1. Al cambiar de cuenta en este workspace ejecuta `planifier contexto --compacto` y `planifier relevo --formato json`.
2. El relevo enseña alertas y si Git diverge. Con alerta o checkpoint desactualizado, revisa repos, procesos y efectos externos antes de repetir operaciones.
3. Guarda microhitos tras cada avance y antes de agotar contexto: `planifier relevo sella '<hito>' --siguiente '<comando exacto>' --agente '<cuenta>'`.
4. El número cuenta checkpoints, no sesiones. Guardar confirma persistencia; no reconstruye conversación ni certifica tests/despliegues.

## Reglas esenciales
- Planifier Docs es la fuente de verdad; nunca edites allí documentos a mano. Los ADR aprobados son inmutables.
- Una issue/SPEC corresponde a un repositorio. Tests rojos antes de implementación; no hagas commit con fallos o DoD incompleta.
- Si un pack bloquea, resuelve el hueco aguas arriba; no uses `--forzar`.
- Revisa y conserva los cambios sin commitear del agente anterior. El checkpoint orienta; no demuestra vigencia.

Usa `planifier contexto` para el contrato completo y las reglas de creación/validación documental.
Usa un resumen de conversación si hay acuerdos que aún no estén guardados en el checkpoint o Docs.