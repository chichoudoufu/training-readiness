exports.handler = async (event) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json'
  };
  if (event.httpMethod === 'OPTIONS') return { statusCode: 200, headers, body: '' };
  try {
    const { code, grant_type, refresh_token } = JSON.parse(event.body || '{}');
    const body = {
      client_id: '244519',
      client_secret: process.env.STRAVA_CLIENT_SECRET,
      grant_type: grant_type || 'authorization_code',
    };
    if (grant_type === 'refresh_token') body.refresh_token = refresh_token;
    else body.code = code;
    const res = await fetch('https://www.strava.com/oauth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    return { statusCode: res.status, headers, body: JSON.stringify(data) };
  } catch (e) {
    return { statusCode: 500, headers, body: JSON.stringify({ error: e.message }) };
  }
};
