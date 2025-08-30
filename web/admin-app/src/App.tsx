import { useEffect, useMemo, useState } from 'react'
import { api as apiBuilder } from './api'

const KEY = 'nfse-admin-env'

export default function App() {
  const [apiUrl, setApiUrl] = useState<string>(() => localStorage.getItem(`${KEY}:apiUrl`) || '')
  const [idToken, setIdToken] = useState<string>(() => localStorage.getItem(`${KEY}:idToken`) || '')
  const [log, setLog] = useState<string>('ready.')

  useEffect(() => {
    if (location.hash.includes('id_token=')) {
      const params = new URLSearchParams(location.hash.replace('#', '?'))
      const tok = params.get('id_token')
      if (tok) {
        setIdToken(tok)
        localStorage.setItem(`${KEY}:idToken`, tok)
        setLog(l => l + '\nCaptured id_token from URL hash.')
        history.replaceState(null, '', location.pathname)
      }
    }
  }, [])

  useEffect(() => { localStorage.setItem(`${KEY}:apiUrl`, apiUrl) }, [apiUrl])
  useEffect(() => { localStorage.setItem(`${KEY}:idToken`, idToken) }, [idToken])

  const api = useMemo(() => apiBuilder(apiUrl, idToken), [apiUrl, idToken])

  const ping = async () => {
    try {
      const { data } = await api.get('/public/ping')
      setLog(l => l + '\nPING: ' + JSON.stringify(data))
    } catch (e: any) {
      setLog(l => l + '\nPING ERROR: ' + (e?.message || e))
    }
  }
  const emit = async () => {
    try {
      const { data } = await api.post('/invoices', { companyCnpj: '00000000000000', total: 100 })
      setLog(l => l + '\nEMIT: ' + JSON.stringify(data))
    } catch (e: any) {
      setLog(l => l + '\nEMIT ERROR: ' + (e?.message || e))
    }
  }
  const consult = async () => {
    const id = prompt('invoiceId?'); if (!id) return
    try {
      const { data } = await api.get('/invoices/' + id)
      setLog(l => l + '\nGET: ' + JSON.stringify(data))
    } catch (e: any) {
      setLog(l => l + '\nGET ERROR: ' + (e?.message || e))
    }
  }
  const cancel = async () => {
    const id = prompt('invoiceId?'); if (!id) return
    try {
      const { data } = await api.post(`/invoices/${id}/cancel`)
      setLog(l => l + '\nCANCEL: ' + JSON.stringify(data))
    } catch (e: any) {
      setLog(l => l + '\nCANCEL ERROR: ' + (e?.message || e))
    }
  }

  return (
    <div style={{ maxWidth: 860, margin: '40px auto', fontFamily: 'system-ui, Segoe UI, Roboto, Arial' }}>
      <h1>NFS-e Admin (Starter, Python)</h1>
      <p>1) Informe <b>API URL</b> (output <code>ApiUrl</code> do CDK). 2) Faça login via Hosted UI para obter o <b>id_token</b> (ou cole).</p>
      <div style={{ display: 'grid', gap: 12, gridTemplateColumns: '1fr 1fr' }}>
        <label>API URL<input value={apiUrl} onChange={e => setApiUrl(e.target.value)} placeholder="https://xxxx.execute-api.REGION.amazonaws.com/dev" style={{ width: '100%' }} /></label>
        <label>id_token (JWT)<input value={idToken} onChange={e => setIdToken(e.target.value)} placeholder="Cole o id_token" style={{ width: '100%' }} /></label>
      </div>
      <div style={{ marginTop: 16, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <button onClick={ping}>PING (público)</button>
        <button onClick={emit}>EMITIR (JWT)</button>
        <button onClick={consult}>CONSULTAR (JWT)</button>
        <button onClick={cancel}>CANCELAR (JWT)</button>
        <a href="#" onClick={(e) => { e.preventDefault(); const d = prompt('Cognito domain (ex: https://your-domain.auth.REGION.amazoncognito.com)'); const c = prompt('ClientId'); const cb = prompt('Callback URL (ex: http://localhost:5173/)'); if (d && c && cb) { location.href = `${d}/login?client_id=${c}&response_type=token&scope=email+openid+profile&redirect_uri=${encodeURIComponent(cb)}`; } }}>Login via Hosted UI</a>
      </div>
      <pre style={{ marginTop: 16, background: '#f7f7f7', padding: 12, borderRadius: 8, minHeight: 120 }}>{log}</pre>
    </div>
  )
}
