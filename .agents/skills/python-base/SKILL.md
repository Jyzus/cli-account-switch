---
name: python-base
description: Convención de la casa para cualquier repositorio Python — entorno, estructura, tests y lo que no se decide sobre la marcha. Se compone con la skill del framework (fastapi, cli…), que la da por supuesta.
version: 1
requiere: []
---

Cómo se construye un repositorio Python **aquí**. No es Python: es la forma de la casa, la que
hace que dos repos distintos se lean igual.

Esta convención es el **valor por defecto**. Si un `ADR` del pack dice otra cosa, **gana el ADR** —
y si eso pasa, dilo: significa que la convención se quedó vieja o que este proyecto es una
excepción que nadie escribió.

## Entorno

- **Siempre `venv`, siempre local al repositorio**, en `.venv/`. Nunca se instala nada en el Python
  del sistema ni se activa un entorno de otro repo.
- Las dependencias se declaran en `pyproject.toml`. Nada de `requirements.txt` suelto, y nada de
  instalar algo sin declararlo: lo que no está en `pyproject.toml` no existe en la siguiente
  máquina.
- **Añadir una dependencia es una decisión de arquitectura, no un paso de la implementación.** Si
  la librería no aparece en el pack, párate y repórtalo.

## Estructura

```
paquete/          el código; el nombre del paquete, en snake_case
  __init__.py
tests/            un archivo por módulo, mismo nombre con prefijo test_
pyproject.toml
```

**El nombre del repositorio y el del paquete no tienen por qué coincidir**, y en cuanto el
repositorio lleva prefijos de organización es mejor que no coincidan. El del repositorio es
metadato de propiedad y despliegue —empresa, tipo de proyecto, parte—; el del paquete es una
**ruta de import**, y hacerlos iguales mete la empresa en cada línea del código:

```python
from kaymer_triireview_wk.anclaje import por_etiqueta     # el repo, colado en cada import
from trii_review.anclaje import por_etiqueta              # lo que quieres leer
```

Cuando difieran, dilo en `pyproject.toml` —`[tool.setuptools] packages = ["…"]`— en vez de dejarlo
a la autodetección: acierta mientras haya un solo directorio y deja de acertar sin avisar.

- **Un módulo, una responsabilidad, y el nombre lo dice.** Si necesitas un `utils.py` es que falta
  un nombre, no un cajón.
- Los tests viven en `tests/` y **no** dentro del paquete.
- No crees paquetes ni carpetas nuevas por tu cuenta. Si el código no encaja en ninguno de los que
  hay, eso es información: dilo.

## Estilo

- Todo lo público lleva **anotaciones de tipo**. Lo privado, si aclara.
- Docstrings donde explican **por qué**, no qué. Un docstring que parafrasea la firma sobra.
- Excepciones concretas. `except Exception: pass` esconde justo lo que el test intentaba
  comprobar, y lo mismo hace `# type: ignore`.
- El formateador y el linter del repositorio mandan. **Si se quejan, el que cede es tu código** —
  no la configuración.

## Tests

- `pytest`, con `assert` a secas. Nada de `unittest.TestCase`.
- Un test nombra lo que comprueba, no la función que llama: `test_un_token_caducado_no_da_acceso`,
  no `test_validar_token_2`.
- **Se mockean las fronteras** —red, reloj, terceros—, nunca la lógica bajo prueba.
- Los datos de cada caso van explícitos en el test. Un fixture compartido entre casos rompe la
  independencia que el escenario garantiza.

## Lo que en Python parece código y en realidad es una decisión

Los sitios donde el lenguaje invita a cruzar una línea del método sin que se note:

| Parece… | Y en realidad es |
|---|---|
| `pip install` | comprometer al proyecto con una dependencia durante años |
| relajar una regla del linter | cambiar el estándar del repositorio para salvar tu parche |
| crear un paquete nuevo | redefinir la estructura que comparten todos los módulos |
| subir la versión mínima de Python | un cambio de compatibilidad con efectos fuera del repo |
| un `Protocol` nuevo para desacoplar | introducir una frontera de arquitectura |

Ninguna es tuya. Todas se reportan.

## Los comandos no están aquí

Cómo se corre la suite de **este** repositorio viene en el pack, sección «Cómo se ejecuta este
repositorio». Están ahí y no en esta skill a propósito: la convención es de la casa y los comandos
son del repositorio, y mezclarlos haría que esta skill mintiera en cuanto un repo use `nox`.
