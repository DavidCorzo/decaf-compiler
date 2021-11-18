# Primera Fase: Lexer Documentación.

En este README se encuentra en general cómo funcióna el lexer, sin embargo para detalles triviales hay documentación en cada método del algoritmo que se pueden consultar en cuyo caso se necesite.

El algoritmo consta de 4 clases:
- class NFA
- class DFA 
- class scanner
- class error_msg

A continuación explicaré cada una.

## class NFA
En esta clase se construye el NFA de los estados y sus aristas. 
Los estados son guardados en un diccionario de la siguiente forma:
```
{<nombre_de_estado>:{<arista_1>:<siguiente_estado1>, ... ,<arista_n>:<sigiente_estado_n>}, <nombre_de_siguiente_estado>:{<aristas>}}
```
Ejemplo:
```
{1:{'a':2}, 2:{'b':3}, 3:{}}
```
La única arista que tiene más de un siguiente estado es la de None que es la representación que usamos para denotar épsilon. Todas las demás arístas son únicas.
Se utilizó el algorimo de thompson para construir cada operación especificada del regex. Cada operación se hace push a un stack, si este stack no tiene un length de 1 al finalizar la operación la expresión regular es incorrecta (usualmente es por que falta una concatenación).

## class DFA
Toma como argumento en su contructor a la clase NFA anterior. Los estados del NFA a continuación se les calcula el closure de cada uno y se almacena en un diccionario. 
Después, empezando por el estado inicial construimos la tabla de closure recursivamente, mientras van apareciendo nuevos estados del dfa los agregamos al registro de estados del dfa de la siguiente manera:
```
{<tupla_de_estados_de_closure_nfa>:{<arista>:<tupla_siguiente_estado_de_dfa>}}
```
Ejemplo:
```
{(3,4,5,6):{'a':(3,4,5)}, (3,4,5):{'b':(8)}, (8):{}}
```
Al teriminar por conveniencia cambiamos los nombres de tuplas a un string autogenerado de letras y números.

## class scanner
Esta clase abre el archivo de tokens y las mete a un OrderedDict, en el archivo de tokens se asume que hay precedencia, la primera regex que haga match al buffer de texto ingresado es la que gana por precedencia, de esta manera logramos diferenciar entre 'if' y 'id', 'if' aparece primero en el archivo y por ello tiene mayor precedencia. Cada token y su expresión regular son convertidas a NFA y después a DFA para poder trabajar con ellas.
Scanner también abre el archivo a leer y empieza a hacer el match de acuerdo a reglas establecidas en el método de 'scan'.
De cualquier error llegar a ocurrir mandamos el número de línea y el número de columna a una instancia de clase de error_msg para que imprima dónde las coordinadas del archivo al igual que en qué caracter falló.


## class error_msg
Esta clase únicamente despliega errores al usuario si llegase a haber alguno. Después de imprimir el error en pantalla termina el programa con -1 por que hubo error.


## CLI
El command line interfase se usa de la siguiente manera:
```
python <archivo.py> --target <stage> --debug <stage --o <new_name>
```
