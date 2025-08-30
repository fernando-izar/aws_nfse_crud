# NFS-e AWS Starter (Python CDK + Lambdas em Python)

Infra AWS (CDK v2 **Python**) + Lambdas (Python 3.12) + Admin Web + Mobile (Expo).

## Estrutura
- `infra/` — CDK Python: S3+CloudFront (admin), API Gateway REST, Lambdas, Cognito (User Pool), DynamoDB, S3 docs
- `infra/lambdas/*` — handlers Python
- `web/admin/` — HTML estático (S3)
- `web/admin-app/` — App React (Vite) p/ dev local
- `mobile/expo-app/` — App Expo (RN)
- `diagrams/` — Mermaid (.mmd + .html)

## Pré-requisitos
- Python 3.10+
- Node.js 18+ (para web/mobile)
- AWS CLI configurado (`aws configure`)
- CDK v2 (`npm i -g aws-cdk`)

## Deploy da Infra (Python)
```bash
cd infra
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
cdk bootstrap
cdk deploy
```
**Outputs**: `ApiUrl`, `UserPoolId`, `UserPoolClientId`, `AdminBucketName`, `AdminDistributionDomain`, `DocsBucketName`

## Teste rápido (ping público)
```bash
curl $(cdk output NfseStack.ApiUrl)public/ping
```

## Rotas protegidas (JWT - Cognito)
- Crie usuário no **User Pool** (console AWS) e obtenha `id_token` (Hosted UI).
- Exemplos:
```bash
curl -X POST -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json"     -d '{"companyCnpj":"00000000000000","total": 100}'     $(cdk output NfseStack.ApiUrl)invoices

curl -H "Authorization: Bearer <JWT>" $(cdk output NfseStack.ApiUrl)invoices/<invoiceId>

curl -X POST -H "Authorization: Bearer <JWT>" $(cdk output NfseStack.ApiUrl)invoices/<invoiceId>/cancel
```

## Admin Web (local, Vite)
```bash
cd ../web/admin-app
yarn
yarn dev
```

## Publicar Admin estático (S3+CloudFront)
```bash
aws s3 sync ../web/admin s3://$(cdk output NfseStack.AdminBucketName) --delete
# acesse: https://$(cdk output NfseStack.AdminDistributionDomain)/
```

## Mobile (Expo)
```bash
cd ../../mobile/expo-app
npm i
npx expo start
```

## Limpeza
```bash
cd ../../infra
cdk destroy --force
```

> Observação: Lambdas usam boto3 do runtime. Sem dependências externas.
