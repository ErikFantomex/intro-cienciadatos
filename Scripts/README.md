# API NestJS de CryptoInsight

Esta aplicación conserva los módulos de usuarios, autenticación y productos
Teslo, y agrega el gateway REST de CryptoInsight. La configuración canónica
de los cinco servicios está en [`../compose.yaml`](../compose.yaml); ejecuta
los comandos de inicio desde la raíz y consulta allí las instrucciones,
variables, redes y persistencia.

Swagger NestJS está disponible en `http://localhost:3000/api`. La API financiera
se enruta bajo `/api/crypto/*` y llama a FastAPI mediante `CRYPTO_API_URL`.

La ruta seed destructiva ya no usa `GET`: es `POST /api/seed`, requiere un JWT
de administrador, solo se habilita fuera de producción con
`ENABLE_SEED_ENDPOINT=true` y está desactivada por defecto. No la habilites
contra una base con datos que quieras conservar.
