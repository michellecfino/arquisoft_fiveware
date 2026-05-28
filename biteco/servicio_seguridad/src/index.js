const express = require('express');
const jwt = require('jsonwebtoken');
const jwksClient = require('jwks-rsa');

const app = express();
app.use(express.json());

const COGNITO_REGION     = process.env.COGNITO_REGION     || 'us-east-1';
const COGNITO_USER_POOL  = process.env.COGNITO_USER_POOL  || '';
const GRUPO_PERMITIDO    = process.env.GRUPO_PERMITIDO    || 'financiero';
const PORT               = process.env.PORT               || 3000;

// Cliente JWKS — descarga las llaves públicas de Cognito y las cachea
const client = jwksClient({
  jwksUri: `https://cognito-idp.${COGNITO_REGION}.amazonaws.com/${COGNITO_USER_POOL}/.well-known/jwks.json`,
  cache: true,
  cacheMaxAge: 3600000  // 1 hora
});

function getKey(header, callback) {
  client.getSigningKey(header.kid, (err, key) => {
    if (err) return callback(err);
    callback(null, key.getPublicKey());
  });
}

// ── Endpoint de validación ──────────────────────────────────────────
app.get('/validar', (req, res) => {
  const authHeader = req.headers['authorization'] || '';

  if (!authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ autorizado: false, motivo: 'Token ausente' });
  }

  const token = authHeader.split(' ')[1];

  jwt.verify(token, getKey, { algorithms: ['RS256'] }, (err, decoded) => {
    if (err) {
      return res.status(401).json({ autorizado: false, motivo: 'Token inválido: ' + err.message });
    }

    // Cognito guarda los grupos en el claim 'cognito:groups'
    const grupos = decoded['cognito:groups'] || [];

    if (!grupos.includes(GRUPO_PERMITIDO)) {
      return res.status(403).json({
        autorizado: false,
        motivo: `Grupo '${grupos}' no tiene acceso. Se requiere '${GRUPO_PERMITIDO}'`
      });
    }

    return res.status(200).json({
      autorizado: true,
      usuario: decoded.sub,
      grupos: grupos
    });
  });
});

// ── Health check ────────────────────────────────────────────────────
app.get('/health', (req, res) => {
  res.json({ status: 'ok', servicio: 'seguridad' });
});

app.listen(PORT, () => {
  console.log(`Servicio de Seguridad corriendo en puerto ${PORT}`);
});