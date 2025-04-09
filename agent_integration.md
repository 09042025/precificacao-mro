
# Integração com Agente IA Abecom

Este app foi projetado para usar seu agente personalizado da OpenAI:

🔗 [Pricing Analyst Specialist MRO](https://chatgpt.com/g/g-67f6aa2ac35881918c19a3753fa7bd0c-pricing-analys-specialit-mro/c/67f6ba8e-c08c-8010-a1af-105bd2b24c58)

## Como integrar

No momento, a OpenAI **não permite uso direto de agentes personalizados via API pública**. Assim que essa função for liberada, atualize o modelo assim:

```python
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "Você é um especialista da Abecom."},
        {"role": "user", "content": "<descrição do produto>"}
    ]
)
```

Para adaptar ao seu agente específico, será necessário usar o identificador do agente assim que for disponibilizado via API.

## Recomendação

Utilize este app com os prompts modelados como se fossem enviados ao seu agente. O agente pode ser usado na fase de testes, coleta de exemplos e ajustes de prompt para melhorar a automação futura.
