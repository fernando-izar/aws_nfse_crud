import React, { useState } from 'react';
import { SafeAreaView, Text, TextInput, Button, ScrollView } from 'react-native';

export default function App() {
  const [apiUrl, setApiUrl] = useState('');
  const [idToken, setIdToken] = useState('');
  const [log, setLog] = useState('ready.');

  const call = async (path, method='GET', body) => {
    try {
      const res = await fetch(apiUrl + path, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...(path.startsWith('/public') ? {} : { Authorization: 'Bearer ' + idToken }),
        },
        body: body ? JSON.stringify(body) : undefined
      });
      const txt = await res.text();
      setLog(l => l + '\n' + method + ' ' + path + ': ' + txt);
    } catch (e) {
      setLog(l => l + '\nERR: ' + (e?.message || String(e)));
    }
  };

  return (
    <SafeAreaView style={{flex:1, padding:16}}>
      <ScrollView>
        <Text style={{fontSize:22, fontWeight:'600'}}>NFS-e App (Starter, Python)</Text>

        <Text>API URL</Text>
        <TextInput value={apiUrl} onChangeText={setApiUrl} placeholder="https://xxxx.execute-api.REGION.amazonaws.com/dev" style={{borderWidth:1, padding:8, borderRadius:8, marginBottom:8}} />

        <Text>id_token (JWT)</Text>
        <TextInput value={idToken} onChangeText={setIdToken} placeholder="Cole o id_token" style={{borderWidth:1, padding:8, borderRadius:8, marginBottom:8}} />

        <Button title="PING (public)" onPress={()=>call('/public/ping')} />
        <Button title="EMITIR" onPress={()=>call('/invoices','POST',{ companyCnpj:'00000000000000', total:100 })} />
        <Button title="CONSULTAR" onPress={()=>{
          const id = prompt('invoiceId?');
          if (id) call('/invoices/'+id, 'GET');
        }} />
        <Button title="CANCELAR" onPress={()=>{
          const id = prompt('invoiceId?');
          if (id) call('/invoices/'+id+'/cancel', 'POST');
        }} />
        <Text style={{marginTop:12}} selectable>{log}</Text>
      </ScrollView>
    </SafeAreaView>
  );
}
